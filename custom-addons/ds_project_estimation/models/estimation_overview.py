from odoo import models, fields, api


class EstimationOverview(models.Model):
    _name = "estimation.overview"
    _description = "Overview of each estimation"

    connect_overview = fields.Many2one('estimation.work', string="Connect Overview")
    
    # Notebook and pages
    author = fields.Many2one('res.users', string="User Update", default=lambda self: self.env.user, readonly=True)
    revision = fields.Char("Revision", readonly=True, copy=False, index=False, default="/")
    description = fields.Text("Description", default="Nothing")

    @api.model
    def create(self, vals):
        if vals.get("revision", "/") == "/":
            vals["revision"] = self.env["ir.sequence"].next_by_code("estimation.overview") or "/"
        result = super(EstimationOverview, self).create(vals)
        return result