odoo.define('smo.CustomListView', function (require) {
  "use strict";

    const ListController = require('web.ListController')
    const viewRegistry = require('web.view_registry')
    const ListView = require('web.ListView')
    const ControlPanel = require('web.ControlPanel')
    const CustomDevicesListRenderer = require('smo.CustomDevicesListRenderer')

    const CustomListController = ListController.extend({
        renderButtons: function ($node) {
            this._super.apply(this, arguments)
            if (this.$buttons && this.modelName != 'smo.device.lc.schedule') {
                const $syncButton = $('<button type="button" class="btn btn-primary">')
                    .text('Sync').click(this.onClickSyncButton.bind(this))
                this.$buttons.append($syncButton)
          }
        },

        onClickSyncButton: function () {
            this.do_action('smo.sync_data_action')
        }
    })

    const CustomListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
          Controller: CustomListController,
          Renderer: CustomDevicesListRenderer,
        })
    })

    viewRegistry.add('smo_custom_list_view', CustomListView)
})

