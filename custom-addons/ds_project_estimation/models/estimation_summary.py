from odoo import models, fields, api


class EstimationSummaryTotalCost(models.Model):
    _name = "estimation.summary.totalcost"
    _description = "Summary of each estimation"
    _order = "sequence,id"

    estimation_id = fields.Many2one('estimation.work', string="Estimation")

    sequence = fields.Integer(string="No", index=True, readonly=True, help='Use to arrange calculation sequence',
                              default=1)
    check_activate = fields.Boolean(string='Activate', default=False)
    check_generate_project = fields.Boolean(string="Check Generate Project", default=False,)
    name = fields.Char(string="Components", default="Module")
    design_effort = fields.Float(string="Designer",  compute='_compute_effort', store=True)
    dev_effort = fields.Float(string="Developer", store=True)
    tester_effort = fields.Float(string="Tester", store=True)
    comtor_effort = fields.Float(string="Comtor", store=True)
    brse_effort = fields.Float(string="Brse", store=True)
    pm_effort = fields.Float(string="PM", store=True)

    total_effort = fields.Float(string="Total Effort (MD)", readonly=True, compute='_compute_total_effort', store=True)
    cost = fields.Float(string="Cost", readonly=True, compute='_compute_cost', store=True)

    @api.depends('estimation_id.add_lines_summary_costrate.yen_month', 'estimation_id.add_lines_summary_costrate.role', 'total_effort')
    def _compute_cost(self):
        for record in self:
            component = record.name
            module_active = record.estimation_id.module_activate
            cost_rate_old = record.estimation_id.add_lines_summary_costrate
            if component != module_active:
                cost_rate_old = self.env['estimation.summary.costrate'].search([('name', '=', component)])
                for item in cost_rate_old:
                    if item.connect_summary_costrate:
                        cost_rate = self.env['cost.rate'].search([('id', '=', item.role.id)])

                        if record.estimation_id.currency_id.id:
                            currency_id = record.estimation_id.currency_id.id

                        elif record.estimation_id.currency_id.id == False:
                            currency_id = record.estimation_id.currency_id.id

                        elif record.estimation_id.currency_id.id.origin:
                            currency_id = record.estimation_id.currency_id.id

                        else:
                            currency_id = record.estimation_id.currency_id.id
                            if currency_id == False:
                                currency_id = 1

                        if currency_id == 1:
                            item.yen_month = cost_rate.cost_usd
                            item.yen_day = cost_rate.cost_usd / 20
                        elif currency_id == 22:
                            item.yen_month = cost_rate.cost_vnd
                            item.yen_day = cost_rate.cost_vnd / 20
                        else:
                            item.yen_month = cost_rate.cost_yen
                            item.yen_day = cost_rate.cost_yen / 20

            if not len(cost_rate_old):
                cost_rate_old = record.estimation_id.add_lines_summary_costrate

            cost = 0
            for item_cost_rate in cost_rate_old:
                if (item_cost_rate.name == component)and(item_cost_rate.connect_summary_costrate):
                    types = item_cost_rate.types
                    if types == 'Developer':
                        cost += record.dev_effort * item_cost_rate.yen_month
                    elif types == 'Designer':
                        cost += record.design_effort * item_cost_rate.yen_month
                    elif types == 'Tester':
                        cost += record.tester_effort * item_cost_rate.yen_month
                    elif types == 'Comtor':
                        cost += record.comtor_effort * item_cost_rate.yen_month
                    elif types == 'Brse':
                        cost += record.brse_effort * item_cost_rate.yen_month
                    elif types == 'Project manager':
                        cost += record.pm_effort * item_cost_rate.yen_month
                    else:
                        continue
            record.cost = cost

    @api.depends('design_effort', 'dev_effort', 'tester_effort', 'comtor_effort', 'brse_effort', 'pm_effort')
    def _compute_total_effort(self):
        for record in self:
            record.total_effort = record.design_effort + record.dev_effort + record.tester_effort + record.comtor_effort + record. \
                pm_effort + record.brse_effort

    def total_efforts_job_position(self, job_position):
        result_total_effort = 0
        for record in self.estimation_id.add_lines_module:
            if record.component == self.name:
                for activity in record.module_config_activity:
                    for breakdown in activity.add_lines_breakdown_activity: # compute effort for each job position
                        if breakdown.job_pos.job_position == job_position:
                            result_total_effort += breakdown.mandays
        return result_total_effort

    @api.depends('estimation_id.add_lines_module.total_manday')
    def _compute_effort(self):
        ls_key = {'dev_effort': 'Developer', 'design_effort': 'Designer', 'tester_effort': 'Tester',
                  'comtor_effort': 'Comtor', 'pm_effort': 'Project manager', 'brse_effort': 'Brse'}
        for key in ls_key:
            final_effort = 0
            for record in self:  # compute total effort for each module
                if record.name not in ['Total (MD)', 'Total (MM)']:
                    result_total_efforts = EstimationSummaryTotalCost.total_efforts_job_position(record, ls_key[key])
                    record[key] = result_total_efforts
                    final_effort += result_total_efforts

                    # get total manday from module = total_effort field
                    for module in record.estimation_id.add_lines_module:
                        if module.component == record.name:
                            record.total_effort = module.total_manday


class EstimationSummaryCostRate(models.Model):
    _name = "estimation.summary.costrate"
    _description = "Summary of cost rate in each estimation"
    _order = "sequence"

    connect_summary_costrate = fields.Many2one('estimation.work', string="Connect Summary Cost Rate", store=True)
    name = fields.Char(string="Components", store=True)

    sequence = fields.Integer(string="No", store=True)
    types = fields.Char(string="Type", store=True)
    role = fields.Many2one('cost.rate', string='Role', store=True)
    yen_month = fields.Float(string="Unit (Currency/Month)", store=True, default=0.00, compute='_compute_yen_month', readonly=True)
    yen_day = fields.Float(string="Unit (Currency/Day)", store=True, default=0.00, readonly=True)

    @api.depends('role', 'connect_summary_costrate.currency_id', 'role.cost_usd', 'role.cost_yen', 'role.cost_vnd')
    def _compute_yen_month(self):
        for item in self:
            cost_rate = self.env['cost.rate'].search([('id', '=', item.role.id)])

            if item.connect_summary_costrate.id:
                currency_id = item.connect_summary_costrate.currency_id.id

            elif item.connect_summary_costrate.id == False:
                currency_id = item.connect_summary_costrate.currency_id.id

            elif item.connect_summary_costrate.id.origin:
                currency_id = item.connect_summary_costrate.currency_id.id

            else:
                currency_id = item.connect_summary_costrate.currency_id.id
                if currency_id == False:
                    currency_id = 1

            if currency_id == 1:
                item.yen_month = cost_rate.cost_usd
                item.yen_day = cost_rate.cost_usd / 20
            elif currency_id == 22:
                item.yen_month = cost_rate.cost_vnd
                item.yen_day = cost_rate.cost_vnd / 20
            else:
                item.yen_month = cost_rate.cost_yen
                item.yen_day = cost_rate.cost_yen / 20
