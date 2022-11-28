from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CategorySupportServices(models.Model):
    _name = "category.support.service"

    name = fields.Char('Category', readonly=False, required=True)
    type_category = fields.Char('Type', required=True)

    @api.constrains('name', 'type_category')
    def check_duplica_name(self):
        for record in self:
            name_dupli = self.env['category.support.service'].search([('type_category', '=', record.type_category), ('id', '!=', record.id)])
            if len(name_dupli) > 0:
               raise UserError('Type Category already exists!')

    def unlink(self):
        for record in self:
            if record.type_category in ['team_building', 'salary_advance', 'it_helpdesk', 'open_projects', 'other']:
               raise UserError(_('Do not delete records whose type_category is %(type_category)s.', type_category=record.type_category))
        return super().unlink()

class PaymentSupportService(models.Model):
    _name = "payment.support.service"

    name = fields.Char('Payment')
    type_payment = fields.Char('Type')

class StatusSupportService(models.Model):
    _name = "status.support.service"

    name = fields.Char('Status')
    type_status = fields.Char('Type')


class PayrollSupportService(models.Model):
    _name = "payroll.support.service"

    name = fields.Char('Name')
    amount = fields.Float('Amount (VND)')
    support_service_id = fields.Many2one('support.services', string='Support Service')


    @api.constrains('amount')
    def check_amount_validation(self):
        for record in self:
            if record.amount <= 0:
                raise UserError('Amount cannot be less than or equal to 0')
            else:
                payroll_services = self.env['payroll.support.service'].search([
                    ('support_service_id', '=', record.support_service_id.id),
                    ('id', '!=', record.id)
                    ])
                
                total_amount = sum([payroll.amount for payroll in payroll_services])
                if record.amount + total_amount > record.support_service_id.amount:
                   raise UserError(_('The total amount cannot be greater than the advance (%(advance)s).', advance=record.support_service_id.amount))
              