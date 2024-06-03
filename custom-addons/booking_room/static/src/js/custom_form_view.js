odoo.define('booking_room.meeting_view_form', function (require) {
  "use strict";

  var core = require("web.core");
  var Dialog = require("web.Dialog");
  var rpc = require("web.rpc");
  var QWeb = core.qweb;
  const FormController = require('web.FormController');
  const FormView = require('web.FormView');
  const viewRegistry = require('web.view_registry');
  var _t = core._t;

  // Custom Form Controller
  const CustomFormController = FormController.extend({
      
    _deleteRecords: function (ids) {
      function doIt() {
          return self.model
              .deleteRecords(ids, self.modelName)
              .then(self._onDeletedRecords.bind(self, ids));
      }
      var self = this;
      var id = self.model.loadParams.res_id;
      var type_view = "form_view";

      var dialog = new Dialog(this, {
        title: _t("Delete Confirmation"),
        size: "medium",
        $content: $(QWeb.render("booking_room.RecurrentEventUpdateForm", {})),
        buttons: [
          {
            text: _t("OK"),
            classes: "btn btn-primary",
            close: true,
            click: function () {
              var selectedValue = $('input[name="recurrence-update"]:checked').val();
              var reason_delete = $('input[name="reason"]:checked').val();
              if (reason_delete=="others"){
                reason_delete = $('textarea[name="reason_delete_event"]').val();
              }
              rpc.query({
                model: "meeting.schedule",
                method: "delete_meeting",
                args: [selectedValue, reason_delete, id, type_view],
              }).then(function (result) {
                console.log(result.message)
                  try {
                      Dialog.alert("sss")
                  } catch (e){
                      doIt()
                  }
              }).catch(function (error) {
                console.error('RPC call failed:', error);
              });
            }
          },
          {
            text: _t("Cancel"),
            close: true,
          },
        ],
      });

      dialog.open(); // Open the dialog

      // Add the event listener to toggle the textarea display
      dialog.opened().then(function() {
          var othersRadio = dialog.$('input[name="reason"][value="others"]');
          var reasonTextarea = dialog.$('#reason_textarea');
          dialog.$('input[name="reason"]').on('change', function () {
              if (othersRadio.is(':checked')) {
                  reasonTextarea.show();
              } else {
                  reasonTextarea.hide();
              }
          });
      });
    },
  });

  // Custom Form View
  const CustomFormView = FormView.extend({
    config: _.extend({}, FormView.prototype.config, {
      Controller: CustomFormController,
    }),
  });

  // Register the custom view
  viewRegistry.add('custom_form_view', CustomFormView);
});
