odoo.define('rs_plan_gantt.ResourcePlanGanttModel', function(require) {
    "use strict";

    var AbstractModel = require('web.AbstractModel');
    var time = require('web.time');
    var rpc = require('web.rpc');
    var ResourcePlanGanttModel = AbstractModel.extend({
        get: function() {
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
        load: function(params) {
            this.map_id = params.id_field;
            this.map_text = params.text;
            this.map_date_start = params.date_start;
            this.map_duration = params.duration;
            this.map_progress = params.progress;
            this.map_portal_user_names = params.portal_user_names;


            this.map_open = params.open;
            this.map_total_float = params.total_float;
            this.modelName = params.modelName;
            this.configStartDate = params.configStartDate;
            return this._load(params);
        },
        reload: function(id, params) {
            return this._load(params);
        },
        _load: function(params) {
            params = params ? params : {};
            this.domain = params.domain || this.domain || [];
            this.modelName = params.modelName || this.modelName;
            var self = this;
            var fieldNames = [this.map_text, this.map_date_start, this.map_duration];
            this.map_open && fieldNames.push(this.map_open);
            // HL
            this.map_widget && fieldNames.push(this.map_widget);
            this.map_progress && fieldNames.push(this.map_progress);
            this.map_portal_user_names && fieldNames.push(this.map_portal_user_names);
            this.map_child_ids && fieldNames.push(this.map_child_ids)
            this.map_total_float && fieldNames.push(this.map_total_float);
            return this._rpc({
                model: this.modelName,
                method: 'search_read',
                fields: fieldNames,
                domain: this.domain
            }).then(async(records) => {
                var valuesMM = await self._fetchDataValueMM();
                self.convertData(records, valuesMM);
            })
        },

        convertData: function(records, valuesMM) {
            const data = [];
            var self = this;
            this.res_ids = [];
            const links = [];
            const formatFunc = gantt.date.str_to_date("%Y-%m-%d %h:%i:%s", true);
            records.forEach(function(record) {
                self.res_ids.push(record[self.map_id]);
                var datetime;
                const task = {};

                task.id = record[self.map_id] ? record[self.map_id] : parseInt(_.uniqueId());
                task.text = record[self.map_text] ? record[self.map_text] : record.job_position_id[1];
                task.duration = record[self.map_duration];
                task.progress = typeof record[self.map_progress] === 'undefined' ? 0 : record[self.map_progress] / 100;

                // if (record.type) {
                //     // Add serverId to get real id in edit mode
                //     task.serverId = record.serverId;
                //     datetime = record.start_date ? formatFunc(record.start_date) : formatFunc(record.milestone_date);
                // } else {
                    // Show start time of task
                    if (record[self.map_date_start]) {
                        datetime = formatFunc(record[self.map_date_start]);
                    } else {
                        datetime = self.configStartDate;
                    }

                    // Handle warning or danger of task
                    // Convert to days
                    const currentDuration = (new Date() - datetime) / 1000 / 86400;

                    // if Danger else if warning
                    if (currentDuration > record[self.map_duration] && task.progress != 1) {
                        task.deadline = 1;
                    } else if (currentDuration > 0 && currentDuration < record[self.map_duration]) {
                        if (record[self.map_duration]) {
                            let progress = (currentDuration) * (1 / record[self.map_duration]);
                            if (progress > task.progress) {
                                task.deadline = 2;
                            }
                        }
                    }
                // }

                task.start_date = datetime;
                task.open = record[self.map_open] ? record[self.map_open] : 'true';
                task.total_float = record[self.map_total_float];
                task.type = record.type ? record.type : "";
                task.valueMM = valuesMM.find(item => item.id == task.id).value_man_month

                data.push(task);
                if (!record.type) {}
            });

            // TODO COVERT pair user_ids and portal_user_name to assignees
            this.records = data;
            this.links = [];
        },

        _fetchDataValueMM: function() {
            return this._rpc({
                model: 'gantt.resource.planning',
                method: 'search_read',
                fields: ['value_man_month'],
                domain: []
            }).then(function (data) {
                return data;
            })
        },

        updateTask: function(data, modelName, id) {
            if (data.isProject) {
                return $.when();
            }

            var formatFunc = gantt.date.str_to_date("%d-%m-%Y %h:%i");
            const values = {
                job_position_id: data.text[0],
            }
            const datetime = time.datetime_to_str(formatFunc(data.start_date));
            values[this.map_date_start] = datetime;
            values[this.map_duration] = data.duration;
            return this._rpc({
                model: modelName,
                method: 'write',
                args: [].concat(id, values),
            });
        },
        createLink: function(data) {
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
        deleteLink: function(data) {
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
        // getCriticalPath: function () {
        //     return this._rpc({
        //         model: this.modelName,
        //         method: 'compute_critical_path',
        //         args: [this.res_ids],
        //     });
        // },
        schedule: function () {
            var self = this;
            return this._rpc({
                model: this.modelName,
                method: 'bf_traversal_schedule',
                args: [this.res_ids],
            });
        },
    });
    return ResourcePlanGanttModel;
});