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

  // Function to check if mail templates exist
  function checkMailTemplateExists(template_ids) {
    return rpc.query({
        model: 'meeting.schedule',
        method: 'check_mail_template_exists',
        args: [template_ids]
    }).then(function (result) {
        return result;
    });
  }
  // Custom Form Controller
  const CustomFormController = FormController.extend({

    saveRecord: function (recordID, options) {
      var self = this;
      const template_ids = [
        'template_send_mail',
        'template_send_mail_add_attendens',
        'template_send_mail_edit_attendens',
        'template_send_mail_delete',
        'template_send_mail_edit_event'
      ];

      // Check if the mail templates exist
    checkMailTemplateExists(template_ids).then(function (existingTemplates) {
      let missingTemplates = [];

      template_ids.forEach(function(template_id) {
          if (!existingTemplates.includes(template_id)) {
              missingTemplates.push(template_id);
          }
      });
      if (missingTemplates.length !== 0) {
        self.do_action({
          type: 'ir.actions.client',
          tag: 'display_notification',
          params: {
            title: "Warning",
            message: "There is a problem with the email template, so emails cannot be sent to attendees. Please contact the administrator to fix it",
            type: "danger",
            sticky: false,
          },
        });
      }
    })
      var unlockedMutex = this.mutex.getUnlockedDef()
          .then(function () {
              return self.renderer.commitChanges(recordID || self.handle);
          })
          .then(function () {
              return self.mutex.exec(self._saveRecord.bind(self, recordID, options));
          });
      this.savingDef = new Promise(function (resolve) {
          unlockedMutex.then(resolve).guardedCatch(resolve);
      });

      return unlockedMutex;
  },
      
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
            close: false,
            click: function () {
              var selectedValue = $('input[name="recurrence-update"]:checked').val();
              var reason_delete = $('input[name="reason"]:checked').val();
              if (reason_delete == "others"){
                reason_delete = $('textarea[name="reason_delete_event"]').val();
                if (!reason_delete.trim()) {
                  dialog.$('#warning_message').show();
                  return;
                }
              }
              dialog.$('#warning_message').hide();
              rpc.query({
                model: "meeting.schedule",
                method: "delete_meeting",
                args: [selectedValue, reason_delete, id, type_view],
              }).then(function () {
                  dialog.close();
                  doIt();
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
                  dialog.$('#warning_message').hide(); 
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
