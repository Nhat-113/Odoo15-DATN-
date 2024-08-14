odoo.define('smo.CustomListView', function (require) {
    "use strict";
  
      const ListController = require('web.ListController')
      const viewRegistry = require('web.view_registry')
      const ListView = require('web.ListView')
      const ControlPanel = require('web.ControlPanel')
      const CustomDevicesListRenderer = require('smo.CustomDevicesListRenderer')
      const busService = require('bus.BusService')
      const rpc = require('web.rpc')
  
      const CustomListController = ListController.extend({
            custom_events: _.extend({}, ListController.prototype.custom_events, {
                'bus_notification': '_onBusNotification',
            }),

            init: function (parent, model, renderer, params) {
                this._super.apply(this, arguments)

                this.call('bus_service', 'addChannel', 'smo_channel')
                this.call('bus_service', 'onNotification', this, this._onNotification)
                this.call('bus_service', 'startPolling')
            },

            _onNotification: function (notifications) {
                for (var i = 0; i < notifications.length; i++) {
                    var type = notifications[i]['type']
                    var payload = notifications[i]['payload']
                    
                    if (type == 'smo.device.lc/update') {
                        this._updateDeviceState(payload)
                    }
                }
            },

            _updateDeviceState: function (payload) {
                const smo_device_lc_id = payload['id']
                const state = payload['current_state']
                
                this.renderer._updateLightBooleanToggle(smo_device_lc_id, state);
            },

            _getActionMenuItems: function (state) {
                this.isExportEnable = false
                return this._super.apply(this, arguments)
            },

            renderButtons: function ($node) {
                this._super.apply(this, arguments)
                this._fetchManualSyncStatus()
            },

            _fetchManualSyncStatus: function() {
                const self = this
                rpc.query({
                    route: '/smo/sync/manual',
                    params: {}
                }).then(function (response) {
                    const manual = response.data.manual
                    if (manual == "True" && self.$buttons && self.modelName != 'smo.device.lc.schedule') {
                        const $syncButton = $('<button type="button" class="btn btn-primary">')
                            .text('Sync').click(self.onClickSyncButton.bind(self))
                        self.$buttons.append($syncButton)
                    }
                }).catch(function (error) {
                    console.error('Error get initial data from server: ', error)
                })
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
    }
)
  
  