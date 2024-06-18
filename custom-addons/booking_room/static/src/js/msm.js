odoo.define("booking_room.schedule_view_calendar", function (require) {
  "use strict";
  var core = require("web.core");
  var Dialog = require("web.Dialog");
  var dialogs = require("web.view_dialogs");
  var rpc = require("web.rpc");
  var QWeb = core.qweb;
  var CalendarController = require("web.CalendarController");
  var CalendarRenderer = require("web.CalendarRenderer");
  var CalendarModel = require("web.CalendarModel");
  var CalendarView = require("web.CalendarView");
  var BookingCalendarPopover = require("booking.CalendarPopover");
  var CustomViewDialogs = require("booking_room.CustomViewDialogs");
  var viewRegistry = require("web.view_registry");
  var session = require("web.session");
  const { createYearCalendarView } = require("booking_room.fullcalendar");
  var _t = core._t;

  function dateToServer(date) {
    return date.clone().utc().locale("en").format("YYYY-MM-DD HH:mm:ss");
  }

  function default_start_minutes() {
    let current_time = new Date();
    let current_hour = current_time.getUTCHours();
    let current_minute = Math.ceil(current_time.getMinutes() / 15 + 1) * 15;

    return { current_hour, current_minute };
  }

  function default_end_minutes() {
    let current_time = new Date();
    let current_hour = current_time.getUTCHours();
    let current_minute =
      Math.ceil(current_time.getMinutes() / 15 + 1) * 15 + 30;

    return { current_hour, current_minute };
  }

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
  const formatDate = (dateStr) => {
    let date = new Date(dateStr.toLocaleString("en-US", { timeZone: "UTC" }));
    let year = date.getFullYear();
    let month = String(date.getMonth() + 1).padStart(2, "0");
    let day = String(date.getDate()).padStart(2, "0");
    let hours = String(date.getHours()).padStart(2, "0");
    let minutes = String(date.getMinutes()).padStart(2, "0");
    let seconds = String(date.getSeconds()).padStart(2, "0");
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  };

  var BookingCalendarController = CalendarController.extend({
    /**
     * @override
     */
    _onOpenCreate: function (event) {
      var self = this;
      const mode = this.mode;

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

        // Continue with the original functionality after checking the templates
        if (["year", "month"].includes(self.model.get().scale)) {
          event.data.allDay = true;
        }
        var data = self.model.calendarEventToRecord(event.data);
        var context = _.extend(
          {},
          self.context,
          event.options && event.options.context
        );
        if (data.name) {
          context.default_name = data.name;
        }
        if (mode === "month" || mode === "year") {
          let current_time = new Date();

          let startTime = default_start_minutes();
          let endTime = default_end_minutes();

          if (startTime.current_hour >= 15 && startTime.current_minute >= 45) {
            var newStartDate = moment(data[self.mapping.date_start])
              .hour(17)
              .minute(0)
              .add(1, 'day'); 
            var newEndDate = moment(data[self.mapping.date_stop])
              .hour(17)
              .minute(30)
              .add(1, 'day'); 
          } else {
            var newStartDate = moment(data[self.mapping.date_start])
              .hour(startTime.current_hour)
              .minute(startTime.current_minute);

            var newEndDate = moment(data[self.mapping.date_stop])
              .hour(endTime.current_hour)
              .minute(endTime.current_minute);
          }
          var formattedStartDate = newStartDate.format("YYYY-MM-DD HH:mm:ss");
          context["default_" + self.mapping.date_start] =
            formattedStartDate || null;
          var formattedDateStop = newEndDate.format("YYYY-MM-DD HH:mm:ss");
          context["default_" + self.mapping.date_stop] = formattedDateStop;
        } else {
          context["default_" + self.mapping.date_start] =
            data[self.mapping.date_start] || null;
          if (self.mapping.date_stop) {
            context["default_" + self.mapping.date_stop] =
              data[self.mapping.date_stop] || null;
          }
        }
        if (self.mapping.date_delay) {
          context["default_" + self.mapping.date_delay] =
            data[self.mapping.date_delay] || null;
        }
        if (self.mapping.all_day) {
          context["default_" + self.mapping.all_day] =
            data[self.mapping.all_day] || null;
        }
        for (var k in context) {
          if (context[k] && context[k]._isAMomentObject) {
            context[k] = dateToServer(context[k]);
          }
        }
        var options = _.extend({}, self.options, event.options, {
          context: context,
          title: self._setEventTitle(),
        });
        if (self.quick != null) {
          self.quick.destroy();
          self.quick = null;
        }
        if (
          !options.disableQuickCreate &&
          !event.data.disableQuickCreate &&
          self.quickAddPop
        ) {
          self.quick = new QuickCreate(self, true, options, data, event.data);
          self.quick.open();
          self.quick.opened(function () {
            self.quick.focus();
          });
          return;
        }
        if (self.eventOpenPopup) {
          if (self.previousOpen) {
            self.previousOpen.close();
          }
          self.previousOpen = new dialogs.FormViewDialog(self, {
            res_model: self.modelName,
            context: context,
            title: options.title,
            view_id: self.formViewId || false,
            disable_multiple_selection: true,
            on_saved: function () {
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
              if (event.data.on_save) {
                event.data.on_save();
              }
              self.reload();
            },
          });
          self.previousOpen.on("closed", self, () => {
            if (event.data.on_close) {
              event.data.on_close();
            }
          });
          self.previousOpen.open();
        } else {
          self.do_action({
            type: "ir.actions.act_window",
            res_model: self.modelName,
            views: [[self.formViewId || false, "form"]],
            target: "current",
            context: context,
          });
        }
      });
    },
    _onOpenEvent: function (event) {
      var self = this;
      var id = event.data._id;
      id = id && parseInt(id).toString() === id ? parseInt(id) : id;

      if (!this.eventOpenPopup) {
        this._rpc({
          model: self.modelName,
          method: "get_formview_id",
          //The event can be called by a view that can have another context than the default one.
          args: [[id]],
          context: event.context || self.context,
        }).then(function (viewId) {
          self.do_action({
            type: "ir.actions.act_window",
            res_id: id,
            res_model: self.modelName,
            views: [[viewId || false, "form"]],
            target: "current",
            context: event.context || self.context,
          });
        });
        return;
      }

      rpc
        .query({
          model: "meeting.schedule",
          method: "get_booking_detail",
          args: [id],
        })
        .then((result) => {
          const date = new Date();
          const start_date = new Date(result.start_date);
          const isReadOnly =
            result.is_hr === false &&
            (result.user_id !== session.uid || start_date < date);
          // re-check -------------------------------------

          var options = {
            res_model: self.modelName,
            res_id: id || null,
            context: event.context || self.context,
            title: event.data.title
              ? _.str.sprintf(_t("Open: %s"), event.data.title)
              : "Booking Detail",
            on_saved: function () {
              if (event.data.on_save) {
                event.data.on_save();
              }
              self.reload();
            },
            close_text: "Cancel",
            readonly: isReadOnly ? true : false,
            event: result,
          };
          if (self.formViewId) {
            options.view_id = parseInt(self.formViewId);
          }
          new CustomViewDialogs.CustomFormViewDialog(self, options).open();
        })
        .catch(function (error) {
          console.log(error);
        });
    },

    _onDropRecord: function (event) {
      const self = this;
      function openDialog() {
        return new Promise(function (resolve, reject) {
          var dialog = new Dialog(self, {
            title: _t("Edit recurring meeting"),
            size: "medium",
            $content: $(QWeb.render("booking_room.edit_recurrent_event", {})),
            onForceClose: function () {
              self.reload();
            },
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
                        event.data.record,
                        formatDate(event.data.start._i),
                        selected_value,
                        "drag",
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
                  resolve(false);
                },
              },
            ],
          });
          dialog.open();
        });
      }

      if (event.data.record.meeting_type !== "normal") {
        return openDialog()
          .then(function (confirmed) {
            if (confirmed) {
              self.reload();
            } else {
              self.reload();
            }
          })
          .catch(function (error) {
            self.reload();
            return Promise.reject(error);
          });
      } else {
        this._updateRecord(
          _.extend({}, event.data, {
            drop: true,
          })
        );
      }
    },
    _setEventTitle: function () {
      return _t("Booking Form");
    },
    _onDeleteRecord: function (ev) {
      var self = this;
    
      var id = ev.data.event.record.id;
      var type_view = "calendar_view";
    
      var dialog = new Dialog(this, {
        title: _t("Delete Confirmation"),
        size: "medium",
        $content: $(QWeb.render("booking_room.RecurrentEventUpdate", {})),
        buttons: [
          {
            text: _t("OK"),
            classes: "btn btn-primary",
            close: false,
            click: function () {
              var selectedValue = $('input[name="recurrence-update"]:checked').val();
              var reason_delete = $('input[name="reason"]:checked').val();
              if (reason_delete == "others") {
                reason_delete = $('textarea[name="reason_delete_event"]').val();
                if (!reason_delete.trim()) {
                  dialog.$('#warning_message').show();
                  return;
                }
              }
              dialog.$('#warning_message').hide();
              rpc
                .query({
                  model: "meeting.schedule",
                  method: "delete_meeting",
                  args: [selectedValue, reason_delete, id, type_view],
                })
                .then(function (result) {
                  dialog.close();
                  self.reload();
                })
                .catch(function (error) {
                  Dialog.alert(self, error.message.data.message);
                });
            },
          },
          {
            text: _t("Cancel"),
            close: true,
          },
        ],
      });
      dialog.open();
      dialog.o;
      dialog.open(); // Open the dialog

      // Add the event listener to toggle the textarea display
      dialog.opened().then(function() {
          var othersRadio = dialog.$('input[name="reason"][value="others"]');
          var reasonTextarea = dialog.$('#reason_textarea');
          var reasonInput = dialog.$('#w3review');
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

  var BookingPopoverRenderer = CalendarRenderer.extend({
    config: {
      CalendarPopover: BookingCalendarPopover,
      eventTemplate: "calendar-box",
    },

    _getFullCalendarOptions: function (fcOptions) {
      var self = this;
      const options = Object.assign(
        {},
        this.state.fc_options,
        {
          plugins: ["moment", "interaction", "dayGrid", "timeGrid"],
          eventDrop: function (eventDropInfo) {
            var event = self._convertEventToFC3Event(eventDropInfo.event);
            self.trigger_up("dropRecord", event);
          },
          eventResize: function (eventResizeInfo) {
            self._unselectEvent();
            var event = self._convertEventToFC3Event(eventResizeInfo.event);
            self.trigger_up("updateRecord", event);
          },
          eventClick: function (eventClickInfo) {
            eventClickInfo.jsEvent.preventDefault();
            eventClickInfo.jsEvent.stopPropagation();
            var eventData = eventClickInfo.event;
            self._unselectEvent();
            $(self.calendarElement)
              .find(self._computeEventSelector(eventClickInfo))
              .addClass("o_cw_custom_highlight");
            self._renderEventPopover(eventData, $(eventClickInfo.el));
          },
          selectAllow: function (event) {
            if (event.end.getDate() === event.start.getDate() || event.allDay) {
              return true;
            }
          },
          yearDateClick: function (info) {
            self._unselectEvent();
            info.view.unselect();
            if (!info.events.length) {
              if (info.selectable) {
                const data = {
                  start: info.date,
                  allDay: true,
                };
                if (self.state.context.default_name) {
                  data.title = self.state.context.default_name;
                }
                self.trigger_up(
                  "openCreate",
                  self._convertEventToFC3Event(data)
                );
              }
            } else {
              self._renderYearEventPopover(
                info.date,
                info.events,
                $(info.dayEl)
              );
            }
          },
          select: function (selectionInfo) {
            var data = {
              start: selectionInfo.start,
              end: selectionInfo.end,
              allDay: selectionInfo.allDay,
            };
            self._preOpenCreate(data);
          },
          eventRender: function (info) {
            var event = info.event;
            var element = $(info.el);
            var view = info.view;
            self._addEventAttributes(element, event);
            if (view.type === "dayGridYear") {
              const color = this.getColor(event.extendedProps.color_index);
              if (typeof color === "string") {
                element.css({
                  backgroundColor: color,
                });
              } else if (typeof color === "number") {
                element.addClass(`o_calendar_color_${color}`);
              } else {
                element.addClass("o_calendar_color_1");
              }
            } else {
              var $render = $(self._eventRender(event));
              element.find(".fc-content").html($render.html());
              element.addClass($render.attr("class"));

              // Add background if doesn't exist
              if (!element.find(".fc-bg").length) {
                element
                  .find(".fc-content")
                  .after($("<div/>", { class: "fc-bg" }));
              }

              if (view.type === "dayGridMonth" && event.extendedProps.record) {
                var start = event.extendedProps.r_start || event.start;
                var end = event.extendedProps.r_end || event.end;
                $(this.el)
                  .find(
                    _.str.sprintf(
                      '.fc-day[data-date="%s"]',
                      moment(start).format("YYYY-MM-DD")
                    )
                  )
                  .addClass("fc-has-event");
                // Detect if the event occurs in just one day
                // note: add & remove 1 min to avoid issues with 00:00
                var isSameDayEvent = moment(start)
                  .clone()
                  .add(1, "minute")
                  .isSame(moment(end).clone().subtract(1, "minute"), "day");
                if (!event.extendedProps.record.allday && isSameDayEvent) {
                  // For month view: do not show background for non allday, single day events
                  element.addClass("o_cw_nobg");
                  if (event.extendedProps.showTime && !self.hideTime) {
                    const displayTime = moment(start)
                      .clone()
                      .format(self._getDbTimeFormat());
                    element.find(".fc-content .fc-time").text(displayTime);
                  }
                }
              }

              // On double click, edit the event
              element.on("dblclick", function () {
                self.trigger_up("edit_event", { id: event.id });
              });
            }
          },
          datesRender: function (info) {
            const viewToMode = Object.fromEntries(
              Object.entries(self.scalesInfo).map(([k, v]) => [v, k])
            );
            self.trigger_up("viewUpdated", {
              mode: viewToMode[info.view.type],
              title: info.view.title,
            });
          },
          // Add/Remove a class on hover to style multiple days events.
          // The css ":hover" selector can't be used because these events
          // are rendered using multiple elements.
          eventMouseEnter: function (mouseEnterInfo) {
            $(self.calendarElement)
              .find(self._computeEventSelector(mouseEnterInfo))
              .addClass("o_cw_custom_hover");
          },
          eventMouseLeave: function (mouseLeaveInfo) {
            if (!mouseLeaveInfo.event.id) {
              return;
            }
            $(self.calendarElement)
              .find(self._computeEventSelector(mouseLeaveInfo))
              .removeClass("o_cw_custom_hover");
          },
          eventDragStart: function (mouseDragInfo) {
            mouseDragInfo.el.classList.add(mouseDragInfo.view.type);
            $(self.calendarElement)
              .find(`[data-event-id=${mouseDragInfo.event.id}]`)
              .addClass("o_cw_custom_hover");
            self._unselectEvent();
          },
          eventResizeStart: function (mouseResizeInfo) {
            $(self.calendarElement)
              .find(`[data-event-id=${mouseResizeInfo.event.id}]`)
              .addClass("o_cw_custom_hover");
            self._unselectEvent();
          },
          eventLimitClick: function () {
            self._unselectEvent();
            return "popover";
          },
          windowResize: function () {
            self._onWindowResize();
          },
          views: {
            timeGridDay: {
              columnHeaderFormat: "LL",
            },
            timeGridWeek: {
              columnHeaderFormat: "ddd D",
            },
            dayGridMonth: {
              columnHeaderFormat: "dddd",
            },
            dayGridYear: {
              weekNumbers: false,
            },
          },
          height: "parent",
          unselectAuto: false,
          // prevent too small events
          timeGridEventMinHeight: 15,
          dir: _t.database.parameters.direction,
          events: (info, successCB) => {
            successCB(self.state.data);
          },
        },
        fcOptions
      );
      options.plugins.push(createYearCalendarView(FullCalendar, options));
      return options;
    },
  });

  var BookingCalendarRenderer = BookingPopoverRenderer.extend({
    /**
     * @override
     */
    _renderEventPopover: function (eventData, $eventElement) {
      var self = this;

      let calendarPopover = new self.config.CalendarPopover(
        self,
        self._getPopoverContext(eventData)
      );

      rpc
        .query({
          model: "meeting.schedule",
          method: "get_current_user",
          args: [],
        })
        .then(function (result) {
          const record = eventData._def.extendedProps.record;
          const date = new Date();
          const partner_id = record.partner_ids.find(
            (id) => id === result.employee_id
          );
          if (!result.is_hr && record.user_id[0] !== session.uid) {
            calendarPopover._canDelete = false;
            calendarPopover.isEventEditable = function () {
              return false;
            };
          }

          if (partner_id && record.user_id[0] !== session.uid && !result.is_hr) {
            calendarPopover.isEventViewable = function () {
              return true;
            };
          }
        })
        .catch(function (error) {
          console.log(error);
        })
        .finally(function () {
          calendarPopover.appendTo($("<div>")).then(() => {
            $eventElement
              .popover(self._getPopoverParams(eventData))
              .on("shown.bs.popover", function () {
                self._onPopoverShown($(this), calendarPopover);
              })
              .popover("show");
          });
        });
    },
    _getPopoverParams: function (eventData) {
      const params = this._super.apply(this, arguments);
      var title_room = eventData._def.extendedProps.record.room_id[1];
      var truncated_title_room = title_room;

      if (title_room.length > 25) {
        truncated_title_room = title_room.substring(0, 25) + "…";
      }

      params.title = `<span class="booking-room-title" data-full-title="${title_room}">${truncated_title_room}</span>`;
      return params;
    },
  });

  var BookingCalendarView = CalendarView.extend({
    config: _.extend({}, CalendarView.prototype.config, {
      Controller: BookingCalendarController,
      Renderer: BookingCalendarRenderer,
      Model: CalendarModel,
    }),
  });
  viewRegistry.add("msm", BookingCalendarView);
});