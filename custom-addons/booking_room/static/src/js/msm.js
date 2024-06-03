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

  var BookingCalendarController = CalendarController.extend({
    /**
     * @override
     */
    _onOpenCreate: function (event) {
      var self = this;
      const mode = this.mode;
      if (["year", "month"].includes(this.model.get().scale)) {
        event.data.allDay = true;
      }
      var data = this.model.calendarEventToRecord(event.data);
      var context = _.extend(
        {},
        this.context,
        event.options && event.options.context
      );
      if (data.name) {
        context.default_name = data.name;
      }
      if (mode === "month" || mode === "year") {
        let current_time = new Date();

        let startTime = default_start_minutes();
        var newStartDate = moment(data[this.mapping.date_start])
          .hour(startTime.current_hour)
          .minute(startTime.current_minute);
        if (current_time.getDay > 7) {
          newStartDate = newStartDate.subtract(1, "day");
        }
        var formattedStartDate = newStartDate.format("YYYY-MM-DD HH:mm:ss");
        context["default_" + this.mapping.date_start] =
          formattedStartDate || null;

        let endTime = default_end_minutes();
        var newEndDate = moment(data[this.mapping.date_stop])
          .hour(endTime.current_hour)
          .minute(endTime.current_minute);
        if (current_time.getDay > 7) {
          newEndDate = newEndDate.subtract(1, "day");
        }
        var formattedDateStop = newEndDate.format("YYYY-MM-DD HH:mm:ss");
        context["default_" + this.mapping.date_stop] = formattedDateStop;
      } else {
        context["default_" + this.mapping.date_start] =
          data[this.mapping.date_start] || null;
        if (this.mapping.date_stop) {
          context["default_" + this.mapping.date_stop] =
            data[this.mapping.date_stop] || null;
        }
      }
      if (this.mapping.date_delay) {
        context["default_" + this.mapping.date_delay] =
          data[this.mapping.date_delay] || null;
      }
      if (this.mapping.all_day) {
        context["default_" + this.mapping.all_day] =
          data[this.mapping.all_day] || null;
      }
      for (var k in context) {
        if (context[k] && context[k]._isAMomentObject) {
          context[k] = dateToServer(context[k]);
        }
      }
      var options = _.extend({}, this.options, event.options, {
        context: context,
        title: this._setEventTitle(),
      });
      if (this.quick != null) {
        this.quick.destroy();
        this.quick = null;
      }
      if (
        !options.disableQuickCreate &&
        !event.data.disableQuickCreate &&
        this.quickAddPop
      ) {
        this.quick = new QuickCreate(this, true, options, data, event.data);
        this.quick.open();
        this.quick.opened(function () {
          self.quick.focus();
        });
        return;
      }
      if (this.eventOpenPopup) {
        if (this.previousOpen) {
          this.previousOpen.close();
        }
        this.previousOpen = new dialogs.FormViewDialog(self, {
          res_model: this.modelName,
          context: context,
          title: options.title,
          view_id: this.formViewId || false,
          disable_multiple_selection: true,
          on_saved: function () {
            if (event.data.on_save) {
              event.data.on_save();
            }
            self.reload();
          },
        });
        this.previousOpen.on("closed", this, () => {
          if (event.data.on_close) {
            event.data.on_close();
          }
        });
        this.previousOpen.open();
      } else {
        this.do_action({
          type: "ir.actions.act_window",
          res_model: this.modelName,
          views: [[this.formViewId || false, "form"]],
          target: "current",
          context: context,
        });
      }
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

      const buttons = [];
      rpc
        .query({
          model: "meeting.schedule",
          method: "get_booking_detail",
          args: [id],
        })
        .then((result) => {
          const date = new Date();
          const start_date = new Date(result.start_date);
          if (
            result.is_hr === false &&
            (result.user_id !== session.uid || start_date < date)
          ) {
            buttons.push({
              text: _t("Cancel"),
              class: "btn-secondary o_form_button_cancel",
              close: true,
            });
          }

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
            buttons: buttons.length > 0 ? buttons : undefined,
          };
          if (self.formViewId) {
            options.view_id = parseInt(self.formViewId);
          }
          new dialogs.FormViewDialog(self, options).open();
        })
        .catch(function (error) {
          console.log(error);
        });
    },
    _setEventTitle: function () {
      return _t("Booking Form");
    },
    _onDeleteRecord: function (ev) {
      var self = this;

      var id = ev.data.event.record.id;
      var type_view = "calendar_view"

      var dialog = new Dialog(this, {
        title: _t("Delete Confirmation"),
        size: "medium",
        $content: $(QWeb.render("booking_room.RecurrentEventUpdate", {})),
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
              rpc
                .query({
                  model: "meeting.schedule",
                  method: "delete_meeting",
                  args: [selectedValue, reason_delete, id, type_view],
                })
                .then(function (result) {
                  self.reload();
                })
                .catch(function (error) {
                  Dialog.alert(this, error.message.data.message);
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
          if (result.is_hr === false && record.user_id[0] !== session.uid) {
            calendarPopover._canDelete = false;
            calendarPopover.isEventEditable = function () {
              return false;
            };
          }

          if (partner_id && record.user_id[0] !== session.uid) {
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

      if (title_room.length > 30) {
        truncated_title_room = title_room.substring(0, 30) + "…";
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