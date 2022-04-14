odoo.define('dhx_gantt.GanttModel', function (require) {
    "use strict";

    var AbstractModel = require('web.AbstractModel');
    var time = require('web.time');
    var GanttModel = AbstractModel.extend({
        get: function(){
            var data = [];
            var links = [];

            var gantt_model = {
                data: this.records,
                links: this.links,
            }
            var res = {
                records: gantt_model,
            };
            return res;
        },
        load: function(params){
            this.map_id = params.id_field;
            this.map_text = params.text;
            this.map_date_start = params.date_start;
            this.map_duration = params.duration;
            this.map_progress = params.progress;
            // HL
            this.map_child_ids = params.child_ids;
            this.map_user_ids = params.user_ids;
            this.map_portal_user_names = params.portal_user_names;
            // this.map_widget = params.widget

            
            this.map_open = params.open;
            this.map_links_serialized_json = params.links_serialized_json;
            this.map_total_float = params.total_float;
            this.map_parent = 'project_id';
            this.modelName = params.modelName;
            this.linkModel = params.linkModel;
            return this._load(params);
        },
        reload: function(id, params){
            return this._load(params);
        },
        _load: function(params){
            params = params ? params : {};
            this.domain = params.domain || this.domain || [];
            this.modelName = params.modelName || this.modelName;
            var self = this;
            var fieldNames = [this.map_text, this.map_date_start, this.map_duration];
            this.map_open && fieldNames.push(this.map_open);
            this.map_links_serialized_json && fieldNames.push(this.map_links_serialized_json);
            // HL
            this.map_widget && fieldNames.push(this.map_widget);
            this.map_progress && fieldNames.push(this.map_progress);
            this.map_portal_user_names && fieldNames.push(this.map_portal_user_names);
            this.map_user_ids && fieldNames.push(this.map_user_ids);
            this.map_child_ids && fieldNames.push(this.map_child_ids)
            this.map_total_float && fieldNames.push(this.map_total_float);
            this.map_parent && fieldNames.push(this.map_parent);
            return this._rpc({
                model: this.modelName,
                method: 'search_read',
                fields: fieldNames,
                domain: this.domain,
                orderBy: [{
                    name: this.map_date_start,
                    asc: true,
                }]
            })
            .then(function (records) {
                self.convertData(records);
            });
        },
        convertData: function(records){
            const data = [];
            var self = this;
            this.res_ids = [];
            const links = [];
            const formatFunc = gantt.date.str_to_date("%Y-%m-%d %h:%i:%s", true);

            records.forEach(function(record){
                self.res_ids.push(record[self.map_id]);
                var datetime;
                if(record[self.map_date_start]){
                    datetime = formatFunc(record[self.map_date_start]);
                }else{
                    datetime = false;
                }

                const task = {};
                if(self.map_parent){
                    var projectFound = data.find(function(element) {
                        return element.type === 'project' && element.serverId == record[self.map_parent][0];
                    });
                    
                    if(!projectFound){
                        var project = {
                            id: _.uniqueId('project-'),
                            serverId: record[self.map_parent][0],
                            text: record[self.map_parent][1],
                            type: 'project',
                            open: true,
                        }
                        task.parent = project.id;
                        data.push(project);
                    }else{
                        task.parent = projectFound.id;
                    }
                }
                task.id = record[self.map_id];
                task.text = record[self.map_text];
                task.start_date = datetime;

                // Handle warning or danger task
                // Convert to days
                const currentDuration = (new Date() - datetime)/1000/86400;

                // if Danger else if warning
                if (currentDuration > record[self.map_duration] && record[self.map_progress] !=1) {
                    task.deadline = 1;
                } else if(currentDuration > 0 && currentDuration < record[self.map_duration]) {
                    if(record[self.map_duration]) {
                        let progress = (currentDuration) *(1/record[self.map_duration]);
                        if(progress > record[self.map_progress]) {
                            task.deadline = 2;
                        }
                    }
                }


                task.duration = record[self.map_duration];
                task.progress = record[self.map_progress];
                task.open = record[self.map_open];
                task.links_serialized_json = record[self.map_links_serialized_json];
                task.total_float = record[self.map_total_float];
                task.user_ids = record[self.map_user_ids];

                data.push(task);
                links.push.apply(links, JSON.parse(record.links_serialized_json))
            });
            // TODO COVERT pair user_ids and portal_user_name to assignees
            this.records = data;
            this.links = links;
        },
        updateTask: function(data){
            if(data.isProject){
                return $.when();
            }
            var args = [];
            var values = {};

            var id = data.id;
            values[this.map_text] = data.text;
            values[this.map_duration] = data.duration;
            if (this.map_open){
                values[this.map_open] = data.open;
            }
            if (this.map_progress){
                values[this.map_progress] = data.progress;
            }
            // TODO
            // convert time from dhx's string, to a javascript datetime, then to odoo's sting format :D
            var formatFunc = gantt.date.str_to_date("%d-%m-%Y %h:%i");
            values[this.map_date_start] = time.datetime_to_str(formatFunc(data.start_date));
            args.push(id);
            args.push(values)
            return this._rpc({
                model: this.modelName,
                method: 'write',
                args: args,
            });
        },
        createLink: function(data){
            // console.log('createLink');
            // console.log({data});
            var args = [];
            var values = {};

            values.id = data.id;
            values.task_id = data.source;
            values.depending_task_id = data.target;
            values.relation_type = data.type;

            args.push([values]);
            return this._rpc({
                model: this.linkModel,
                method: 'create',
                args: args,
            });
        },
        deleteLink: function(data){
            // console.log('deleteLink');
            // console.log({data});
            var args = [];

            args.push([data.id]);
            return this._rpc({
                model: this.linkModel,
                method: 'unlink',
                args: args,
            });
        },
        getCriticalPath: function(){
            return this._rpc({
                model: this.modelName,
                method: 'compute_critical_path',
                args:[this.res_ids],
            });
        },
        schedule: function(){
            var self = this;
            return this._rpc({
                model: this.modelName,
                method: 'bf_traversal_schedule',
                args:[this.res_ids],
            });
        },
    });
    return GanttModel;
});