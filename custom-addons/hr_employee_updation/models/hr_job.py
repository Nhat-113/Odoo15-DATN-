from odoo import models, fields

class HrJobModel(models.Model):
    _inherit = ["hr.job"]

    name = fields.Char(string='Job Position', required=True, index=True, translate=True)
    
    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Job position has already been taken'),
        (
            'name_len_check',
            'CHECK (length(name) <= 64)',
            ('Job position field should be less than 65 characters')
        ),
    ]
