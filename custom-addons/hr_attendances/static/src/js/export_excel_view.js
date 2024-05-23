odoo.define('exportExcelAttendances', function(require) {
    "use strict";
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');

    var exportBtn = ListController.extend({
        buttons_template: 'export_excel_dialog_btn.button',
        events: _.extend({}, ListController.prototype.events, {
            'click .open_wizard_action': '_OpenWizardExport'
        }),

        _OpenWizardExport: function() {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'export.wizard',
                name: 'Export Attendances',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
                res_id: false
            });
        }
    });


    var HrAttendanceListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: exportBtn
        })
    });

    viewRegistry.add('wizard_export_btn', HrAttendanceListView);
});