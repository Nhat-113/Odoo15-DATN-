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
      model: 'ir.model.data',
      method: 'search_read',
      args: [
        [['module', '=', 'booking_room'], ['name', 'in', template_ids]],
        ['name']
      ]
    }).then(function (result) {
      return result.map(record => record.name);
    });
  }
  // Custom Form Controller
  const CustomFormController = FormController.extend({

    saveRecord: function (recordID, options) {
      var self = this;
      const template_ids = [
        'template_sendmail',
        'template_sendmail_add_attendens',
        'template_sendmail_delete_attendens',
        'template_send_mail_delete',
        'template_sendmail_edit_event'
      ];

      // Check if the mail templates exist
    checkMailTemplateExists(template_ids).then(function (existingTemplates) {
      let check_mail_template = [];
      if (!existingTemplates.includes("template_sendmail")) {
        check_mail_template.push("template_sendmail")
      }

      if (!existingTemplates.includes("template_sendmail_add_attendens")) {
        check_mail_template.push("template_sendmail_add_attendens")
      }

      if (!existingTemplates.includes("template_sendmail_delete_attendens")) {
        check_mail_template.push("template_sendmail_delete_attendens")
      }

      if (!existingTemplates.includes("template_send_mail_delete")) {
        check_mail_template.push("template_send_mail_delete")
      }

      if (!existingTemplates.includes("template_sendmail_edit_event")) {
        check_mail_template.push("template_sendmail_edit_event")
      }
      if (check_mail_template.length !== 0) {
        self.do_action({
          type: 'ir.actions.client',
          tag: 'display_notification',
          params: {
            title: "Waring",
            message: "The following templates don't exist:\n" + check_mail_template.join("\n"),
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
