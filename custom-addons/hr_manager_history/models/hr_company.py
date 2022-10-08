# -*- coding:utf-8 -*-

from odoo import fields, models, api
from datetime import timedelta
from odoo.exceptions import UserError


class Company(models.Model):
    _inherit = "res.company"

    company_history_id = fields.One2many('hr.company.history', 'company_id', string='Company History', readonly=False)

    @api.model
    def create(self, vals):
        ## Definition
        company = super(Company, self).create(vals)
        user_email = vals.get("user_email")
        action_date = fields.Datetime.now()
        try:
            employee = self.env['hr.employee'].search([('work_email','=',user_email)])
        except:
            raise UserError("User email does not exist!")

        self.env['hr.company.history'].create({
                'company_id': company.id or False,
                'date_start' : action_date,
                'date_end': False,
                'email_history_id': user_email,
                'representative': employee.id or False,
            })
        return company

    def write(self, vals):
        user_email = vals.get("user_email")
        if user_email:
            self._update_and_create_history(user_email)

        return super(Company, self).write(vals)

    def _update_and_create_history(self, user_email):
        for company in self:
            # Update history email manager
            last_record_id = self.env['hr.company.history'].search([('company_id','=', company.id)], limit=1, order='id desc')
            action_date = fields.Datetime.now()
            try:
                employee = self.env['hr.employee'].search([('work_email','=',user_email)])
                last_employee = self.env['hr.employee'].search([('work_email','=', company.user_email)])
            except:
                raise UserError("User email does not exist!")
            
            if len(last_record_id):
                if last_record_id.date_start.day > action_date.day:
                    last_record_id.date_end = last_record_id.date_start
                else:
                    last_record_id.date_end = action_date
            else:
                self.env['hr.company.history'].create({
                'company_id': company.id or False,
                'date_start' : False,
                'date_end': action_date,
                'email_history_id': company.user_email,
                'representative':  last_employee.id or False,
            })

            last_record_id = self.env['hr.company.history'].search([('company_id','=', company.id)], limit=1, order='id desc')

            # Create new history email manager
            self.env['hr.company.history'].create({
                'company_id': company.id or False,
                'date_start': last_record_id.date_end + timedelta(days=1),
                'date_end': False,
                'email_history_id': user_email,
                'representative': employee.id or False,
            })
        return True