from odoo import models, fields, api


class EstimationSummaryTotalCost(models.Model):
    _name = "estimation.summary.totalcost"
    _description = "Summary of each estimation"
    _order = "sequence,id"

    estimation_id = fields.Many2one('estimation.work', string="Estimation")

    sequence = fields.Integer(string="No", index=True, readonly=True, help='Use to arrange calculation sequence',
                              default=1)
    check_activate = fields.Boolean(string='Activate', default=False)
    module_id = fields.Many2one("estimation.module", string="Module")
    name = fields.Char(string="Components", default="Module")
    design_effort = fields.Float(string="Design",  compute='_compute_effort')
    dev_effort = fields.Float(string="Developer",)
    tester_effort = fields.Float(string="Tester", )
    comtor_effort = fields.Float(string="Comtor",)
    brse_effort = fields.Float(string="Brse", )
    pm_effort = fields.Float(string="PM",)

    total_effort = fields.Float(string="Total Effort (MD)", readonly=True, compute='_compute_total_effort')
    cost = fields.Float(string="Cost", readonly=True, compute='_compute_cost')

    @api.depends('estimation_id.add_lines_summary_costrate.yen_month', 'estimation_id.add_lines_summary_costrate.role', 'total_effort')
    def _compute_cost(self):
        for record in self:
            module_id = record.module_id.id
            cost_rate = self.env['estimation.summary.costrate'].search([('module_id', '=', module_id)])

            cost = 0
            for item_cost_rate in cost_rate:
                if item_cost_rate.module_id.id == module_id:
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

    @api.depends('estimation_id.add_lines_module.total_manday')
    def _compute_effort(self):
        for record in self:
            module_id = record.module_id.id
            if record.id:
                check_origin = False
            elif record.id == False:
                check_origin = False
            elif record.id.origin:
                check_origin = True
            else:
                check_origin = False

            design_total = 0.0
            dev_total = 0.0
            tester_total = 0.0
            comtor_total = 0.0
            pm_total = 0.0
            brse_total = 0.0

            for rec in record.estimation_id.add_lines_module:
                for item in rec.module_config_activity:

                    if item.module_id.id:
                        activity_module_id = item.module_id.id
                    elif item.module_id.id.origin:
                        activity_module_id = item.module_id.id.origin

                    if activity_module_id == module_id:
                        for i in item.add_lines_breakdown_activity:
                            if i.job_pos.job_position == 'Designer':
                                design_total += i.mandays
                            elif i.job_pos.job_position == 'Developer':
                                dev_total += i.mandays
                            elif i.job_pos.job_position == 'Tester':
                                tester_total += i.mandays
                            elif i.job_pos.job_position == 'Comtor':
                                comtor_total += i.mandays
                            elif i.job_pos.job_position == 'Brse':
                                brse_total += i.mandays
                            elif i.job_pos.job_position == 'Project manager':
                                pm_total += i.mandays
                    else:
                        continue

            if not check_origin:
                record.design_effort = design_total
                record.dev_effort = dev_total
                record.tester_effort = tester_total
                record.comtor_effort = comtor_total
                record.pm_effort = pm_total
                record.brse_effort = brse_total
            else:
                record.design_effort += design_total
                record.dev_effort += dev_total
                record.tester_effort += tester_total
                record.comtor_effort += comtor_total
                record.pm_effort += pm_total
                record.brse_effort += brse_total


class EstimationSummaryCostRate(models.Model):
    _name = "estimation.summary.costrate"
    _description = "Summary of cost rate in each estimation"
    _order = "sequence,module_id"

    connect_summary_costrate = fields.Many2one('estimation.work', string="Connect Summary Cost Rate")
    module_id = fields.Many2one("estimation.module", string="Module")
    name = fields.Char(string="Components", default="Module", readonly=True)

    sequence = fields.Integer(string="No", readonly=True)
    types = fields.Char(string="Type", readonly=True)
    role = fields.Many2one('cost.rate', string='Role')
    yen_month = fields.Float(string="Unit (Currency/Month)", store=True, default=0.00, readonly=True)
    yen_day = fields.Float(string="Unit (Currency/Day)", store=True, compute='_compute_yen_month', default=0.00, readonly=True)

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

