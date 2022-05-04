odoo.define('dhx_gantt.GanttRenderer', function (require) {
    "use strict";

    var AbstractRenderer = require('web.AbstractRenderer');
    var FormRenderer = require('web.FormRenderer');
    var GanttRenderer = AbstractRenderer.extend({
        template: "dhx_gantt.gantt_view",
        ganttApiUrl: "/gantt_api",
        date_object: new Date(),
        events: _.extend({}, AbstractRenderer.prototype.events, {
            'click button.o_dhx_critical_path': '_onClickCriticalPath',
            'click button.o_dhx_reschedule': '_onClickReschedule',
            'click button.o_dhx_zoom_in': '_onClickZoomIn',
            'click button.o_dhx_zoom_out': '_onClickZoomOut',
            'click button.o_dhx_export_to_pdf': '_exportToPDF',
            'click a.o_dhx_create_phase': '_onBtnCreatePhase',
            'click a.o_dhx_create_milestone': '_onBtnCreateMilestone',
            'click button.o_dhx_calendar_resource': '_onBtnCalendarResource',
        }),
        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.initDomain = params.initDomain;
            this.modelName = params.modelName;
            this.map_text = params.map_text;
            this.map_id_field = params.map_id_field;
            this.map_date_start = params.map_date_start;
            this.map_duration = params.map_duration;
            this.map_open = params.map_open;
            this.map_progress = params.map_progress;
            this.map_links_serialized_json = params.map_links_serialized_json;
            this.link_model = params.link_model;
            this.is_total_float = params.is_total_float;


            var self = this;
            gantt.config.grid_width = 580;
            gantt.config.work_time = true;
            gantt.config.skip_off_time = true;

            gantt.plugins({
                tooltip: true
            });

            function byId(id) {
                return `
                    <div class="o_field_many2manytags avatar o_clickable_m2x_avatar o_field_widget o_field_many2manytags_multi" name="user_ids">
                        <img src="/web/image/res.users/${id}/avatar_128" title="" data-id="2" class="rounded-circle o_m2m_avatar">
                    </div>
                `
            }

            gantt.config.drag_progress = false;
            gantt.config.columns = [
                {name: "text", tree: true, resize: true, label: this.state.records.data[0].project_name, width: 180},
                {name: "start_date", align: "center", resize: true, width: 120},
                {name: "end_date", label: "End time", align: "center", resize: true, width: 120},
                {name: "duration", align: "center", resize: true},
                {
                    name: "assignees", width: 80, label: "Assignees", align: "center", resize: true, template: function (task) {
                        var result = "";
                        var assignees = task.user_ids
    
                        if (!assignees)
                            return;
    
                        assignees.forEach(function (element) {
                            var assignee = byId(element);
                            result += assignee;
                        });
    
                        return result
                    }
                }
            ]

            gantt.templates.task_class = function (start, end, task) {
                switch (task.deadline) {
                    case 1:
                        return "danger";
                    case 2:
                        return "warning";
                }
            };

            gantt.templates.grid_header_class = function(columnName, column){
                if(columnName == 'text') {
                    return "projectHeaderColor"
                }
                return "headerColor";
              };

            gantt.templates.rightside_text = function (start, end, task) {
                if (task.type === "milestone") {
                    return task.text;
                }
                return "";
            };

            const tooltips = gantt.ext.tooltips;
            gantt.templates.tooltip_date_format = gantt.date.date_to_str("%F %j, %Y");
			gantt.templates.tooltip_text = function (start, end, task) {
                // Add assignee
				return `<b>Task:</b> ${task.text}<br/>
                <b>Duration:</b> ${task.duration}<br/>
                <b>Start date:</b> ${gantt.templates.tooltip_date_format(start)} 
                <br/><b>End date:</b> ${gantt.templates.tooltip_date_format(end)}`
					
			};
            

            if(this.is_total_float){
                gantt.config.columns.push({name: "total_float", label: "Total Float", align: "center"})
            }

            //TODO: setup configurable weekend days.
            gantt.setWorkTime({day:5, hours: true });
            gantt.setWorkTime({day:6, hours: true });
            gantt.setWorkTime({day:0, hours: true });
            gantt.setWorkTime({hours: [0,23]});

            var zoomConfig = {
                levels: [
                    {
                        name:"day",
                        scale_height: 27,
                        min_column_width:80,
                        scales:[
                            {unit: "day", step: 1, format: "%d %M"}
                        ]
                    },
                    {
                        name:"week",
                        scale_height: 50,
                        min_column_width:50,
                        scales:[
                            {unit: "week", step: 1, format: function (date) {
                                var dateToStr = gantt.date.date_to_str("%d %M");
                                var endDate = gantt.date.add(date, +6, "day");
                                var weekNum = gantt.date.date_to_str("%W")(date);
                                return "#" + weekNum + ", " + dateToStr(date) + " - " + dateToStr(endDate);
                            }},
                            {unit: "day", step: 1, format: "%j %D"}
                        ]
                    },
                    {
                        name:"month",
                        scale_height: 50,
                        min_column_width:120,
                        scales:[
                            {unit: "month", format: "%F, %Y"},
                            {unit: "week", format: "Week #%W"}
                        ]
                    },
                    {
                        name:"quarter",
                        height: 50,
                        min_column_width:90,
                        scales:[
                            {unit: "month", step: 1, format: "%M"},
                            {
                                unit: "quarter", step: 1, format: function (date) {
                                    var dateToStr = gantt.date.date_to_str("%M");
                                    var endDate = gantt.date.add(gantt.date.add(date, 3, "month"), -1, "day");
                                    return dateToStr(date) + " - " + dateToStr(endDate);
                                }
                            }
                        ]
                    },
                    {
                        name:"year",
                        scale_height: 50,
                        min_column_width: 30,
                        scales:[
                            {unit: "year", step: 1, format: "%Y"}
                        ]
                    }
                ]
            };
            gantt.ext.zoom.init(zoomConfig);
            gantt.ext.zoom.setLevel("week");
        },
        _onClickCriticalPath: function(){
            // console.log('_onClickCriticalPath');
            this.trigger_up('gantt_show_critical_path');
        },
        _onClickReschedule: function(){
            // console.log('_onClickReschedule');
            this.trigger_up('gantt_schedule');
        },
        _onClickZoomIn: function(){
            // console.log('_onClickZoomIn');
            gantt.ext.zoom.zoomIn();
        },
        _onClickZoomOut: function(){
            // console.log('_onClickZoomOut');
            gantt.ext.zoom.zoomOut();
        },

        _exportToPDF: function() {
            gantt.exportToPDF();
        },
        _onBtnCreatePhase: function (ev) {
            // prevent the event propagation 
            if (ev) {
                ev.stopPropagation();
            }
            var self = this;
            var project_id = this.initDomain[0][2];
            return this._rpc({
                model: 'project.planning.phase',
                method: 'open_create_phase',
                args: [project_id],
            }).then(function(result) {
                // location.reload();
                self.do_action(result);
            });
        },
        _onBtnCreateMilestone: function (ev) {
            // prevent the event propagation 
            if (ev) {
                ev.stopPropagation();
            }
            var self = this;
            var project_id = this.initDomain[0][2];
            return this._rpc({
                model: 'project.planning.milestone',
                method: 'open_create_milestone',
                args: [project_id],
            }).then(function(result) {
                self.do_action(result);
            });
        },
        _onBtnCalendarResource: function (ev) {
            // prevent the event propagation 
            if (ev) {
                ev.stopPropagation();
            }
            var self = this;
            var project_id = this.initDomain[0][2];
            console.log('project_id', project_id);
            return this._rpc({
                model: 'planning.calendar.resource',
                method: 'open_calendar_resource',
                args: [project_id],
            }).then(function(result) {
                self.do_action(result);
            });
        },
        on_attach_callback: function () {
            this.renderGantt();
            // console.log('on_attach_callback');
            // console.log(this.$el);
        },

        renderGantt: function(){
            gantt.init(this.$('.o_dhx_gantt').get(0));
            this.trigger_up('gantt_config');
            this.trigger_up('gantt_create_dp');
            if(!this.events_set){
                var self = this;
                gantt.attachEvent('onBeforeGanttRender', function() {
                    // console.log('tadaaaa, onBeforeGanttRender');
                    var rootHeight = self.$el.height();
                    var headerHeight = self.$('.o_dhx_gantt_header').height();
                    self.$('.o_dhx_gantt').height(rootHeight - headerHeight);
                });
                this.events_set = true;
            }
            gantt.clearAll();
            var date_to_str = gantt.date.date_to_str(gantt.config.task_date);
            gantt.addMarker({
                start_date: new Date(), //a Date object that sets the marker's date
                css: "today", //a CSS class applied to the marker
                text: "Today", //the marker title
                title:date_to_str( new Date()) // the marker's tooltip
            });
            var rootHeight = this.$el.height();
            var headerHeight = this.$('.o_dhx_gantt_header').height();
            this.$('.o_dhx_gantt').height(rootHeight - headerHeight);
            gantt.parse(this.state.records);
        },
        _onUpdate: function () {
        },
        updateState: function (state, params) {
            // this method is called by the controller when the search view is changed. we should 
            // clear the gantt chart, and add the new tasks resulting from the search
            var res = this._super.apply(this, arguments);
            gantt.clearAll();
            this.renderGantt();
            return res;
        },
        disableAllButtons: function(){
            // console.log('disableAllButtons:: Renderer');
            this.$('.o_dhx_gantt_header').find('button').prop('disabled', true);
        },
        enableAllButtons: function(){
            // console.log('enableAllButtons:: Renderer');
            this.$('.o_dhx_gantt_header').find('button').prop('disabled', false);
        },
        undoRenderCriticalTasks: function(data){
            gantt.eachTask(function(item){
                item.color = "";
            });
            gantt.getLinks().forEach(function(item){
                item.color = "";
            });
            gantt.render();
        },
        renderCriticalTasks: function(data){
            data.tasks.forEach(function(item){
                var task = gantt.getTask(item);
                if(task){
                    task.color = "red";
                }
            });
            data.links.forEach(function(item){
                var link = gantt.getLink(item);
                if(link){
                    link.color = "red";
                }
            });
            if(data.tasks.length > 0){
                gantt.render();
            }
        },
        destroy: function () {
            gantt.clearAll();
            this._super.apply(this, arguments);
        },
    });
    return GanttRenderer;
});

// code that i worked so hard for i am not ready to throw it yet :D
            // Approach 1: use dhx_gantt's dataProcessor to read from server api(controller)
            // console.log('ganttApiUrl');
            // console.log(this.ganttApiUrl);
            // console.log('initDomain');
            // console.log(JSON.stringify(this.initDomain));
            // console.log('JSON.stringify(this.undefinedStuff)');
            // console.log(JSON.stringify(this.undefinedStuff));
            // console.log('1243');
            // console.log(this.ganttApiUrl);
            // console.log(this.ganttApiUrl + '?domain=');
            // console.log(this.ganttApiUrl + '?domain=' + this.initDomain ? JSON.stringify(this.initDomain) : 'False');
            // console.log(this.ganttApiUrl + '?domain=' + (this.initDomain ? JSON.stringify(this.initDomain) : 'False'));
            // console.log(this.ganttApiUrl + '?domain=' + this.initDomain);

            // var domain_value = (this.initDomain ? JSON.stringify(this.initDomain) : 'False');
            // var initUrl = this.ganttApiUrl +
            // '?domain=' + domain_value +
            // '&model_name=' + this.modelName +
            // '&timezone_offset=' + (-this.date_object.getTimezoneOffset());
            // console.log('initUrl');
            // console.log(initUrl);

            // [
            //     {name:"add", label:"", width:50, align:"left" },

            //     {name:"text",       label:textFilter, width:250, tree:true },
            //     {name:"start_date", label:"Start time", width:80, align:"center" },
            //     {name:"duration",   label:"Duration",   width:60, align:"center" }
            // ]
 

            // gantt.load(initUrl);
            // var dp = new gantt.dataProcessor(initUrl);
            // keep the order of the next 3 lines below
            // var dp = gantt.createDataProcessor({
            //     url: initUrl,
            //     mode:"REST",
            // });
            // // dp.init(gantt);
            // dp.setTransactionMode({
            //     mode: "REST",
            //     payload: {
            //         csrf_token: core.csrf_token,
            //         link_model: this.link_model,
            //         model_name: self.modelName
            //     },
            // });
            // var dp = gantt.createDataProcessor(function(entity, action, data, id){
            //     console.log('createDataProcessor');
            //     console.log('entity');
            //     console.log({entity});
            //     console.log({action});
            //     console.log({data});
            //     console.log({id});
            //     const services = {
            //         "task": this.taskService,
            //         "link": this.linkService
            //     };
            //     const service = services[entity];
            //     switch (action) {
            //         case "update":
            //             self.trigger_up('gantt_data_updated', {entity, data});
            //             return true;
            //             // return service.update(data);
            //         case "create":
            //             self.trigger_up('gantt_data_created', {entity, data});
            //             // return service.insert(data);
            //         case "delete":
            //             self.trigger_up('gantt_data_deleted', {entity, data});
            //             // return service.remove(id);
            //     }
            // });

            // dp.attachEvent("onAfterUpdate", function(id, action, tid, response){
            //     if(action == "error"){
            //         console.log('nice "an error occured :)"');
            //     }else{
            //         // self.renderGantt();
            //         return true;
            //     }
            // });
            // dp.attachEvent("onBeforeUpdate", function(id, state, data){
            //     console.log('BeforeUpdate. YAY!');
            //     data.csrf_token = core.csrf_token;
            //     data.model_name = self.modelName;
            //     data.timezone_offset = (-self.date_object.getTimezoneOffset());
            //     data.map_text = self.map_text;
            //     data.map_text = self.map_text;
            //     data.map_id_field = self.map_id_field;
            //     data.map_date_start = self.map_date_start;
            //     data.map_duration = self.map_duration;
            //     data.map_open = self.map_open;
            //     data.map_progress = self.map_progress;
            //     data.link_model = self.link_model;
            //     console.log('data are ');
            //     console.log(data);
            //     return true;
            // });

            // gantt.attachEvent("onBeforeLinkDelete", function(id, item){
            //     data.csrf_token = core.csrf_token;
            //     data.link_model = self.link_model;
            //     return true;
            // });
            // Approach 2: use odoo's mvc
            // console.log('this.state');
            // console.log(this.state);
            // console.log('SETTING TO ');
            // console.log(this.state.records);
            // gantt.init(this.$el.find('.o_dhx_gantt').get(0));