from odoo import models, fields, api


class JobPosition(models.Model):
    """
    Describe job position in configuration.
    """
    _name = "config.job.position"
    _description = "Job Position"
    _order = "sequence,id"
    _rec_name = "job_position"

    sequence = fields.Integer(string="No", index=True)
    job_position = fields.Char("Job Position", required=True)
    description = fields.Char("Description", required=True)

    _sql_constraints = [
            ('job_position_uniq', 'unique (job_position)', "Job position name already exists!"),
            ('sequence_uniq', 'unique (sequence)', "No already exists!")
        ]

    @api.model
    def create(self, vals):
        if 'sequence' in vals:
            ls_data = self.env['config.job.position'].search([])
            if ls_data:
                sequence_max = max(record.sequence for record in ls_data)
                vals['sequence'] = sequence_max + 1
        return super(JobPosition, self).create(vals)
           