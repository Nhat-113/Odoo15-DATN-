odoo.define('smo.CustomDevicesListRenderer', function (require) {
  'use strict';

  const ListRenderer = require('web.ListRenderer')
  const rpc = require('web.rpc')

  const CustomDevicesListRenderer = ListRenderer.extend({
    _updateLightBooleanToggle: function (SmoDeviceLcId, newState) {
      const self = this

      const $recordRow = this.$el.find(`tr[custom-data-id="smo.device.lc_${SmoDeviceLcId}"]`)
      
      if ($recordRow.length) {
        const recordId = $($recordRow).data('id')
        const record = self._getRecord(recordId)
        record.data.current_state = newState

        self.defs = []
        const $newRow = self._renderRow(record)
        $recordRow.replaceWith($newRow);
      }
    },

    _renderRow: function (record) {
      var $tr = this._super.apply(this, arguments)
      $tr.attr('custom-data-id', record.model + '_' + record.data.id)
      return $tr
    },

    _renderGroupRow: function (group, groupLevel) {
      const $row = this._super.apply(this, arguments)
      const { groupedBy } = this.state
      
      const groupedByModels = [
        'smo.device',
        'smo.device.iaq',
        'smo.device.lc',
        'smo.device.lc.schedule'
      ]

      if (groupedByModels.includes(group.model) && groupedBy.length === 1) {
        const itemNames = {
          'smo.device': 'devices',
          'smo.device.iaq': 'parameters',
          'smo.device.lc': 'lights',
          'smo.device.lc.schedule': 'schedules'
        }
        
        const field = groupedBy[0]
          
        let groupTitle = ''
        if (field == 'repeat_daily') {
          groupTitle = group.value == true ? 'Daily Repeating Schedules' : 'Onetime Schedules'
        }

        const itemName = itemNames[group.model] || 'items'     
          
        const customTitle = `${groupTitle == '' ? group.value : groupTitle} (${group.count} ${itemName})`
        $row.find('.o_group_name').text(customTitle)
      }

      return $row
    },
  })

  return CustomDevicesListRenderer
})
