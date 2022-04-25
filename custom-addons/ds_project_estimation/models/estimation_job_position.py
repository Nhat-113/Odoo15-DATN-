from odoo import models, fields, api


class JobPosition(models.Model):
    """
    Describe job position in configuration.
    """
    _name = "config.job_position"
    _description = "Job Position"
    _order = "sequence,id"
    _rec_name = "job_position"

    sequence = fields.Integer()
    job_position = fields.Char("Job Position", required=True)
    description = fields.Char("Description", required=True)
    effort = fields.Float(string="Effort", default=0.0)
    percent = fields.Char(string="Percentage", default="0.0")
    