odoo.define('ds_support_services.BasicView', function (require) {
    "use strict";
    
    var session = require('web.session');
    var BasicView = require('web.BasicView');
    BasicView.include({
            init: function(viewInfo, params) {
                var self = this;
                this._super.apply(this, arguments);
                var model = self.controllerParams.modelName in ['support.services'] ? 'True' : 'False';
                if(self.controllerParams.modelName == 'support.services') {
                    session.user_has_group('ds_support_services.group_archive').then(function(has_group) {
                        if(!has_group) {
                            self.controllerParams.archiveEnabled = 'False' in viewInfo.fields;
                        }
                    });
                }
            },
        });
    }); 