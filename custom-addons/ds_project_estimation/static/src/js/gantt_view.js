odoo.define('rs_plan_gantt.ResourcePlanGanttView', function (require) {
    "use strict";

    var AbstractView = require('web.AbstractView');
    // var BasicView = require('web.BasicView');
    var GanttController = require('rs_plan_gantt.ResourcePlanGanttController');
    var GanttModel = require('rs_plan_gantt.ResourcePlanGanttModel');
    var GanttRenderer = require('rs_plan_gantt.ResourcePlanGanttRenderer');
    var viewRegistry = require('web.view_registry');
    // var resizeItem = require('rs_plan_gantt.resizeTaskViewGantt');

    var ResourcePlanGanttView = AbstractView.extend({
        viewType: 'rs_plan_gantt',
        icon: 'fa-tasks',
        config: _.extend({}, AbstractView.prototype.config, {
            Controller: GanttController,
            Model: GanttModel,
            Renderer: GanttRenderer,
        }),
        init: function (viewInfo, params) {
            this._super.apply(this, arguments);
            this.loadParams.type = 'list';

            this.loadParams.id_field = this.arch.attrs.id_field;
            this.loadParams.date_start = this.arch.attrs.date_start;
            this.loadParams.duration = this.arch.attrs.duration;
            this.loadParams.open = this.arch.attrs.open;
            this.loadParams.progress = this.arch.attrs.progress;
            this.loadParams.text = this.arch.attrs.text;
            this.loadParams.portal_user_names = this.arch.attrs.portal_user_names;
            this.loadParams.total_float = this.arch.attrs.total_float;
            this.loadParams.modelName = params.modelName;
            this.loadParams.configStartDate = new Date();

            this.loadParams.fieldNames = [
                this.arch.attrs.id_field,
                this.arch.attrs.date_start,
                this.arch.attrs.duration,
                this.arch.attrs.open,
                this.arch.attrs.progress,
                this.arch.attrs.text,
                this.arch.attrs.portal_user_names,
            ];

            this.rendererParams.configStartDate = this.loadParams.configStartDate;
            this.rendererParams.initDomain = params.domain;
            this.rendererParams.modelName = params.modelName;
            this.rendererParams.map_id_field = this.arch.attrs.id_field;
            this.rendererParams.map_date_start = this.arch.attrs.date_start;
            this.rendererParams.map_duration = this.arch.attrs.duration;
            this.rendererParams.map_open = this.arch.attrs.open;
            this.rendererParams.map_progress = this.arch.attrs.progress;
            this.rendererParams.map_text = this.arch.attrs.text;
            
            
            this.rendererParams.portal_user_names = this.arch.attrs.portal_user_names
            this.rendererParams.is_total_float = this.arch.attrs.total_float;
        },
        _processFieldsView: function (fieldsView, viewType) {
            var fv = this._super.apply(this, arguments);
            return fv;
        },
    })

    viewRegistry.add('rs_plan_gantt', ResourcePlanGanttView);
    return ResourcePlanGanttView;
});