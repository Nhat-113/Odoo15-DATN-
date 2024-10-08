odoo.define('smo.LcScheduleListView', function (require) {
    "use strict";

    const ListController = require('web.ListController')
    const viewRegistry = require('web.view_registry')
    const ListView = require('web.ListView')
    const ControlPanel = require('web.ControlPanel')

    const LcScheduleListController = ListController.extend({
        
    })

    const LcScheduleListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: LcScheduleListController,
        })
    })

    viewRegistry.add('smo_lc_schedule_list_view', LcScheduleListView)
})