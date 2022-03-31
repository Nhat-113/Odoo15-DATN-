from odoo import http


class Works(http.Controller):

    @http.route("/estimation/works")
    def list(self, **kwargs):
        Work = http.request.env["estimation.work"]
        works = Work.search([])
        return http.request.render(
            "estimation_app.work_list_template",
            {"works": works}
        )

class CostRates(http.Controller):

    @http.route("/estimation/rate")
    def list(self, **kwargs):
        Rate = http.request.env["cost.rate"]
        rates = Rate.search([])
        return http.request.render(
            "estimation_app.costrate_list_template",
            {"cost_rate": rates}
        )

class Activities(http.Controller):

    @http.route("/estimation/activity")
    def list(self, **kwargs):
        Activity = http.request.env["config.activity"]
        activities = Activity.search([])
        return http.request.render(
            "estimation_app.activity_list_template",
            {"activities": activities}
        )