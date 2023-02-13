from odoo import models, fields, api, _


class EstimationSummaryTotalCost(models.Model):
    _name = "estimation.summary.totalcost"
    _description = "Summary of each estimation"
    _order = "sequence,id"

    estimation_id = fields.Many2one('estimation.work', string="Estimation")

    sequence = fields.Integer(string="No", index=True, help='Use to arrange calculation sequence', default=1)
    check_generate_project = fields.Boolean(string="Check Generate Project", default=False,)
    name = fields.Char(string="Components", default="Module")
    key_primary = fields.Char(string="Key unique module")

    total_effort = fields.Float(string="Total Effort (MD)", readonly=True, compute='_compute_effort', store=True)
    cost = fields.Float(string="Cost", store=True)
    
    summary_costrates = fields.One2many('estimation.summary.costrate', 'total_cost_id')
    
    
    def total_efforts_job_position(self, job_position):
        result_total_effort = 0
        for record in self.estimation_id.add_lines_module:
            if record.component == self.name:
                for activity in record.module_config_activity:
                    for breakdown in activity.add_lines_breakdown_activity: # compute effort for each job position
                        if breakdown.job_pos.job_position == job_position:
                            result_total_effort += breakdown.mandays
        return result_total_effort

    @api.depends('estimation_id.add_lines_module.total_manday', 'summary_costrates.yen_month')
    def _compute_effort(self):
        ls_keys = self.get_field_effort({})
        for key in ls_keys:
            final_effort = 0
            for record in self:  # compute total effort for each module
                # if record.name not in ['Total (MD)', 'Total (MM)']:
                result_total_efforts = EstimationSummaryTotalCost.total_efforts_job_position(record, ls_keys[key])
                record[key] = result_total_efforts
                final_effort += result_total_efforts

                # get total manday from module = total_effort field
                for module in record.estimation_id.add_lines_module:
                    if module.key_primary == record.key_primary:
                        record.total_effort = module.total_manday
        self._compute_total_cost(ls_keys) 
                            
    def get_field_effort(self, ls_keys):
        ls_fields = self.fields_get()
        for field in ls_fields:
            if ls_fields[field]['type'] == 'float' and field not in ['total_effort', 'cost']:
                ls_keys[field] = ls_fields[field]['string']
        return ls_keys
    
    
    def _compute_total_cost(self, ls_fields):
        for tt_cost in self:
            total_cost = 0
            for cr in tt_cost.summary_costrates:
                for field in ls_fields:
                    if ls_fields[field] == cr.job_position.job_position:
                        total_cost += cr.yen_month * tt_cost[field]
                        break
            
            tt_cost.cost = total_cost
            
    
    @api.constrains('summary_costrates')
    def check_modify_costrate(self):
        overview = self.env['estimation.overview']
        next_revision = self.estimation_id.add_lines_overview[0].revision + 0.1
        des = 'Modified Cost Rate component ' + self.name
        
        overview.create({
                'connect_overview': self.estimation_id.id,
                'revision': next_revision,
                'description': des
            })

    def get_summary_costrate(self):
        view_id = self.env.ref('ds_project_estimation.estimation_summary_totalcost_view_form').id,
        return {
            'name': _('Cost Rates'),
            'type': 'ir.actions.act_window',
            'res_model': 'estimation.summary.totalcost',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [[view_id, 'form']],
            'view_id': view_id,
            'target': 'new',
            'context': {'create': False},
            'flags':{'mode':'readonly'}
        }