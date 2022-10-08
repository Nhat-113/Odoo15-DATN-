# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import timedelta

class Department(models.Model):
    _inherit = "hr.department"

    department_history_id = fields.One2many('hr.department.history', 'department_id', string='Department history', readonly=False)

    @api.model
    def create(self, vals):
        department = super(Department, self.with_context(mail_create_nosubscribe=True)).create(vals)
        manager = self.env['hr.employee'].browse(vals.get("manager_id"))
        manager_id = vals.get("manager_id")
        action_date = fields.Datetime.now()
        if manager.user_id:
            department.message_subscribe(partner_ids=manager.user_id.partner_id.ids)
        self.env['hr.department.history'].create({
                'department_id': department.id or False,
                'date_start': action_date,
                'date_end': False,
                'manager_history_id': manager_id or False
                })
        return department

    def write(self, vals):
        if 'manager_id' in vals:
            manager_id = vals.get("manager_id")
            self._update_and_create_history(manager_id)
        return super(Department, self).write(vals)

    def _update_and_create_history(self, manager_id):
        for department in self:
            # Update history department manager
            action_date = fields.Datetime.now()
            last_record_id = self.env['hr.department.history'].search([('department_id', '=', department.id)], limit=1, order='id desc')

            if len(last_record_id):
                if last_record_id.date_start.day > action_date.day:
                    last_record_id.date_end = last_record_id.date_start
                else:
                    last_record_id.date_end = action_date
            else:
                self.env['hr.department.history'].create({
                'department_id': department.id or False,
                'date_start' : False,
                'date_end': action_date,
                'manager_history_id': department.manager_id.id or False
            })

            last_record_id = self.env['hr.department.history'].search([('department_id', '=', department.id)], limit=1, order='id desc')

            # Create new history department manager
            self.env['hr.department.history'].create({
                'department_id': department.id or False,
                'date_start': last_record_id.date_end + timedelta(days=1),
                'date_end': False,
                'manager_history_id': manager_id
            })
        return True
        

    def unlink(self):
        for record in self:
            record.department_history_id.unlink()

        return super(Department, self).unlink()