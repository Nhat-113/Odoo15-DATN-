from odoo import models, fields


class CategoryGeneralExpense(models.Model):
    _name = "expense.general.category"
    _description = "Categories General Expense"
    _rec_name = "name"
    _order = "id"
    
    name = fields.Char(string="Category", required=True)
    description = fields.Char(string="Description")