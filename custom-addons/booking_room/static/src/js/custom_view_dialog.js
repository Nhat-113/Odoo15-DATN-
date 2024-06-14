odoo.define("booking_room.CustomViewDialogs", function (require) {
  "use strict";
  var dialogs = require("web.view_dialogs");
  var core = require("web.core");
  var rpc = require("web.rpc");
  var Dialog = require("web.Dialog");
  var _t = core._t;
  var QWeb = core.qweb;

  const CustomFormViewDialog = dialogs.FormViewDialog.extend({
    init: function (parent, options) {
      var self = this;
      options = options || {};

      this.res_id = options.res_id || null;
      this.on_saved = options.on_saved || function () {};
      this.on_remove = options.on_remove || function () {};
      this.context = options.context;
      this._createContext = options._createContext;
      this.model = options.model;
      this.parentID = options.parentID;
      this.recordID = options.recordID;
      this.shouldSaveLocally = options.shouldSaveLocally;
      this.readonly = options.readonly;
      this.deletable = options.deletable;
      this.editable = options.editable;
      this.disable_multiple_selection = options.disable_multiple_selection;
      var oBtnRemove = "o_btn_remove";

      var multi_select =
        !_.isNumber(options.res_id) && !options.disable_multiple_selection;
      var readonly = _.isNumber(options.res_id) && options.readonly;

      if (!options.buttons) {
        options.buttons = [
          {
            text:
              options.close_text || (readonly ? _t("Close") : _t("Discard")),
            classes: "btn-secondary o_form_button_cancel",
            close: true,
            click: function () {
              if (!readonly) {
                self.form_view.model.discardChanges(self.form_view.handle, {
                  rollback: self.shouldSaveLocally,
                });
              }
            },
          },
        ];

        if (!readonly) {
          options.buttons.unshift({
            text:
              options.save_text ||
              (multi_select ? _t("Save & Close") : _t("Save")),
            classes: "btn-primary",
            click: function () {
              self._save(options.event).then(self.close.bind(self));
            },
          });

          if (multi_select) {
            options.buttons.splice(1, 0, {
              text: _t("Save & New"),
              classes: "btn-primary",
              click: function () {
                self
                  ._save()
                  .then(function () {
                    // reset default name field from context when Save & New is clicked, pass additional
                    // context so that when getContext is called additional context resets it
                    const additionalContext =
                      self._createContext && self._createContext(false);
                    self.form_view.createRecord(
                      self.parentID,
                      additionalContext
                    );
                  })
                  .then(function () {
                    if (!self.deletable) {
                      return;
                    }
                    self.deletable = false;
                    self.buttons = self.buttons.filter(function (button) {
                      return button.classes.split(" ").indexOf(oBtnRemove) < 0;
                    });
                    self.set_buttons(self.buttons);
                    self.set_title(
                      _t("Create ") + _.str.strRight(self.title, _t("Open: "))
                    );
                  });
              },
            });
          }

          var multi = options.disable_multiple_selection;
          if (!multi && this.deletable) {
            this._setRemoveButtonOption(options, oBtnRemove);
          }
        }
      }
      this._super(parent, options);
    },
    /**
     * Show a warning message if the user modified a translated field.  For each
     * field, the notification provides a link to edit the field's translations.
     *
     * @override
     */
    _save: function (event) {
      var self = this;
      var data = this.form_view.renderer.state.data;
      const old_start_date = new Date(event.start_date);
      const old_end_date = new Date(event.end_date);

      const formatDate = (dateStr) => {
        let date = new Date(
          dateStr.toLocaleString("en-US", { timeZone: "UTC" })
        );
        let year = date.getFullYear();
        let month = String(date.getMonth() + 1).padStart(2, "0");
        let day = String(date.getDate()).padStart(2, "0");
        let hours = String(date.getHours()).padStart(2, "0");
        let minutes = String(date.getMinutes()).padStart(2, "0");
        let seconds = String(date.getSeconds()).padStart(2, "0");

        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
      };

      function openDialog() {
        return new Promise(function (resolve, reject) {
          var dialog = new Dialog(self, {
            title: _t("Edit recurring meeting"),
            size: "medium",
            $content: $(QWeb.render("booking_room.edit_recurrent_event", {})),
            buttons: [
              {
                text: _t("Confirm"),
                classes: "btn btn-primary",
                close: true,
                click: function () {
                  var selected_value = $(
                    'input[name="edit-option"]:checked'
                  ).val();
                  rpc
                    .query({
                      model: "meeting.schedule",
                      method: "write_many",
                      args: [
                        data,
                        formatDate(old_start_date),
                        selected_value,
                      ],
                    })
                    .then(function () {
                      resolve(true); 
                    })
                    .catch(function (error) {
                      Dialog.alert(this, error.message.data.message);
                      reject(error);
                    });
                },
              },
              {
                text: _t("Cancel"),
                close: true,
                click: function () {
                  // resolve(false);
                },
              },
            ],
          });
          dialog.open();
        });
      }

      if (data.meeting_type !== "normal") {
        return openDialog()
          .then(function (confirmed) {
            if (confirmed) {
              return self.on_saved({}, !![].length);
            } else {
              return Promise.resolve();
            }
          })
          .catch(function (error) {
            return Promise.reject(error);
          });
      } else {
        return this.form_view
          .saveRecord(this.form_view.handle, {
            stayInEdit: true,
            reload: false,
            savePoint: this.shouldSaveLocally,
            viewType: "form",
          })
          .then(function (changedFields) {
            // record might have been changed by the save (e.g. if this was a new record, it has an
            // id now), so don't re-use the copy obtained before the save
            var record = self.form_view.model.get(self.form_view.handle);
            return self.on_saved(record, !!changedFields.length);
          });
      }
    },
  });

  return { CustomFormViewDialog: CustomFormViewDialog };
});
