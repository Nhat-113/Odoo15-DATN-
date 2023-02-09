odoo.define("estimation.EstimationCustomizeResourcePlanFormView", function(require) {
    "use strict";
    const FormRenderer = require("web.FormRenderer");
    /**
     * Override the form renderer so that we can mount the component on render
     * to any div with the class o_partner_order_summary.
     */

    // This is function override form view for display 2 record Total MM & MD for resource planning tab
    FormRenderer.include({
        async _renderView() {
            await this._super(...arguments);
            var resourcePlanFooter = this.el.querySelectorAll('div[name="add_lines_resource_effort"] table tfoot');
            var resourcePlanHeader = this.el.querySelectorAll('div[name="add_lines_resource_effort"] table thead tr th')
            if (resourcePlanHeader.length != 0) {
                this._rpc({
                    model: "estimation.resource.plan.result.effort",
                    method: "search_read",
                    domain: [
                        ['estimation_id', '=', this.state.res_id]
                    ]

                }).then(data => {
                    for (var item = 0; item < data.length; item++) {
                        var nodeParentTr = document.createElement('tr');
                        for (var index = 1; index < resourcePlanHeader.length; index++) {
                            let fieldName = resourcePlanHeader[index].dataset.name;
                            var nodeChildTd = document.createElement('td');
                            
                            let vals = data[item][fieldName];
                            if (fieldName != 'sequence' && fieldName != 'name') {
                                vals = vals.toFixed(2);
                            }
                            let valsContent = document.createTextNode(vals);
                            
                            if (index == 1) {
                                nodeChildTd.setAttribute('colspan', '2'); // Merged 2 column of first column
                                nodeChildTd.style.textAlign = 'center';
                            }
                            nodeChildTd.appendChild(valsContent);
                            nodeParentTr.appendChild(nodeChildTd);
                        }
                        resourcePlanFooter[0].appendChild(nodeParentTr);
                    }
                })
            }
        },
    });
});