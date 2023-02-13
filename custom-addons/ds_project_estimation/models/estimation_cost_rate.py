from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
import math


class CostRate(models.Model):
    """
    Describe cost rate.
    """
    _name = "cost.rate"
    _description = "CostRate"
    _order = "id"
    _rec_name = "description"


    description = fields.Char("Description", required=True)
    job_type = fields.Many2one('config.job.position', string='Type',required=True)
    
    
    @api.constrains('job_type')
    def validate_unique_job_position(self):
        costrate_datas = self.search([('id', '!=', self.id)])
        if self.job_type.id in costrate_datas.job_type.ids:
           raise UserError(_('The %s Cost Rate is already exist!', self.job_type.job_position))
    

class EstimationExchangeRate(models.Model):
    _name = "estimation.currency"
    _description = "Estimation Currency"

    name = fields.Char(string='Currency', size=3, required=True, help="Currency Code (ISO 4217)")
    full_name = fields.Char(string='Name')
    symbol = fields.Char(help="Currency sign, to be used when printing amounts.", required=True)
    rounding = fields.Float(string='Rounding Factor', digits=(12, 6), default=0.01, )
    decimal_places = fields.Integer(compute='_compute_decimal_places', store=True, )
    is_active = fields.Boolean(string="Active", default=False)

    def round(self, amount):
        """Return ``amount`` rounded  according to ``self``'s rounding rules.

           :param float amount: the amount to round
           :return: rounded float
        """
        self.ensure_one()
        return tools.float_round(amount, precision_rounding=self.rounding)

    @api.depends('rounding')
    def _compute_decimal_places(self):
        for currency in self:
            if 0 < currency.rounding < 1:
                currency.decimal_places = int(math.ceil(math.log10(1 / currency.rounding)))
            else:
                currency.decimal_places = 0
                

    @api.onchange('is_active')
    def _action_dynamic_column_costrate_currency(self):
        field_name = 'x_cost_' + self.name.casefold()
        field_des = 'Cost (' + self.name + ')'
        model = 'cost.rate'
        model_dynamic = self.env['ir.model'].search([('model', '=', model)])
        xml_inherit_id = self.env.ref('ds_project_estimation.view_tree_costrate')
        view_name = 'dynamic_view_costrate_customize_' + field_name
        
        if self.is_active == True:
            # Create new field (Column) when active new currency
            vals = {
                'name': field_name,
                'field_description': field_des,
                'model_id': model_dynamic.id,
                'ttype': 'float',
                'readonly': False,
                'store': True
            }
            self.env['ir.model.fields'].sudo().create(vals)
            
            # Create new view to show new field to cost rate treeview
            xml_arch = _('<?xml version="1.0" ?>'
                    '<data>'
                    '<field name="create_date" position="before">'
                    '<field name="%s"/>'
                    '</field>'
                    '</data>') % (field_name)
            vals_xml = {
                'name': view_name,
                'type': 'tree',
                'model': model,
                'mode': 'extension',
                'inherit_id': xml_inherit_id.id,
                'arch_base': xml_arch,
                'active': True
            }
            self.env['ir.ui.view'].sudo().create(vals_xml)
        else:
            estimations = self.env['estimation.work'].search([('currency_id', 'in', self.ids)], limit=1)
            if estimations:
                raise ValidationError('This currency is active, hence it cannot be turned off!')
            self.env['ir.ui.view'].search([('name', '=', view_name), ('model', '=', model)]).sudo().unlink()
            self.env['ir.model.fields'].search([('name', '=', field_name), ('model', '=', model)]).sudo().unlink()
            self.is_active = False