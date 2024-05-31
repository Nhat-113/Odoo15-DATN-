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
      _onDeleteRecord: function (ev) {
          var self = this;
          var id = ev.model.loadParams.res_id;
          var type_v = "form_view";
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
                          var reason_delete = $('textarea[name="reason_delete_event"]').val();
                          rpc.query({
                              model: "meeting.schedule",
                              method: "delete_meeting",
                              args: [selectedValue, reason_delete, id, type_v],
                          }).then(function (result) {
                              if (result.status === 'success') {
                                  self.do_action({
                                      type: 'ir.actions.act_window',
                                      res_model: 'meeting.schedule',
                                      res_id: result.view_id,
                                      views: [[false, 'list']],
                                      target: 'current'
                                  });
                              } else {
                                  Dialog.alert(self, result.message);
                              }
                          }).catch(function (error) {
                              Dialog.alert(self, error.message.data.message);
                          });
                      }
                  },
                  {
                      text: _t("Cancel"),
                      close: true,
                  },
              ],
          });
          dialog.open();
      },
  });

  // Custom Form View
  const CustomFormView = FormView.extend({
      config: _.extend({}, FormView.prototype.config, {
          Controller: CustomFormController,
      }),
  });

  // Register the custom views
  viewRegistry.add('custom_form_view', CustomFormView);
});
