from odoo import models, fields, api


class MeetingRoom(models.Model):
    _name = "meeting.room"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Meeting room"


    name = fields.Char(string="Room name", required=True, tracking=True, size=50)
    description = fields.Text(string="Description", tracking =True)
    active = fields.Boolean(string="Active", default=True)
    
    _sql_constraints = [('name_uniq', 'unique (name)', 'This room name already exists.')]
   