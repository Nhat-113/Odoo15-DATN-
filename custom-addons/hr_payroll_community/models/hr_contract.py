# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """
    _inherit = 'hr.contract'
    _description = 'Employee Contract'
    _order = 'date_start desc'

    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure')
    schedule_pay = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi-annually', 'Semi-annually'),
        ('annually', 'Annually'),
        ('weekly', 'Weekly'),
        ('bi-weekly', 'Bi-weekly'),
        ('bi-monthly', 'Bi-monthly'),
    ], string='Scheduled Pay', index=True, default='monthly',
        help="Defines the frequency of the wage payment.")
    resource_calendar_id = fields.Many2one(required=True, help="Employee's working schedule.")
    hra = fields.Monetary(string='HRA', tracking=True, help="House rent allowance.")
    travel_allowance = fields.Monetary(string="Travel Allowance", help="Travel allowance")
    da = fields.Monetary(string="DA", help="Dearness allowance")
    meal_allowance = fields.Monetary(string="Meal Allowance", help="Meal allowance")
    medical_allowance = fields.Monetary(string="Medical Allowance", help="Medical allowance")
    union_fee = fields.Monetary(string="Union Fee", help="Union fee")
    number_of_dependents = fields.Integer(string="Number Of Dependents", help="Number of dependents", default=0)
    other_allowance = fields.Monetary(compute='_other_allowance_total', string="Other Allowance", readonly=True, help="Other allowances = Non-Taxable Allowances + Taxable Allowances")
    non_taxable_allowance = fields.Monetary(string="Non-Taxable Allowance", help="Non-Taxable Allowances")
    taxable_allowance = fields.Monetary(string="Taxable Allowance", help="Taxable Allowances")
    gasoline_subsidy = fields.Monetary(string="Gasoline Subsidy", help="Gasoline subsidy")
    percent_prob_contract = fields.Float('Probationary Contract', store=True, default=85)

    @api.depends('non_taxable_allowance', 'taxable_allowance')
    def _other_allowance_total(self):
        """ Calculates Other Allowances"""
        for contract in self:
            contract.other_allowance = contract.non_taxable_allowance + contract.taxable_allowance
    
    def get_all_structures(self):

        """
        @return: the structures linked to the given contracts, ordered by hierachy (parent=False first,
                 then first level children and so on) and without duplicata
        """
        structures = self.mapped('struct_id')
        if not structures:
            return []
        # YTI TODO return browse records
        return list(set(structures._get_parent_structure().ids))

    def get_attribute(self, code, attribute):

        return self.env['hr.contract.advantage.template'].search([('code', '=', code)], limit=1)[attribute]

    def set_attribute_value(self, code, active):
        for contract in self:

            if active:

                value = self.env['hr.contract.advantage.template'].search([('code', '=', code)], limit=1).default_value
                contract[code] = value
            else:

                contract[code] = 0.0

    @api.constrains('percent_prob_contract')
    def check_validate_percent_prob(self):
        for contract in self:
            if contract.percent_prob_contract <= 0 or contract.percent_prob_contract > 100:
               raise UserError('Percent must not be less than 0 and greater than 100')
                

class HrContractAdvandageTemplate(models.Model):
    _name = 'hr.contract.advantage.template'
    _description = "Employee's Advantage on Contract"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    lower_bound = fields.Float('Lower Bound', help="Lower bound authorized by the employer for this advantage")
    upper_bound = fields.Float('Upper Bound', help="Upper bound authorized by the employer for this advantage")
    default_value = fields.Float('Default value for this advantage')
