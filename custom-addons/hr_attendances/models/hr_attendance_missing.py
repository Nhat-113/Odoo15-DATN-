from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import pytz
import pandas as pd
import base64


class HrAttendanceMissing(models.Model):
    _name = 'hr.attendance.missing'
    _description = 'HR Attendance Missing'
    _order = 'employee_id, date, status_timeoff'
    _rec_name = 'employee_id'
    
    
    
    employee_id = fields.Many2one('hr.employee', string="Employee")
    company_id = fields.Many2one('res.company', related='employee_id.company_id', store=True, string="Company")
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', store=True, string="Department")
    date = fields.Date(string="Date")
    timeoff = fields.Many2one('hr.leave', string="Time Off", domain="[('employee_id', '=', employee_id)]")
    status_timeoff = fields.Selection(related='timeoff.state', store=True, string='Status')
    description = fields.Text(string="Note")
    is_holiday = fields.Boolean(string="Is Holiday", default=False)
    public_holiday = fields.Many2one('resource.calendar.leaves', string="Public Holiday")
    

    
    def action_approve_timeoff(self):
        self.timeoff.action_validate()
        
    def action_multiple_approve_timeoff(self):
        for record in self.filtered(lambda x: x.timeoff):
            if record.timeoff.state not in ['refuse', 'validate', 'validate1']:
                record.timeoff.action_validate()
            
    def action_refuse_timeoff(self):
        self.timeoff.action_refuse()
        
    def action_multiple_refuse_timeoff(self):
        for record in self.filtered(lambda x: x.timeoff):
            if record.timeoff.state not in ['refuse', 'validate', 'validate1']:
                record.timeoff.action_refuse()
            
    def action_enable_holiday(self):
        dates = [record.date for record in self]
        date_min = min(dates)
        date_max = max(dates)
        domain = [('date_start', '>=', date_min), 
                ('date_start', '<=', date_max),
                '|',
                ('date_end', '>=', date_min), 
                ('date_end', '<=', date_max),
                ('resource_id', '=', False),
                ('holiday_id', '=', False)]
        if date_min == date_max:
            domain = [('date_start', '<=', date_min), 
                      ('date_end', '>=', date_min),
                      ('resource_id', '=', False),
                      ('holiday_id', '=', False)]
            
        holidays = self.env['resource.calendar.leaves'].search(domain)
        for record in holidays:
            attendance_misings = self.filtered(lambda d: d.date >= record.date_start and d.date <= record.date_end)
            for am in attendance_misings:
                am.is_holiday = True
                am.public_holiday = record
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Public Holiday (Time Off) enabled successfully'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
        
        
    def action_disable_holiday(self):
        self.is_holiday = False
        self.public_holiday = False
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Public Holiday disabled successfully'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
        
        
    
    def action_open_timeoff(self):
        view_id = self.env.ref('hr_holidays.hr_leave_view_tree').id
        return {
            'name': _(self.employee_id.name + ' Time Off Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave',
            'views': [[view_id, 'list'], [False, 'form']],
            'target': 'current',
            # 'context': {'no_breadcrumbs': True, 'no_create': True},
            'search_view_id': [False],
            'domain': [('id', '=', self.timeoff.id)]
        }
        
        
    def cron_action_create_missing_attendance(self):
        today = date.today()
        if self.is_working_day(today):
            contracts = self.env['hr.contract'].search([('state', 'not in', ['cancel', 'draft']),
                                                        '|',
                                                            ('date_end', '>=', today),
                                                            ('date_end', '=', False)], order='id')
            attendances = self.env['hr.attendance'].search([('check_in', '>=', today.strftime('%Y-%m-%d 00:00:00')),
                                                            ('check_in', '<=', today.strftime('%Y-%m-%d 23:59:59'))])
            timeoffs = self.env['hr.leave'].search([('date_start', '<=',today),
                                                    ('date_end', '>=',today),
                                                    ('state', '!=', 'refuse')])
            employee_missing_attendances = [emp for emp in contracts.employee_id.ids if emp not in attendances.employee_id.ids]
            attendances_missing_exists = self.search([('employee_id', 'in', employee_missing_attendances),
                                                    ('date', '=', today)])
            employee_missing_attendance_finals = [emp for emp in employee_missing_attendances if emp not in attendances_missing_exists.employee_id.ids]
            for emp in employee_missing_attendance_finals:
                timeoffid = timeoffs.filtered(lambda t: t.employee_id.id == emp)
                self.create({
                    'employee_id': emp,
                    'date': today,
                    'timeoff': timeoffid.id
                })
            
        
    def is_working_day(self, date):
        return bool(len(pd.bdate_range(date, date)))
    
    
    
    def send_mail_attendance_missing(self):
        report = self.env.ref('hr_attendances.action_report_attendance_missing_xlsx')
        generated_report = report._render_xlsx(self.ids, [])
        data_record = base64.b64encode(generated_report[0])
        ir_values = {
            'name': 'Attendance_Missing_report.xlsx',
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/vnd.ms-excel',
            'res_model': 'hr.attendance.missing'
        }
        attachment = self.env['ir.attachment'].sudo().create(ir_values)
        
        try:
            email_template = self.env.ref('hr_attendances.email_template_attendance_missing')
        except ValueError:
            email_template = False
            
        try:
            compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        except ValueError:
            compose_form_id = False
            
        if email_template:
            email_template.attachment_ids = False
            email_template.attachment_ids = [(4, attachment.id)]
            
        # Send data to email template
        email_to = ','.join([emp.work_email for emp in self.employee_id])
        start = min([record.date for record in self])
        end = max([record.date for record in self])
        period = str(start.month) + '/' + str(start.year)
        if start.month != end.month:
            period += ' - ' + str(end.month) + '/' + str(end.year)
            
        unapproved = self.filtered(lambda x: x.status_timeoff not in ['refuse', 'validate', 'validate1', False] and bool(x.public_holiday) == False)
        attendance_missing = self.filtered(lambda d: bool(d.timeoff) == False and bool(d.public_holiday) == False)
        if not unapproved and not attendance_missing:
            raise UserError('No missing attendance data or unapproved time off!')
            
        ctx = {
            'default_model' :  'hr.attendance.missing',
            'default_res_ids' : self.ids,
            'default_use_template' : bool(email_template),
            'default_template_id' : email_template.id,
            'default_composition_mode' : 'comment',
            'mark_so_as_sent' : True,
            'custom_layout' : 'mail.mail_notification_light',
            'force_email' : True,
            'period': period,
            'email_to': email_to,
            'email_from': 'hr@d-soft.com.vn',
            'is_timeoff': bool(unapproved),
            'is_missing_attendance': bool(attendance_missing)
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx
        }
        
    def cron_action_missing_attendance_send_mail_daily_to_hr(self):
        datas = self.search([('date', '>=', date.today().replace(day=1)), 
                             ('date', '<=', date.today().replace(day=1) + relativedelta(months=1, days=-1))])
        if datas:
            try:
                email_template = self.env.ref('hr_attendances.email_template_attendance_missing_mail_to_hr')
            except ValueError:
                email_template = False
                
            if email_template:
                email_values = {
                    'email_to': 'hr@d-soft.com.vn'
                }
                email_template.send_mail(datas[0].id, force_send=True, 
                                         notif_layout='hr_attendances.custom_template_mail_notification_attendance', 
                                         email_values=email_values)