odoo.define('smo.CustomFormView', function (require) {
    "use strict";

    const FormController = require('web.FormController')
    const viewRegistry = require('web.view_registry')
    const FormView = require('web.FormView')
    const ControlPanel = require('web.ControlPanel')
    const CustomDevicesFormRenderer = require('smo.CustomDevicesFormRenderer')
    const busService = require('bus.BusService')

    const CustomFormController = FormController.extend({
        custom_events: _.extend({}, FormController.prototype.custom_events, {
            'bus_notification': '_onBusNotification',
        }),

        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments)

            this.call('bus_service', 'addChannel', 'smo_channel')
            this.call('bus_service', 'onNotification', this, this._onNotification)
            this.call('bus_service', 'startPolling')
        },

        _onNotification: function (notifications) {
            const self = this
        
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
            
            this.renderer._updateLightBooleanToggleInNotebook(smo_device_lc_id, state);
        },
    })

    const CustomFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: CustomFormController,
            Renderer: CustomDevicesFormRenderer,
        })
    })

    viewRegistry.add('smo_custom_form_view', CustomFormView)
})


