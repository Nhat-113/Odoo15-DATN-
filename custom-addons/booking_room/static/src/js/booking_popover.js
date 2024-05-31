odoo.define("booking.CalendarPopover", function (require) {
  "use strict";

  var CalendarPopover = require("web.CalendarPopover");

  var BookingCalendarPopover = CalendarPopover.extend({
    template: "booking_room.popover",
    isEventViewable() {
        return false;
    },
  });

  return BookingCalendarPopover
});
