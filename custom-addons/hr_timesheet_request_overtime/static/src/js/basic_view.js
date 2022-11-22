odoo.define('hr_timesheet_request_overtime.BasicView', function (require) {
    "use strict";
    
    var session = require('web.session');
    var BasicView = require('web.BasicView');
    BasicView.include({
            init: function(viewInfo, params) {
                var self = this;
                this._super.apply(this, arguments);
                var model = self.controllerParams.modelName in ['hr.request.overtime'] ? 'True' : 'False';
                if(self.controllerParams.modelName == 'hr.request.overtime') {
                    session.user_has_group('hr_timesheet_request_overtime.group_archive').then(function(has_group) {
                        if(!has_group) {
                            self.controllerParams.archiveEnabled = 'False' in viewInfo.fields;
                        }
                    });
                }
            },
        });
    }); 