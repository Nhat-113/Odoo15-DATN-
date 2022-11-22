from odoo import fields, models

class CategorySupportServices(models.Model):
    _name = "category.support.service"

    name = fields.Char('Category')
    type_category = fields.Char('Type')


class PaymentSupportService(models.Model):
    _name = "payment.support.service"

    name = fields.Char('Payment')
    type_payment = fields.Char('Type')

class StatusSupportService(models.Model):
    _name = "status.support.service"

    name = fields.Char('Status')
    type_status = fields.Char('Type')