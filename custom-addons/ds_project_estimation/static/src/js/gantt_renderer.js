odoo.define("rs_plan_gantt.ResourcePlanGanttRenderer", function(require) {
    "use strict";

    var AbstractRenderer = require("web.AbstractRenderer");
    var FormRenderer = require("web.FormRenderer");
    var session = require("web.session");
    var rpc = require('web.rpc');
    var ResourcePlanGanttRenderer = AbstractRenderer.extend({
        template: "rs_plan_gantt.resource_plan_gantt_view",
        ganttApiUrl: "/gantt_api",
        date_object: new Date(),
        events: _.extend({}, AbstractRenderer.prototype.events, {
            "click button.o_dhx_zoom_in": "_onClickZoomIn",
            "click button.o_dhx_zoom_out": "_onClickZoomOut",
            "click button.o_dhx_export_to_pdf": "_exportToPDF"
        }),
        init: function(parent, state, params) {
            this._super.apply(this, arguments);
            this.initDomain = params.initDomain;
            this.modelName = params.modelName;
            this.map_text = params.map_text;
            this.map_id_field = params.map_id_field;
            this.map_date_start = params.map_date_start;
            this.map_duration = params.map_duration;
            this.map_open = params.map_open;
            this.map_progress = params.map_progress;
            this.is_total_float = params.is_total_float;
            this.configStartDate = params.configStartDate;

            var self = this;
            gantt.config.grid_width = 180;
            gantt.config.work_time = true;
            gantt.config.skip_off_time = true;
            gantt.config.drag_links = false;
            gantt.plugins({
                tooltip: true,
            });

            const startDateEditor = { type: "date", map_to: "start_date" };
            const endDateEditor = { type: "date", map_to: "end_date" };

            // config left column
            gantt.config.drag_progress = false;
            gantt.config.columns = [{
                    name: "text",
                    tree: true,
                    resize: true,
                    label: "Job Positions",
                    width: 180,
                    template: function(item) {
                        return "<b>" + item.text[1] + "</b>";
                    },
                },
                {
                    name: "valueMM",
                    tree: true,
                    resize: true,
                    label: "Total (MM)",
                    width: 100,
                    template: function(item) {
                        return item.valueMM;
                    },
                }
            ];
            gantt.attachEvent("onTaskLoading", function(task) {

                //console.log(`task`, task);
                // if (task.custom_date) 
                task.start_date = gantt.date.convert_to_utc(task.start_date);
                task.end_date = gantt.date.convert_to_utc(task.end_date);

                // task.custom_date = gantt.date.parseDate(task.custom_date,"%m-%d-%y")
                return true;
            });
            gantt.templates.task_text = function (start, end, task) {
              return task.valueMM;
                
            };
            gantt.templates.task_class = function(start, end, task) {
                if (start - self.configStartDate === 0) {
                    return "none";
                }
                switch (task.deadline) {
                    case 1:
                        return "danger";
                    case 2:
                        return "warning";
                }
            };

            gantt.templates.grid_header_class = function(columnName, column) {
                if (columnName == "text") {
                    return "projectHeaderColor";
                }
                return "headerColor";
            };

            gantt.templates.rightside_text = function(start, end, task) {
                if (task.type === "milestone") {
                    return task.text;
                }
                return "";
            };

            // template is displayed when hover gantt item
            const tooltips = gantt.ext.tooltips;
            gantt.templates.tooltip_date_format = gantt.date.date_to_str("%F %j, %Y");
            gantt.templates.tooltip_text = function(start, end, task) {
                var type = "Job Positions"

                return `<b>${type}:</b> ${task.text[1]}<br/>
                <b>Value (MM):</b> ${task.valueMM}<br/>
                <b>Start date:</b> ${gantt.templates.tooltip_date_format(
                  start
                )} 
                <br/><b>End date:</b> ${gantt.templates.tooltip_date_format(
                  end
                )}`;
            };

            if (this.is_total_float) {
                gantt.config.columns.push({
                    name: "total_float",
                    label: "Total Float",
                    align: "center",
                });
            }

            //TODO: setup configurable weekend days.
            gantt.setWorkTime({ day: 5, hours: true });
            gantt.setWorkTime({ day: 6, hours: true });
            gantt.setWorkTime({ day: 0, hours: true });
            //gantt.setWorkTime({ hours: [0, 23] });

            var zoomConfig = {
                levels: [{
                        name: "day",
                        scale_height: 27,
                        min_column_width: 80,
                        scales: [{ unit: "day", step: 1, format: "%d %M" }],
                    },
                    {
                        name: "week",
                        scale_height: 50,
                        min_column_width: 50,
                        scales: [{
                                unit: "week",
                                step: 1,
                                format: function(date) {
                                    var dateToStr = gantt.date.date_to_str("%d %M");
                                    var endDate = gantt.date.add(date, +6, "day");
                                    var weekNum = gantt.date.date_to_str("%W")(date);
                                    return (
                                        "#" +
                                        weekNum +
                                        ", " +
                                        dateToStr(date) +
                                        " - " +
                                        dateToStr(endDate)
                                    );
                                },
                            },
                            { unit: "day", step: 1, format: "%j %D" },
                        ],
                    },
                    {
                        name: "month",
                        scale_height: 50,
                        min_column_width: 120,
                        scales: [
                            { unit: "month", format: "%F, %Y" },
                            { unit: "week", format: "Week #%W" },
                        ],
                    },
                    {
                        name: "quarter",
                        height: 50,
                        min_column_width: 90,
                        scales: [
                            { unit: "month", step: 1, format: "%M" },
                            {
                                unit: "quarter",
                                step: 1,
                                format: function(date) {
                                    var dateToStr = gantt.date.date_to_str("%M");
                                    var endDate = gantt.date.add(
                                        gantt.date.add(date, 3, "month"), -1,
                                        "day"
                                    );
                                    return dateToStr(date) + " - " + dateToStr(endDate);
                                },
                            },
                        ],
                    },
                    {
                        name: "year",
                        scale_height: 50,
                        min_column_width: 30,
                        scales: [{ unit: "year", step: 1, format: "%Y" }],
                    },
                ],
            };
            gantt.ext.zoom.init(zoomConfig);
            gantt.ext.zoom.setLevel("quarter");
        },
       
        _onClickZoomIn: function() {
            gantt.ext.zoom.zoomIn();
        },
        _onClickZoomOut: function() {
            gantt.ext.zoom.zoomOut();
        },

        _exportToPDF: function() {
            gantt.exportToPDF({
                header: "<style>.danger {border: 1px solid #990614;color: #f30f0f;background: #f30f0f;}.danger .gantt_task_progress {background: #990614;}.warning {border: 1px solid #eec41e;color: #ffffcc;background: #ffeb3b;}.warning .gantt_task_progress {background: #eec41e;}</style>",
            });
        },
        on_attach_callback: function() {
            this.renderGantt();
        },

        renderGantt: function() {
            gantt.init(this.$(".o_dhx_gantt").get(0));
            this.trigger_up("gantt_config");
            this.trigger_up("gantt_create_dp");
            if (!this.events_set) {
                var self = this;
                gantt.attachEvent("onBeforeGanttRender", function() {
                    var rootHeight = self.$el.height();
                    var headerHeight = self.$(".o_dhx_gantt_header").height();
                    self.$(".o_dhx_gantt").height(rootHeight - headerHeight);
                });
                this.events_set = true;
            }
            gantt.clearAll();
            var date_to_str = gantt.date.date_to_str(gantt.config.task_date);
            gantt.addMarker({
                start_date: new Date(), //a Date object that sets the marker's date
                css: "today", //a CSS class applied to the marker
                text: "Today", //the marker title
                title: date_to_str(new Date()), // the marker's tooltip
            });
            var rootHeight = this.$el.height();
            var headerHeight = this.$(".o_dhx_gantt_header").height();
            this.$(".o_dhx_gantt").height(rootHeight - headerHeight);
            gantt.parse(this.state.records);
        },
        _onUpdate: function() {},
        updateState: function(state, params) {
            // this method is called by the controller when the search view is changed. we should
            // clear the gantt chart, and add the new tasks resulting from the search
            var res = this._super.apply(this, arguments);
            gantt.clearAll();
            this.renderGantt();
            return res;
        },
        disableAllButtons: function() {
            // console.log('disableAllButtons:: Renderer');
            this.$(".o_dhx_gantt_header").find("button").prop("disabled", true);
        },
        enableAllButtons: function() {
            // console.log('enableAllButtons:: Renderer');
            this.$(".o_dhx_gantt_header").find("button").prop("disabled", false);
        },
        undoRenderCriticalTasks: function (data) {
          gantt.eachTask(function (item) {
            item.color = "";
          });
          gantt.getLinks().forEach(function (item) {
            item.color = "";
          });
          gantt.render();
        },
        renderCriticalTasks: function (data) {
          data.tasks.forEach(function (item) {
            var task = gantt.getTask(item);
            if (task) {
              task.color = "red";
            }
          });
          data.links.forEach(function (item) {
            var link = gantt.getLink(item);
            if (link) {
              link.color = "red";
            }
          });
          if (data.tasks.length > 0) {
            gantt.render();
          }
        },
        destroy: function() {
            gantt.clearAll();
            this._super.apply(this, arguments);
        },
    });
    return ResourcePlanGanttRenderer;
});