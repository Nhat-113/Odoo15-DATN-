from odoo import models, fields, api


class EstimationOverview(models.Model):
    _name = "estimation.overview"
    _description = "Overview of each estimation"
    _order= "revision desc"
    
    connect_overview = fields.Many2one('estimation.work', string="Connect Overview")
    
    # Notebook and pages
    author = fields.Many2one('res.users', string="User Update", default=lambda self: self.env.user, readonly=True)
    revision = fields.Float("Revision", readonly=True, copy=False, index=False, default=0, digits= (1,1))
    description = fields.Text("Description", default="Nothing", readonly=True)

    @api.model
    def create(self, vals):
        list_revision = self.env['estimation.overview'].search([])
        revision_value = 0
        for item in list_revision:
            if item.connect_overview.id == vals["connect_overview"]:
                if revision_value < item.revision:
                    revision_value = item.revision
        if vals.get("revision", 0) == 0:
            vals["revision"] = (revision_value + 0.1)
        return super(EstimationOverview, self).create(vals)