odoo.define('dhx_gantt.GanttModel', function (require) {
    "use strict";

    var AbstractModel = require('web.AbstractModel');
    var time = require('web.time');
    var GanttModel = AbstractModel.extend({
        get: function () {
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
        load: function (params) {
            this.map_id = params.id_field;
            this.map_text = params.text;
            this.map_date_start = params.date_start;
            this.map_duration = params.duration;
            this.map_progress = params.progress;
            this.map_user_ids = params.user_ids;
            this.map_working_day = params.working_day;
            this.map_portal_user_names = params.portal_user_names;


            this.map_open = params.open;
            this.map_links_serialized_json = params.links_serialized_json;
            this.map_total_float = params.total_float;
            this.map_parent = 'project_id';
            this.map_phase = "phase_id";
            this.modelName = params.modelName;
            this.linkModel = params.linkModel;
            this.configStartDate = params.configStartDate;
            return this._load(params);
        },
        reload: function (id, params) {
            return this._load(params);
        },
        _load: function (params) {
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
            this.map_working_day && fieldNames.push(this.map_working_day);
            this.map_child_ids && fieldNames.push(this.map_child_ids);
            this.map_total_float && fieldNames.push(this.map_total_float);
            this.map_parent && fieldNames.push(this.map_parent);
            this.map_phase && fieldNames.push(this.map_phase);
            return this._rpc({
                model: this.modelName,
                method: 'search_read',
                fields: fieldNames,
                domain: this.domain
            }).then(async (records) =>  {
                var  milestones = await self.getMilestones();
                var  phases = await self.getPhases();
                phases = phases.map((phase) => ({...phase, serverId: phase.id, id: parseInt(_.uniqueId())}))
                milestones = milestones.map((milestone) => ({...milestone, serverId: milestone.id, id: parseInt(_.uniqueId())}))
                self.convertData(records.concat(phases, milestones), phases);
            })
        },
        getPhases: function() {
            return this._rpc({
                model: 'project.planning.phase',
                method: 'search_read',
                fields: ['name', 'start_date', 'phase_duration', 'type', 'working_day'],
                domain: [['project_id', '=', this.domain[1][2]]]
            }).then(function (data) {
                return data;
            })
        },

        getMilestones: function() {
            return this._rpc({
                model: 'project.planning.milestone',
                method: 'search_read',
                fields: ['name', 'milestone_date', 'type', 'phase_id'],
                domain: [
                    ['project_id', '=', this.domain[1][2]]
                ]
            }).then(function (data) {
                return data;
            })
        },
        convertData: function (records, phases) {
            const data = [];
            var self = this;
            this.res_ids = [];
            const links = [];
            const formatFunc = gantt.date.str_to_date("%Y-%m-%d %h:%i:%s", true);


            records.forEach(function (record) {
                self.res_ids.push(record[self.map_id]);

                var datetime;
                const task = {};

                // Find phase parent of task
                if (record[self.map_phase]) {
                    const phaseFound = phases.find((item) => item.name === record[self.map_phase][1])
                    if(phaseFound) {
                        task.parent = phaseFound.id;
                    }
                }

                // Find phase parent of milestone
                if (record.phase_id) {
                    const phaseFound = phases.find((item) => item.name === record.phase_id[1])
                    if(phaseFound) {
                        task.parent = phaseFound.id;
                    }
                }

                task.id = record[self.map_id] ? record[self.map_id] : parseInt(_.uniqueId());
                task.text = record[self.map_text] ? record[self.map_text] : record.name;
                task.duration = record[self.map_duration] ? record[self.map_duration]  : record.phase_duration;
                task.progress = typeof record[self.map_progress] === 'undefined' ? 0 : record[self.map_progress] / 100;

                if(record.type) {
                    // Add serverId to get real id in edit mode
                    task.serverId = record.serverId;
                    console.log(`datetime_milesone`, record.milestone_date + 1);
                    datetime = record.start_date ? formatFunc(record.start_date) : formatFunc(record.milestone_date);
                } else {
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
                }

                task.start_date = datetime;
                //datetime= gantt.date.convert_to_utc(datetime);
                //console.log(`datetime_utc`, datetime);
                task.open = record[self.map_open] ? record[self.map_open] : 'true';
                task.links_serialized_json = record[self.map_links_serialized_json];
                task.total_float = record[self.map_total_float];
                task.user_ids = record[self.map_user_ids];
                task.working_day = record[self.map_working_day];
                task.project_name = record[self.map_parent] ? record[self.map_parent][1] : "";
                task.type = record.type ? record.type : "";
                // if(task.type !== "milestone"){
                    task.start_date =gantt.date.convert_to_utc(task.start_date);
                // }   
                data.push(task);
                //console.log(`task`, task.start_date);
                if(!record.type) {
                    links.push.apply(links, JSON.parse(record.links_serialized_json))
                }
            });

            // TODO COVERT pair user_ids and portal_user_name to assignees
            this.records = data;
            this.links = links;
        },
        updateTask: function (data, modelName, id) {
            if (data.isProject) {
                return $.when();
            }

            var formatFunc = gantt.date.str_to_date("%d-%m-%Y %h:%i");
            const values = {
                name:  data.text,
            }
            const datetime = time.datetime_to_str(formatFunc(data.start_date));
            //datetime = gantt.date.convert_to_utc(datetime)
            switch (data.type) {
                case "milestone":
                    values['milestone_date'] = datetime;
                    break;
                case "phase":
                    values['start_date'] = datetime;
                    values['phase_duration'] = data.duration;
                    values['working_day'] = data.duration;
                    values['end_date'] = time.datetime_to_str(formatFunc(data.end_date));
                    break;
                default:
                    values[this.map_date_start] = datetime;
                    values[this.map_duration] = data.duration;
                    break;
            }
            return this._rpc({
                model: modelName,
                method: 'write',
                args: [].concat(id, values),
            });
        },
        createLink: function (data) {
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
        deleteLink: function (data) {
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
        getCriticalPath: function () {
            return this._rpc({
                model: this.modelName,
                method: 'compute_critical_path',
                args: [this.res_ids],
            });
        },
        schedule: function () {
            var self = this;
            return this._rpc({
                model: this.modelName,
                method: 'bf_traversal_schedule',
                args: [this.res_ids],
            });
        },
    });
    return GanttModel;
});
