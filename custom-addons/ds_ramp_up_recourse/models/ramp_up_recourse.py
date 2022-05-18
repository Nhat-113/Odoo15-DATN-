from odoo import models, fields

class RampUp(models.Model):
    _inherit = ['hr.employee']
    _description = ''

    planning_calendar_resources = fields.One2many(
        'planning.calendar.resource', 'project_id', string='Planning Calendar Resources', readonly=True, compute='_get_calendar_resources')
    
    total_effort_rate = fields.Float(string='Total Effort Rate (%)',compute='_get_effort_rate_total', store=True)
    
    def _get_calendar_resources(self):
        for employee in self:
            employee.planning_calendar_resources = self.env['planning.calendar.resource'].search([('employee_id','=',employee.id)])


    def _get_effort_rate_total(self):
        for employee in self:
            effort_rates = [x.effort_rate for x in employee.planning_calendar_resources]
            total = 0
            for effort_rate in effort_rates:
                total += effort_rate
            employee.total_effort_rate = total
        
