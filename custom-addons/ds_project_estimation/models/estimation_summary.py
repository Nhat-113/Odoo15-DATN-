from odoo import models, fields, api


class EstimationSummaryTotalCost(models.Model):
    _name = "estimation.summary.totalcost"
    _description = "Summary of each estimation"
    _order = "sequence,id"
    
    connect_summary = fields.Many2one('estimation.work', string="Connect Summary")

    estimation_id = fields.Many2one('estimation.work', string="Estimation")

    sequence = fields.Integer(string="No", index=True, readonly=True, help='Use to arrange calculation sequence', default=1)
    module = fields.Char(string="Components",)
    design_effort = fields.Float(string="Design", compute='_compute_effort')
    dev_effort = fields.Float(string="Developer", compute='_compute_effort')
    tester_effort = fields.Float(string="Tester", compute='_compute_effort')
    comtor_effort = fields.Float(string="Comtor", compute='_compute_effort')
    brse_effort = fields.Float(string="Brse", compute='_compute_effort')
    pm_effort = fields.Float(string="PM", compute='_compute_effort')
    
    total_effort = fields.Float(string="Total Effort (MD)", readonly=True, compute='_compute_total_effort')
    cost = fields.Float(string="Cost", readonly=True, compute='_compute_total_effort')

    @api.depends('estimation_id')
    def _compute_effort(self):
        estimation_id = self.connect_summary.id
        activities = self.env['module.effort.activity'].search([('estimation_id', '=', estimation_id)])
        design_total = 0.0
        dev_total = 0.0
        tester_total = 0.0
        comtor_total = 0.0
        pm_total = 0.0
        brse_total = 0.0

        for activity in activities:
            breakdown_activity = self.env['module.breakdown.activity'].search([('activity_id', '=', activity.activity_id.id)])
            for item in breakdown_activity:
                if item.job_pos.job_position == 'Designer':
                    design_total += item.mandays
                elif item.job_pos.job_position == 'Developer':
                    dev_total += item.mandays
                elif item.job_pos.job_position == 'Tester':
                    tester_total += item.mandays
                elif item.job_pos.job_position == 'Comtor':
                    comtor_total += item.mandays
                elif item.job_pos.job_position == 'Brse':
                    brse_total += item.mandays
                elif item.job_pos.job_position == 'Project manager':
                    pm_total += item.mandays
                else:
                    continue

        self.design_effort = design_total
        self.dev_effort = dev_total
        self.tester_effort = tester_total
        self.comtor_effort = comtor_total
        self.pm_effort = pm_total
        self.brse_effort = brse_total

    def _compute_total_effort(self):
        self.total_effort = self.design_effort + self.dev_effort + self.tester_effort + self.comtor_effort + \
                            self.pm_effort + self.brse_effort
        connect_summary = self.connect_summary.ids

        cost_designer = self.design_effort * self.env['estimation.summary.costrate'].search(
            [('types', '=', 'Designer'), ('connect_summary_costrate', 'in', connect_summary)]).yen_month

        cost_dev = self.dev_effort * self.env['estimation.summary.costrate'].search(
            [('types', '=', 'Developer'), ('connect_summary_costrate', 'in', connect_summary)]).yen_month

        cost_tester = self.tester_effort * self.env['estimation.summary.costrate'].search(
            [('types', '=', 'Tester'), ('connect_summary_costrate', 'in', connect_summary)]).yen_month

        cost_comtor = self.comtor_effort * self.env['estimation.summary.costrate'].search(
            [('types', '=', 'Comtor'), ('connect_summary_costrate', 'in', connect_summary)]).yen_month

        cost_brse = self.brse_effort * self.env['estimation.summary.costrate'].search(
            [('types', '=', 'Brse'), ('connect_summary_costrate', 'in', connect_summary)]).yen_month

        cost_pm = self.pm_effort * self.env['estimation.summary.costrate'].search(
            [('types', '=', 'Project manager'), ('connect_summary_costrate', 'in', connect_summary)]).yen_month

        self.cost = cost_designer + cost_dev + cost_tester + cost_comtor + cost_brse + cost_pm


class EstimationSummaryCostRate(models.Model):
    _name = "estimation.summary.costrate"
    _description = "Summary of cost rate in each estimation"
    _order = "sequence,id"
    
    connect_summary_costrate = fields.Many2one('estimation.work', string="Connect Summary Cost Rate")
    
    sequence = fields.Integer(string="No", )
    types = fields.Char(string="Type", )
    role = fields.Many2one('cost.rate', string='Role')
    currency_id = fields.Many2one('estimation.currency', compute='_compute_currency_id')
    yen_month = fields.Float(string="Unit (Currency/Month)", compute='_compute_yen_month', default=0.00)
    yen_day = fields.Float(string="Unit (Currency/Day)", compute='_compute_yen_month', default=0.00)
    vnd_day = fields.Float(string="Unit (VND/Day)", compute='_compute_yen_month', default=0.00)

    def _compute_currency_id(self):
        for item in self:
            estimation_id = self.connect_summary_costrate.id
            if type(estimation_id) != 'int':
                estimation_id = self.connect_summary_costrate.ids[0]
            item.currency_id = self.env['estimation.work'].search([('id', '=', estimation_id)]).currency_id

    @api.depends('role')
    def _compute_yen_month(self):
        for item in self:
            cost_rate = self.env['cost.rate'].search([('id', '=', item.role.id)])
            if cost_rate:
                estimation_id = self.connect_summary_costrate.id
                if type(estimation_id) != 'int':
                    estimation_id = self.connect_summary_costrate.ids[0]
                currency_id = self.env['estimation.work'].search([('id', '=', estimation_id)]).currency_id
                value_exchange = self.env['estimation.exchange.rate'].search([('currency_id', '=', currency_id.id)]).value
                if currency_id.id == 1:
                    item.yen_month = cost_rate.cost_usd
                    item.yen_day = cost_rate.cost_usd / 20
                    item.vnd_day = cost_rate.cost_vnd / 20
                else:
                    item.yen_month = cost_rate.cost_usd * value_exchange
                    item.yen_day = cost_rate.cost_usd * value_exchange / 20
                    item.vnd_day = cost_rate.cost_vnd / 20
            else:
                item.yen_month = 0.0
                item.yen_day = 0.0
                item.vnd_day = 0.0

