odoo.define('dhx_gantt.GanttController', function (require) {
    "use strict";
var AbstractController = require('web.AbstractController');
var core = require('web.core');
var dialogs = require('web.view_dialogs');
var session = require("web.session");
// var BasicController = require('web.BasicController');
var GanttController = AbstractController.extend({
    custom_events: _.extend({}, AbstractController.prototype.custom_events, {
        // gantt_data_updated: '_onGanttUpdated',
        gantt_create_dp: '_onGanttCreateDataProcessor',
        gantt_config: '_onGanttConfig',
        gantt_show_critical_path: '_onShowCriticalPath',
        gantt_schedule: '_onGanttSchedule',
    }),
    date_object: new Date(),
    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.projectModel = 'project.project';  // todo: read from view arch
        this.milestoneModel = 'project.planning.milestone';
        this.phaseModel = 'project.planning.phase';
    },
    _onGanttCreateDataProcessor: function(event){
        // console.log('_onGanttCreateDataProcessor');
        var self = this;
        if(this.dp_created){
            return;
        }
        this.dp_created = true;
        var dp = gantt.createDataProcessor(function(entity, action, data, id){
            switch (action) {
                
                case "update":
                    // return self.trigger_up('gantt_data_updated', {entity, data});
                    switch(entity){
                        case "task":
                            const modelName = data.type === 'project' && self.projectModel || data.type === 'milestone' && self.milestoneModel || data.type === 'phase' && self.phaseModel || 'project.task';
                            const target_id = data.type === 'project' && data.serverId || data.type === 'milestone' && data.serverId || data.type === 'phase' && data.serverId || data.id;
                            const res_id = parseInt(target_id, 10).toString() === target_id ? parseInt(target_id, 10) : target_id;
                            const res_deferred = $.Deferred();
                            self.model.updateTask(data, modelName, res_id).then(function(res) {
                                res_deferred.resolve(res.result);
                                self.update({});
                            }, function(res){
                                if(res.message.data.name !== 'odoo.exceptions.ValidationError') {
                                    res_deferred.resolve({state: "error"});
                                    gantt.deleteLink(res_id);
                                }
                                self.update({});
                            });
                            return res_deferred;
                        break;
                    }
                    // return service.update(data);
                break;
                case "create":
                    switch(entity){
                        case "link":
                            var res_deferred = $.Deferred();
                            self.model.createLink(data).then(function(res) {
                                // set res.id as the id returned from the server to update client id :)
                                res.id = res[0];
                                res_deferred.resolve(res);
                            }, function(res){
                                // console.log('create link failed');
                                // console.log(res);
                                res_deferred.resolve({state: "error"});
                                gantt.deleteLink(data.id);
                            });
                            return res_deferred;
                        break;
                    }
                break;
                case "delete":
                    switch(entity){
                        case "link":
                            return self.model.deleteLink(data);
                    }
                break;
            }
        });
        dp.attachEvent("onAfterUpdate", function(id, action, tid, response){
            if(action == "error"){
                // console.log('nice "an error occured :)"');
            }else{
                // self.renderGantt();
                return true;
            }
        });
        dp.attachEvent("onBeforeUpdate", function(id, state, data){
            // console.log('BeforeUpdate. YAY!');
            data.csrf_token = core.csrf_token;
            data.model_name = self.modelName;
            //data.timezone_offset = (-self.date_object.getTimezoneOffset());
            data.map_text = self.map_text;
            data.map_text = self.map_text;
            data.map_id_field = self.map_id_field;
            data.map_date_start = self.map_date_start;
            data.map_duration = self.map_duration;
            data.map_working_day = self.map_working_day;
            data.map_open = self.map_open;
            data.map_progress = self.map_progress;
            data.link_model = self.link_model;
            // console.log('data are ');
            // console.log(data);
            return true;
        });
        gantt.attachEvent("onTaskLoading", function(task) { 
            if (task.working_day === 0 && task.type !== "milestone") {
                task.unscheduled = true;
            }
            if (task.type == "") {
                if(task.status[0] === 7) {
                    return false;
                }
            }
            return true;
        });
        // dp.attachEvent("onBeforeLinkAdd", function(id, link){
        //     let date_start_convert = data.start_date.split('-');

        //     if(!start_date.split) return
        // });
        dp.attachEvent("onBeforeDataSending", function(id, state, data) {
           //console.log(`state`,state );
            if(state!=="inserted" && state!=="deleted" && data.type !=="milestone" ) {
                let date_start_convert = data.start_date.split('-');
                date_start_convert.splice(0, 2, date_start_convert[1], date_start_convert[0]);
                date_start_convert.join('-');
                let date_start = new Date(date_start_convert);
                
                var datestring =
                    ("0" + (date_start.getDate() + 1)).slice(-2) +
                    "-" +
                    ("0" + (date_start.getMonth() + 1)).slice(-2) +
                    "-" +
                    date_start.getFullYear() +
                    " " +
                    ("0" + date_start.getHours()).slice(-2) +
                    ":" +
                    ("0" + date_start.getMinutes()).slice(-2);
    
                data.start_date = datestring;
            }
           
            return true;
        });
    //     gantt.attachEvent("onAfterTaskDrag", function (id, mode, e){
    //         let showTask = gantt.showTask;
    //         let taskObj = gantt.getTask(id);
    //         let id_before =   taskObj.id
    //         //console.log(`id before`, id_before);
    //         if(taskObj.type !== "milestone"){
    //             gantt.showTask = function(id_drag){
    //                 // console.log(`mode`, mode);
    //                 id_drag = id_before
    //                 // console.log('id after1',id_drag); 
    //                 showTask.apply(this, [id_drag]);
    //                 let attr = gantt.config.task_attribute;
    //                 // console.log(`attr`, attr);
    //                 // console.log('id after',id_drag); 
    //                 let timelineElement = document.querySelector(".gantt_task_line["+attr+"='"+id_drag+"']");

    //                 // console.log('timelineElement',timelineElement);
    //                 if(timelineElement)
    //                     timelineElement.scrollIntoView({block:"center"}); 
    //         };
    //     }
    //     return true; 
    // });
    gantt.attachEvent("onBeforeLinkAdd", function(id, link){
        // console.log(`id`, id);
        // console.log(`link`, link);
        var sourceTask = gantt.getTask(link.source);
        var targetTask = gantt.getTask(link.target);
        if (targetTask.type == "milestone" || targetTask.type =="phase"){
            gantt.alert("This link is illegal for milestone and phase");
            return false;
        }
    });
        // deny drag if task have progress === 100% and phase and role user
        session.user_has_group("ds_project_planning.group_project_team_leader").then(function(has_group) {
            gantt.attachEvent("onBeforeTaskDrag", function (id, mode, e) {
                var taskObj = gantt.getTask(id);
                if (has_group) {
                    if( taskObj.progress === 1 || taskObj.type == "phase" ) {
                        return false;
                    }
                    return true;
                }
                return false;
            });
            if (!has_group) {
                var element = document.getElementById("dropdownMenuButton");
                element.parentNode.removeChild(element);
    
                var element2 = document.getElementById("o_dhx_button_left");
                element2.parentNode.removeChild(element2);
            }else {
                // var element = document.getElementById("o_dhx_button_left");
                document.getElementById("o_dhx_button_left").style.display = "block";
                document.getElementById("dropdownMenuButton").style.display = "block";
            }
        });
    
    gantt.attachEvent("onBeforeTaskMove", function(id, parent, tindex){
        // console.log('tindex',parent);
        var task = gantt.getTask(id);
        if(task.parent != parent)
        {
            return false;
        }
        return true;
    });

        //deny drag phase 
        // gantt.attachEvent("onBeforeTaskDrag", function(id, mode, e){
        //     var taskObj = gantt.getTask(id);
        //     if (taskObj.type == "phase") {
        //         return false;
        //     }
        //     return true;
        // });
    },

    _onGanttConfig: function(){
        var self = this;
        if(this.gantt_configured){
            return;
        }
        this.gantt_configured = true;
        gantt.attachEvent('onBeforeLightbox', function(id) {
            // todo: Change this to trigger_up from renderer !!! to avoid errors
            var task = gantt.getTask(id);
            var title = 'Open: ' + task.text;
            if(self.form_dialog && !self.form_dialog.isDestroyed()){
                return false;
            }
            var session =  self.getSession();
            var context = session ? session.user_context : {};
            var modelName = task.type === 'project' && self.projectModel || task.type === 'milestone' && self.milestoneModel || task.type === 'phase' && self.phaseModel || self.model.modelName;
            var target_id = task.type === 'project' && task.serverId || task.type === 'milestone' && task.serverId || task.type === 'phase' && task.serverId || task.id;
            var res_id = parseInt(target_id, 10).toString() === target_id ? parseInt(target_id, 10) : target_id;
            self.form_dialog = new dialogs.FormViewDialog(self, {
                res_model: modelName,
                res_id: res_id,
                context: context,
                title: title,
                // view_id: Number(this.open_popup_action),
                on_saved: function(record, isChanged){
                    self.write_completed(record, isChanged);
                }
            }).open();
            return false;//return false to prevent showing the default form
        });
    },
    write_completed: function (record, isChanged) {
        // console.log('write_completed');
        // console.log(this.renderer.domain);
        if(isChanged){
            var params = {
                context: this.context,
            };

            // this.update(params, options);
            this.update(params);
        }
    },
    _onShowCriticalPath: function(){
        event.stopPropagation();
        var self = this;
        var def;

        if(this.criticalRendered){
            this.criticalRendered = false;
            self.renderer.undoRenderCriticalTasks();
            return;
        }
        else{
            this.criticalRendered = true;
        }

        this._disableAllButtons();
        def = self.model.getCriticalPath().then(function (result) {
            // console.log('critical path result');
            // console.log(result);
            self.renderer.renderCriticalTasks(result);
        });
        def.always(this._enableAllButtons.bind(this));
    },
    _disableAllButtons: function () {
        this.renderer.disableAllButtons();
    },
    _enableAllButtons: function () {
        this.renderer.enableAllButtons();
    },
    _onGanttSchedule: function(){
        var self = this;
        this.model.schedule().then(function () {
            self.update({reload: true});
            self.renderer.renderGantt();
        });
    },
});
return GanttController;

});
