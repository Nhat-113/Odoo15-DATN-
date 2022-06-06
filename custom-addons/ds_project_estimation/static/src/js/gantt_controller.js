odoo.define('rs_plan_gantt.ResourcePlanGanttController', function (require) {
    "use strict";
var AbstractController = require('web.AbstractController');
var core = require('web.core');
var dialogs = require('web.view_dialogs');
var session = require("web.session");
// var BasicController = require('web.BasicController');
var ResourcePlanGanttController = AbstractController.extend({
    custom_events: _.extend({}, AbstractController.prototype.custom_events, {
        // gantt_data_updated: '_onGanttUpdated',
        gantt_create_dp: '_onGanttCreateDataProcessor',
        gantt_config: '_onGanttConfig',
    }),
    date_object: new Date(),
    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.projectModel ='gantt.resource.planning'
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
                            const modelName = self.model.modelName || 'gantt.resource.planning';
                            const target_id = data.id;
                            const res_id = parseInt(target_id, 10).toString() === target_id ? parseInt(target_id, 10) : target_id;
                            const res_deferred = $.Deferred();
                            self.model.updateTask(data, modelName, res_id).then(function(res) {
                                res_deferred.resolve(res.result);
                                self.update({});
                            }, function(res){
                                if(res.message.data.name !== 'odoo.exceptions.ValidationError') {
                                    res_deferred.resolve({state: "error"});
                                    // gantt.deleteLink(res_id);
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
                return true;
            }
        });
        dp.attachEvent("onBeforeUpdate", function(id, state, data){
            data.csrf_token = core.csrf_token;
            data.model_name = self.modelName;
            data.timezone_offset = (-self.date_object.getTimezoneOffset());
            data.map_text = self.map_text;
            data.map_id_field = self.map_id_field;
            data.map_date_start = self.map_date_start;
            data.map_duration = self.map_duration;
            data.map_working_day = self.map_working_day;
            data.map_open = self.map_open;
            data.map_progress = self.map_progress;
            return true;
        });

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
            var title = 'Open: ' + task.text[1];
            if(self.form_dialog && !self.form_dialog.isDestroyed()){
                return false;
            }
            var session =  self.getSession();
            var context = session ? session.user_context : {};
            var modelName = self.model.modelName;
            var target_id = task.id;
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
        if(isChanged){
            var params = {
                context: this.context,
            };

            // this.update(params, options);
            this.update(params);
        }
    },
    _disableAllButtons: function () {
        this.renderer.disableAllButtons();
    },
    _enableAllButtons: function () {
        this.renderer.enableAllButtons();
    },

});
return ResourcePlanGanttController;

});