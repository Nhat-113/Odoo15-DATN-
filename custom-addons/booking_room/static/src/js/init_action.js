/** @odoo-module **/
import { query } from "web.rpc";
var Dialog = require("web.Dialog");
var core = require("web.core");
var _t = core._t;

const checkBookingModel = () => {
  var params = Object.fromEntries(
    window.location.hash
      .substring(1)
      .split("&")
      .map((param) => param.split("=").map(decodeURIComponent))
  );
  return params?.model === "meeting.schedule";
};

export function handleBookingTimezone() {
  if (checkBookingModel()) {
    query({
      model: "meeting.schedule",
      method: "get_current_user",
      args: [],
    })
      .then(function (result) {
        const local_tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const date = new Date();
        const offset = -(date.getTimezoneOffset() / 60);
        if (offset !== result.tz_offset) {
          var dialog = new Dialog(self, {
            title: _t("Timezone Difference"),
            size: "medium",
            $content: $("<div>").append(
              `<p>Do you want to change the System Server's timezone to match your PC's timezone?</p>
                <p>System Server: ${result.user_tz}</p>
                <div></div>
                <p>Your PC: ${local_tz}</p>`
            ),
            buttons: [
              {
                text: _t("OK"),
                classes: "btn btn-primary",
                click: function () {
                  query({
                    model: "meeting.schedule",
                    method: "set_user_tz",
                    args: [local_tz],
                  }).then(function (result) {
                    window.location.reload();
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
        }
      })
      .catch(function (error) {
        console.log(error);
      });
  }
}

window.addEventListener('load', function() {
    handleBookingTimezone()
});