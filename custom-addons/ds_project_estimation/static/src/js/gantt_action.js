odoo.define('rs_plan_gantt.ResourcePlanGanttAction', function (require) {
    "use strict";
    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction');

    var ResourcePlanGanttAction = AbstractAction.extend({
        init: function (parent) {
            this._super.apply(this, arguments);
        },
    });
    core.action_registry.add("project_show_gantt", ResourcePlanGanttAction);
    // console.log('gantt action loaded');
    //hide popup pay to use of gantt chart
    window.alert = function() {};
    alert = function() {};
});