from odoo import models, fields, api


class EstimationOverview(models.Model):
    _name = "estimation.overview"
    _description = "Overview of each estimation"

    connect_overview = fields.Many2one('estimation.work', string="Connect Overview")
    
    # Notebook and pages
    author = fields.Many2one('res.users', string="User Update", default=lambda self: self.env.user, readonly=True)
    revision = fields.Float("Revision", readonly=True, copy=False, index=False, default=0, digits= (1,1))
    description = fields.Text("Description", default="Nothing")

    @api.model
    def create(self, vals):
        listRevision = self.env['estimation.overview'].search([])
        revisionValue = 0
        for item in listRevision:
            if item.connect_overview.id == vals["connect_overview"]:
                if revisionValue < item.revision:
                    revisionValue = item.revision
        if vals.get("revision", 0) == 0:
            vals["revision"] = (revisionValue + 0.1)
        return super(EstimationOverview, self).create(vals)