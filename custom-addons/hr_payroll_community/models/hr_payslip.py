# -*- coding:utf-8 -*-

import babel
from collections import defaultdict
from datetime import date, datetime, time
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from pytz import timezone
from pytz import utc
import pandas as pd

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_utils

# This will generate 16th of days
ROUNDING_FACTOR = 16


class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _description = 'Pay Slip'

    struct_id = fields.Many2one('hr.payroll.structure', string='Structure',
                                readonly=True, states={'draft': [('readonly', False)]}, required=True,
                                help='Defines the rules that have to be applied to this payslip, accordingly '
                                     'to the contract chosen. If you let empty the field contract, this field isn\'t '
                                     'mandatory anymore and thus the rules applied will be all the rules set on the '
                                     'structure of all contracts of the employee valid for the chosen period')
    name = fields.Char(string='Payslip Name', readonly=True,
                       states={'draft': [('readonly', False)]})
    number = fields.Char(string='Reference', readonly=True, copy=False, help="References",
                         states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True, help="Employee",
                                  states={'draft': [('readonly', False)]})
    date_from = fields.Date(string='Date From', readonly=True, required=True, help="Start date",
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
                            states={'draft': [('readonly', False)]})
    date_to = fields.Date(string='Date To', readonly=True, required=True, help="End date",
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
                          states={'draft': [('readonly', False)]})
    # this is chaos: 4 states are defined, 3 are used ('verify' isn't) and 5 exist ('confirm' seems to have existed)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")
    line_ids = fields.One2many('hr.payslip.line', 'slip_id', string='Payslip Lines', readonly=True,
                               states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', readonly=True, copy=False, help="Company",
                                 default=lambda self: self.env['res.company']._company_default_get(),
                                 states={'draft': [('readonly', False)]})
    worked_days_line_ids = fields.One2many('hr.payslip.worked_days', 'payslip_id',
                                           string='Payslip Worked Days', copy=True, readonly=True,
                                           help="Payslip worked days",
                                           states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    input_line_ids = fields.One2many('hr.payslip.input', 'payslip_id', string='Payslip Inputs',
                                     readonly=True, states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    paid = fields.Boolean(string='Made Payment Order ? ', readonly=True, copy=False,
                          states={'draft': [('readonly', False)]})
    note = fields.Text(string='Internal Note', readonly=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string='Contract', readonly=True, help="Contract",
                                  states={'draft': [('readonly', False)]})
    details_by_salary_rule_category = fields.One2many('hr.payslip.line',
                                                      compute='_compute_details_by_salary_rule_category',
                                                      string='Details by Salary Rule Category', help="Details from the salary rule category")
    credit_note = fields.Boolean(string='Credit Note', readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 help="Indicates this payslip has a refund of another")
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batches', readonly=True,
                                     copy=False, states={'draft': [('readonly', False)]})
    payslip_count = fields.Integer(compute='_compute_payslip_count', string="Payslip Computation Details")


    def _compute_details_by_salary_rule_category(self):
        for payslip in self:
            payslip.details_by_salary_rule_category = payslip.mapped('line_ids').filtered(lambda line: line.category_id)

    def _compute_payslip_count(self):
        for payslip in self:
            payslip.payslip_count = len(payslip.line_ids)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):

        if any(self.filtered(lambda payslip: payslip.date_from > payslip.date_to)):
            raise ValidationError(_("Payslip 'Date From' must be earlier 'Date To'."))

        # if self.contract_id.date_end:
        #     if self.contract_id.date_start > self.date_to or self.contract_id.date_end < self.date_from:
        #         raise ValidationError(_('The following employees have a contract outside of the payslip period : %(name)s',
        #         name=self.employee_id.name))

    @api.constrains('struct_id')
    def _check_struct_id(self):
        if not self.struct_id:
            raise ValidationError(_("Field Structure cannot be left blank"))

    @api.constrains('name')
    def _check_payslips(self):
        payslip_names = [payslip.name for payslip in self.employee_id.slip_ids][:-1]

        if any(self.filtered(lambda payslip: payslip.name in payslip_names)):
            raise ValidationError(_("Do not create multiple payslips for an employee in the same month"))

    @api.constrains('contract_id')
    def _check_contract_id(self):

        if len(self.contract_id) == 0:          
            raise ValidationError(_('The following employees have a contract outside of the payslip period : %(name)s',name=self.employee_id.name))

    def action_payslip_draft(self):

        return self.write({'state': 'draft'})

    def action_payslip_done(self):

        self.compute_sheet()
        return self.write({'state': 'done'})

    def action_payslip_cancel(self):

        # if self.filtered(lambda slip: slip.state == 'done'):
        #     raise UserError(_("Cannot cancel a payslip that is done."))
        return self.write({'state': 'cancel'})

    def refund_sheet(self):
        for payslip in self:

            copied_payslip = payslip.copy({'credit_note': True, 'name': _('Refund: ') + payslip.name})
            copied_payslip.compute_sheet()
            copied_payslip.action_payslip_draft()
        formview_ref = self.env.ref('hr_payroll_community.view_hr_payslip_form', False)
        treeview_ref = self.env.ref('hr_payroll_community.view_hr_payslip_tree', False)
        return {
            'name': ("Refund Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % copied_payslip.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            'context': {}
        }

    def check_done(self):

        return True

    def unlink(self):

        if any(self.filtered(lambda payslip: payslip.state not in ('draft', 'cancel'))):
            raise UserError(_('You cannot delete a payslip which is not draft or cancelled!'))
        return super(HrPayslip, self).unlink()

    # TODO move this function into hr_contract module, on hr.employee object
    @api.model
    def get_contract(self, employee, date_from, date_to):

        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final_open = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        clause_final_close = [('employee_id', '=', employee.id), ('state', '=', 'close'), '|',
                        '|'] + clause_1 + clause_2 + clause_3

        contract_open = self.env['hr.contract'].search(clause_final_open)
        contract_close = self.env['hr.contract'].search(clause_final_close)
        if contract_open:
            if contract_open.date_start <= date_to:
                return contract_open.ids
        elif len(contract_close) == 1:
            if contract_close.date_end >= date_from:
                return contract_close.ids
        elif len(contract_close) >= 2:
            if contract_close[0].date_end >= date_from:
                return contract_close[0].ids

        return []   

    def compute_sheet(self):
        
        for payslip in self:
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            # delete old payslip lines
            payslip.line_ids.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or \
                        self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
            lines = [(0, 0, line) for line in self._get_payslip_lines(contract_ids, payslip.id)]
            payslip.write({'line_ids': lines, 'number': number})
            
        return self.write({'state': 'verify'})
       
    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):

        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), time.max)

            # compute leave days
            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to,
                                                                   calendar=contract.resource_calendar_id)
            
            NVKL = 0
            for day, hours, leave in day_leave_intervals:
                holiday = leave.holiday_id
                current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                    'name': holiday.holiday_status_id.name or _('Global Leaves'),
                    'sequence': 5,
                    'code': holiday.holiday_status_id.code or 'GLOBAL',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id,
                })
                current_leave_struct['number_of_hours'] += hours
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if work_hours:
                    current_leave_struct['number_of_days'] += hours / work_hours
                    if holiday.holiday_status_id.code == 'NVKL':
                        NVKL += hours / work_hours

            # compute worked days
            work_data = contract.employee_id.get_work_days_data(day_from, day_to,
                                                                calendar=contract.resource_calendar_id)
            attendances = {
                'name': _("Ngày làm việc bình thường được trả 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'],
                # 'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }


            #tính ngày nằm ngoài hợp đồng
            if contract.date_end and contract.date_start <= self.date_from and contract.date_end < self.date_to:
                if contract.date_end.strftime("%A") == "Sunday" or contract.date_end.strftime("%A") == "Saturday":
                    unpaid_working_day = len(pd.bdate_range(contract.date_end, self.date_to))
                else:
                    unpaid_working_day = len(pd.bdate_range(contract.date_end, self.date_to)) - 1
            elif contract.date_end and contract.date_start > self.date_from and contract.date_end < self.date_to:
                unpaid_working_day = len(pd.bdate_range(contract.date_end, self.date_to)) + len(pd.bdate_range(self.date_from, contract.date_start)) - 2
            elif contract.date_start > self.date_from:
                if contract.date_start.strftime("%A") == "Sunday" or contract.date_start.strftime("%A") == "Saturday":
                    unpaid_working_day = len(pd.bdate_range(self.date_from, contract.date_start))
                else:
                    unpaid_working_day = len(pd.bdate_range(self.date_from, contract.date_start)) - 1
            else:
                unpaid_working_day = 0

            unpaid = {
                'name': _("Ngày nằm ngoài hợp đồng"),
                'sequence': 5,
                'code': 'NNKL',
                'number_of_days': unpaid_working_day,
                # 'number_of_hours': 0,
                'contract_id': contract.id,
            }

            # tính Phí công đoàn
            list_contract = contract.employee_id.contract_ids
            contract_firstly = list_contract[0]
            contract_final = list_contract[0]
            union_fee = contract.union_fee
            if len(list_contract) > 1:
                for i in range(1, len(list_contract)):
                    if list_contract[i].date_start < contract_firstly.date_start:
                        contract_firstly = list_contract[i]

                    if list_contract[i].date_end and contract_final.date_end:
                        if list_contract[i].date_end > contract_final.date_end:
                            contract_final = list_contract[i]
                    elif list_contract[i].date_end == False:
                        contract_final = list_contract[i]
            if contract_firstly == contract:
                    if contract.date_start >= self.date_from and contract.date_start <= self.date_to:
                        if len(pd.bdate_range(contract.date_start, self.date_to)) <= 14:
                            union_fee = 0
                    elif contract.date_end and contract.date_end >= self.date_from and contract.date_end <= self.date_to:
                        if len(pd.bdate_range(self.date_from, contract.date_end)) <= 14 and len(list_contract) == 1:
                            union_fee = 0
            elif contract_final == contract:
                if contract.date_end:
                    if contract.date_end >= self.date_from and contract.date_end <= self.date_to:  
                        if len(pd.bdate_range(self.date_from, contract.date_end)) <= 14:    
                            union_fee = 0

            if NVKL >= 14:
                union_fee = 0

            union = {
                'name': _("Phí công đoàn"),
                'sequence': 55,
                'code': 'PCD',
                'number_of_days': union_fee,
                'contract_id': contract.id,
            }

            #tính thu nhập OT
            time_ots = self.env['account.analytic.line'].search([
                            ('payment_month', '=', str(self.date_from.month)), ('get_year_tb', '=', str(self.date_from.year)), 
                            ('type_ot', '=', 'yes'), ('employee_id', '=', self.employee_id.id),
                            ('status_timesheet_overtime', '=', 'approved'), ('pay_type', '!=', 'full_day_off')])
            
            total_ot_normal = 0
            total_ot_weekend = 0
            total_ot_holiday = 0
            total_ot_other = 0
            for time_ot in time_ots:
                if time_ot.pay_type == 'full_cash':
                    if time_ot.type_day_ot == 'normal_day':
                        total_ot_normal += time_ot.unit_amount
                    elif time_ot.type_day_ot == 'weekend':
                        total_ot_weekend += time_ot.unit_amount
                    elif time_ot.type_day_ot == 'other':
                        total_ot_other += time_ot.unit_amount
                    else:
                        total_ot_holiday += time_ot.unit_amount
                else:
                    if time_ot.type_day_ot == 'normal_day':
                        total_ot_normal += time_ot.unit_amount/2
                    elif time_ot.type_day_ot == 'weekend':
                        total_ot_weekend += time_ot.unit_amount/2
                    elif time_ot.type_day_ot == 'other':
                        total_ot_other += time_ot.unit_amount/2
                    else:
                        total_ot_holiday += time_ot.unit_amount/2
            
            time_ot_other = {
                'name': _("Thời Gian OT 100% Lương (Giờ)"),
                'sequence': 6,
                'code': 'TOT1',
                'number_of_days': total_ot_other,
                'contract_id': contract.id,
            }

            time_ot_normal = {
                'name': _("Thời Gian OT 150% Lương (Giờ)"),
                'sequence': 7,
                'code': 'TOT2',
                'number_of_days': total_ot_normal,
                'contract_id': contract.id,
            }

            time_ot_weekend = {
                'name': _("Thời Gian OT 200% Lương (Giờ)"),
                'sequence': 8,
                'code': 'TOT3',
                'number_of_days': total_ot_weekend,
                'contract_id': contract.id,
            }

            time_ot_holiday = {
                'name': _("Thời Gian OT 300% Lương (Giờ)"),
                'sequence': 9,
                'code': 'TOT4',
                'number_of_days': total_ot_holiday,
                'contract_id': contract.id, 
            }


            if union_fee > 0:
                res.append(union)
            res.append(attendances)
            if unpaid_working_day > 0:
                res.append(unpaid)
            if total_ot_other > 0:
                res.append(time_ot_other)
            if total_ot_normal > 0:    
                res.append(time_ot_normal)
            if total_ot_weekend > 0:
                res.append(time_ot_weekend)
            if total_ot_holiday > 0:
                res.append(time_ot_holiday)
            res.extend(leaves.values())
        return res

    @api.model
    def get_inputs(self, contracts, date_from, date_to):

        res = []

        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')

        for contract in contracts:
            for input in inputs:
                input_data = {
                    'name': input.name,
                    'code': input.code,
                    'contract_id': contract.id,
                }
                res += [input_data]
            
            percent_net = self.env['hr.percent.bhxh'].search([('type_percent', '=', 'bhxh_net')]).percent
            percent_gross = self.env['hr.percent.bhxh'].search([('type_percent', '=', 'bhxh_gross')]).percent
            percent_gross_sdld = self.env['hr.percent.bhxh'].search([('type_percent', '=', 'bhxh_gross_sdld')]).percent
            if contract.contract_document_type != 'probationary':
                if contract.struct_id.code == 'BASE1':
                    bhxh_percent = percent_net
                    bhxh_percent_sdld = 0
                elif contract.struct_id.code == 'BASE2':
                    bhxh_percent = percent_gross
                    bhxh_percent_sdld = percent_gross_sdld
                else:
                    bhxh_percent = 0
                    bhxh_percent_sdld = 0
            else:
                bhxh_percent = 0
                bhxh_percent_sdld = 0
            
            res.append({
                'name': 'Khoản bổ sung/Tạm ứng (VND)',
                'code': 'KBS',
                'contract_id': contract.id,
                'amount': contract.gasoline_subsidy,
            })
            if bhxh_percent > 0:
                res.append({
                    'name': 'BHXH (%) (Trích vào lương NLĐ)',
                    'code': 'PBH',
                    'contract_id': contract.id,
                    'amount': bhxh_percent
                })
            if bhxh_percent_sdld > 0:
                res.append({
                    'name': 'BHXH (%) (Trích vào chi phí DN)',
                    'code': 'BHC',
                    'contract_id': contract.id,
                    'amount': bhxh_percent_sdld
                })
        return res


    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):

        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and \
                                                          localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict, env):
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(amount) as sum
                    FROM hr_payslip as hp, hr_payslip_input as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
                    FROM hr_payslip as hp, hr_payslip_worked_days as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                            FROM hr_payslip as hp, hr_payslip_line as pl
                            WHERE hp.employee_id = %s AND hp.state = 'done'
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        # we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env['hr.payslip'].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict, self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)

        baselocaldict = {'categories': categories, 'rules': rules, 'payslip': payslips, 'worked_days': worked_days,
                         'inputs': inputs}
        # get the ids of the structures on the contracts and their parent id as well
        contracts = self.env['hr.contract'].browse(contract_ids)
        if len(contracts) == 1 and payslip.struct_id:
            structure_ids = list(set(payslip.struct_id._get_parent_structure().ids))
        else:
            structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in sorted_rules:
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                # check if the rule can be applied
                if rule._satisfy_condition(localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule._compute_rule(localdict)
                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in rule._recursive_search_of_rules()]

        return list(result_dict.values())

    # YTI TODO To rename. This method is not really an onchange, as it is not in any view
    # employee_id and contract_id could be browse records
    def onchange_employee_id(self, date_from, date_to, employee_id=False, contract_id=False):

        # defaults
        res = {
            'value': {
                'line_ids': [],
                # delete old input lines
                'input_line_ids': [(2, x,) for x in self.input_line_ids.ids],
                # delete old worked days lines
                'worked_days_line_ids': [(2, x,) for x in self.worked_days_line_ids.ids],
                # 'details_by_salary_head':[], TODO put me back
                'name': '',
                'contract_id': False,
                'struct_id': False,
            }
        }
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        employee = self.env['hr.employee'].browse(employee_id)
        locale = self.env.context.get('lang') or 'en_US'
        res['value'].update({
            'name': _('Salary Slip of %s for %s') % (
            employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))),
            'company_id': employee.company_id.id,
        })

        if not self.env.context.get('contract'):
            # fill with the first contract of the employee
            contract_ids = self.get_contract(employee, date_from, date_to)
        else:
            if contract_id:
                # set the list of contract for which the input have to be filled
                contract_ids = [contract_id]
            else:
                # if we don't give the contract, then the input to fill should be for all current contracts of the employee
                contract_ids = self.get_contract(employee, date_from, date_to)

        if not contract_ids:
            return res
        contract = self.env['hr.contract'].browse(contract_ids[0])
        res['value'].update({
            'contract_id': contract.id
        })
        struct = contract.struct_id
        if not struct:
            return res
        res['value'].update({
            'struct_id': struct.id,
        })
        # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        res['value'].update({
            'worked_days_line_ids': worked_days_line_ids,
            'input_line_ids': input_line_ids,
        })
        return res

    @api.onchange('employee_id')
    def onchange_employ(self):
        if self.employee_id:
            if not self.employee_id.contract_id :
                self.contract_id = False
                self.input_line_ids = False
                self.worked_days_line_ids = False
            else:
                contract_ids = self.env['hr.contract'].search(['&', ('employee_id', '=', self.employee_id.id), ('state', '!=', 'cancel')]).ids
                if contract_ids:
                    self.contract_id = self.env['hr.contract'].browse(contract_ids[0])
                    worked_days_line_ids = self.get_worked_day_lines(self.contract_id, self.date_from, self.date_to)
                    worked_days_lines = self.worked_days_line_ids.browse([])
                    for r in worked_days_line_ids:
                        worked_days_lines += worked_days_lines.new(r)
                    self.worked_days_line_ids = worked_days_lines
                else:
                    self.contract_id = False
                    self.input_line_ids = False
                    self.worked_days_line_ids = False
        return

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):

        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []

        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        locale = self.env.context.get('lang') or 'en_US'
        self.name = _('Salary Slip of %s for %s') % (
        employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
        self.company_id = employee.company_id

        if not self.env.context.get('contract') or not self.contract_id:
            contract_ids = self.get_contract(employee, date_from, date_to)
            if not contract_ids:
                self.contract_id = False
                self.worked_days_line_ids = False
                self.input_line_ids = False
                return 
            self.contract_id = self.env['hr.contract'].browse(contract_ids[0])

        if not self.contract_id.struct_id:
            return
        self.struct_id = self.contract_id.struct_id
        if self.contract_id:
            contract_ids = self.contract_id.ids
        # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines

        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        for r in input_line_ids:
            input_lines += input_lines.new(r)
        self.input_line_ids = input_lines
        return

    @api.onchange('contract_id')
    def onchange_contract(self):

        if not self.contract_id:
            self.struct_id = False
        self.with_context(contract=True).onchange_employee()
        return

    def get_salary_line_total(self, code):

        self.ensure_one()
        line = self.line_ids.filtered(lambda line: line.code == code)
        if line:
            return line[0].total
        else:
            return 0.0


class HrPayslipLine(models.Model):
    _name = 'hr.payslip.line'
    _inherit = 'hr.salary.rule'
    _description = 'Payslip Line'
    _order = 'contract_id, sequence'

    slip_id = fields.Many2one('hr.payslip', string='Pay Slip', required=True, ondelete='cascade', help="Payslip")
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Rule', required=True, help="salary rule")
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, help="Employee")
    # category_id = fields.Many2one(related='salary_rule_id.category_id', string='Category', required=True)
    contract_id = fields.Many2one('hr.contract', string='Contract', required=True, index=True, help="Contract")
    rate = fields.Float(string='Rate (%)', default=100.0)
    amount = fields.Float(string='Amount')
    quantity = fields.Float(default=1.0)
    total = fields.Float(compute='_compute_total', string='Total', help="Total", store=True)

    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):

        for line in self:
            line.total = float(line.quantity) * line.amount * line.rate / 100

    @api.model_create_multi
    def create(self, vals_list):

        for values in vals_list:
            if 'employee_id' not in values or 'contract_id' not in values:
                payslip = self.env['hr.payslip'].browse(values.get('slip_id'))
                values['employee_id'] = values.get('employee_id') or payslip.employee_id.id
                values['contract_id'] = values.get('contract_id') or payslip.contract_id and payslip.contract_id.id
                if not values['contract_id']:
                    raise UserError(_('You must set a contract to create a payslip line.'))
        return super(HrPayslipLine, self).create(vals_list)


class HrPayslipWorkedDays(models.Model):
    _name = 'hr.payslip.worked_days'
    _description = 'Payslip Worked Days'
    _order = 'payslip_id, sequence'

    name = fields.Char(string='Description', required=True)
    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', required=True, ondelete='cascade', index=True, help="Payslip")
    sequence = fields.Integer(required=True, index=True, default=10, help="Sequence")
    code = fields.Char(required=True, help="The code that can be used in the salary rules")
    number_of_days = fields.Float(string='Amount', help="Number of days worked")
    number_of_hours = fields.Float(string='Number of Hours', help="Number of hours worked")
    contract_id = fields.Many2one('hr.contract', string='Contract', required=True,
                                  help="The contract for which applied this input")


class HrPayslipInput(models.Model):
    _name = 'hr.payslip.input'
    _description = 'Payslip Input'
    _order = 'payslip_id, sequence'

    name = fields.Char(string='Description', required=True)
    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', required=True, ondelete='cascade', help="Payslip", index=True)
    sequence = fields.Integer(required=True, index=True, default=10, help="Sequence")
    code = fields.Char(required=True, help="The code that can be used in the salary rules")
    amount = fields.Float(help="It is used in computation. For e.g. A rule for sales having "
                               "1% commission of basic salary for per product can defined in expression "
                               "like result = inputs.SALEURO.amount * contract.wage*0.01.")
    contract_id = fields.Many2one('hr.contract', string='Contract', required=True,
                                  help="The contract for which applied this input")


class HrPayslipRun(models.Model):
    _name = 'hr.payslip.run'
    _description = 'Payslip Batches'

    name = fields.Char(required=True, readonly=True, states={'draft': [('readonly', False)]})
    slip_ids = fields.One2many('hr.payslip', 'payslip_run_id', string='Payslips', readonly=True,
                               states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('close', 'Close'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    date_start = fields.Date(string='Date From', required=True, readonly=True, help="start date",
                             states={'draft': [('readonly', False)]},
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_end = fields.Date(string='Date To', required=True, readonly=True, help="End date",
                           states={'draft': [('readonly', False)]},
                           default=lambda self: fields.Date.to_string(
                               (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    credit_note = fields.Boolean(string='Credit Note', readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 help="If its checked, indicates that all payslips generated from here are refund "
                                      "payslips.")

    def draft_payslip_run(self):
        return self.write({'state': 'draft'})

    def close_payslip_run(self):
        return self.write({'state': 'close'})


class ResourceMixin(models.AbstractModel):
    _inherit = "resource.mixin"

    def get_work_days_data(self, from_datetime, to_datetime, compute_leaves=True, calendar=None, domain=None):
        """
            By default the resource calendar is used, but it can be
            changed using the `calendar` argument.

            `domain` is used in order to recognise the leaves to take,
            None means default value ('time_type', '=', 'leave')

            Returns a dict {'days': n, 'hours': h} containing the
            quantity of working time expressed as days and as hours.
        """
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)

        # total hours per day: retrieve attendances with one extra day margin,
        # in order to compute the total hours on the first and last days
        from_full = from_datetime - timedelta(days=1)
        to_full = to_datetime + timedelta(days=1)
        intervals = calendar._attendance_intervals_batch(from_full, to_full, resource)
        day_total = defaultdict(float)
        for start, stop, meta in intervals[resource.id]:
            day_total[start.date()] += (stop - start).total_seconds() / 3600

        # actual hours per day
        if compute_leaves:
            intervals = calendar._work_intervals_batch(from_datetime, to_datetime, resource, domain)
        else:
            intervals = calendar._attendance_intervals_batch(from_datetime, to_datetime, resource)
        day_hours = defaultdict(float)
        for start, stop, meta in intervals[resource.id]:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600

        # compute number of days as quarters
        days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[day] / day_total[day]) / ROUNDING_FACTOR
            for day in day_hours
        )
        return {
            'days': days,
            'hours': sum(day_hours.values()),
        }
