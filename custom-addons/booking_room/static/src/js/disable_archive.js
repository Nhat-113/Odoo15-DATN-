odoo.define('booking_room.BasicView', function (require) {
  "use strict";
  
  const session = require('web.session')
  const BasicView = require('web.BasicView')
  BasicView.include({
    init: function(viewInfo, params) {
      this._super.apply(this, arguments)
      const controllerParams = this.controllerParams
      if (controllerParams.modelName == 'meeting.room') {
        controllerParams.archiveEnabled = 'False' in viewInfo.fields
      }
    },
  })
})