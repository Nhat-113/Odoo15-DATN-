odoo.define('smo.CustomDevicesFormRenderer', function (require) {
    'use strict';

    const FormRenderer = require('web.FormRenderer')

    const CustomDevicesFormRenderer = FormRenderer.extend({
        _updateLightBooleanToggleInNotebook: function (SmoDeviceLcId, newState) {
            const self = this
            const data = self.state.data
            let recordId
            let record

            data.smo_device_lc_ids.data.forEach(_record => {
                if (_record.data.id == SmoDeviceLcId) {
                    recordId = _record.id
                    record = _record
                }
            })

            if (recordId && record) {
                self.trigger_up('reload')
            }              
        },
    })

    return CustomDevicesFormRenderer
})
