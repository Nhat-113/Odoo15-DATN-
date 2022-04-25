from odoo import models, fields, api


class Description(models.Model):
    """
    Description
    """
    _name = "config.description"
    _description = "Description"
    _order = "sequence,id"
    _rec_name = "descript"
    
    sequence = fields.Integer(string="Sequence")
    descript = fields.Char(string="Description name")
