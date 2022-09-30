# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApplicantGetRefuseReason(models.TransientModel):
    _inherit = "applicant.get.refuse.reason"
    _description = 'Get Refuse Reason'

    send_mail = fields.Boolean("Send Email", compute='_compute_send_mail', store=True, readonly=False)

    @api.depends('refuse_reason_id')
    def _compute_send_mail(self):
        for wizard in self:
            template = wizard.refuse_reason_id.template_id
            wizard.send_mail = False
            wizard.template_id = template