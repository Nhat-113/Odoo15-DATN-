from odoo import models, fields, api


class JobPosition(models.Model):
    """
    Describe job position in configuration.
    """
    _name = "config.job.position"
    _description = "Job Position"
    _order = "sequence,id"
    _rec_name = "job_position"

    sequence = fields.Integer()
    job_position = fields.Char("Job Position", required=True)
    description = fields.Char("Description", required=True)
