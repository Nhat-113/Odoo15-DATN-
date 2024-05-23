# -*- coding: utf-8 -*-

from datetime import date, datetime
from odoo import api, fields, models


class BoxManagement(models.Model):
    _name = "box.management"
    _description = "Box Management"
    _rec_name = "device_id"

    device_name = fields.Char(string="Device Name", required=True)
    device_id = fields.Char(string="Device ID", readonly=True)
    device_type = fields.Selection(
        string="Device Type",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        selection=[
            ("box_in", "In"),
            ("box_out", "Out"),
            ("box_io", "In/Out"),
        ]
    )
    
    employee_ids = fields.Many2many(
      comodel_name="hr.employee", 
      string="Employees Access",
      relation="device_employee_rel",
      column1="device_id", 
      column2="employee_id")

    note = fields.Text(string="Note")

    def write(self, vals):
        ## Validasi Karakter pada field 'name'
        if 'employee_ids' in vals:
            before_records = self.read(['employee_ids'])[0]['employee_ids']
            new_records = vals.get('employee_ids', before_records)[0]
            removed_elements = [element for element in before_records if element not in new_records[2]]
            add_elements = [element for element in new_records[2] if element not in before_records]
        
            if add_elements:
                check_exist_record = self.env['box.employee.rel'].sudo().search([('device_id', '=', self.id), ('employee_id', 'in', add_elements)])
                if check_exist_record:
                    check_exist_record.write({
                            'delete_at': None
                        })
                new_record = [{   
                    'device_id': self.id,
                    'employee_id': element,
                } for element in add_elements if element not in check_exist_record.employee_id.ids]
                if new_record:
                    self.env['box.employee.rel'].sudo().create(new_record)

            if removed_elements:
                self.env['box.employee.rel'].sudo().search([('device_id', '=', self.id), ('employee_id', 'in', removed_elements)]).write({
                    'delete_at': datetime.now()
                })
        
        return super(BoxManagement, self).write(vals=vals)
    
    def unlink(self):
        get_current_record = self.env['box.employee.rel'].sudo().search([("device_id", 'in' , self.ids)])
        
        if get_current_record: 
            get_current_record.sudo().unlink()
        
        return super(BoxManagement, self).unlink()