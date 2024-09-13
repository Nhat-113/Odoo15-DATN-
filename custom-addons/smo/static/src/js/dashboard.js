odoo.define('smo.dashboard', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');
    const rpc = require('web.rpc');
    var Dialog = require("web.Dialog");
    var _t = core._t;

    const DashboardAction = AbstractAction.extend({
        start: function () {
            this._super.apply(this, arguments);
            this.removeControlPanel();
            this.getDashboardUrl().then(url => {
                if (url) {
                    this.renderDashboard(url); 
                } else {
                    var dialog = new Dialog(this, {
                      title: _t("Dashboard Wiget URL not set."),
                      size: "medium",
                      $content: $("<div>").append(
                        `<p>Dashboard Wiget URL not set! Do you want to configure it?</p>
                          <div></div>`
                      ),
                      buttons: [
                        {
                          text: _t("OK"),
                          classes: "btn btn-primary",
                          click: () => {
                            this.redirectToConfigSettings();
                          },
                        },
                      ],
                    });
                    dialog.open();
                }
            });
        },

        removeControlPanel: function () {
            const controlPanel = this.$el.closest('.o_control_panel');
            if (controlPanel.length) {
                controlPanel.remove();
            }
        },

        getDashboardUrl: function () {
            return rpc.query({
                model: 'ir.config_parameter',
                method: 'get_param',
                args: ['smo.dashboard_wiget'],
            }).then(result => result);
        },
        
        renderDashboard: function (url) {
            const self = this;
            const iframe = `<iframe src="${url}" style="width: 100%; height: 100vh;" frameborder="0"></iframe>`;
            self.$el.html(iframe);
            setInterval(function () {
                self.$el.html(iframe);
            }, 60000);
        },

        checkIframeStatus: function (iframe) {
            if (iframe.contentWindow.document.readyState === 'complete') {
                const status = iframe.contentWindow.document.querySelector('html').getAttribute('data-status');
                if (status === '502') {
                    self.$el.html('<p>Not found data. Please check url ThingsBoard!.</p>');
                }
            }
        },
        
        redirectToConfigSettings: function () {
            const url = '/web#cids=1&menu_id=4&action=89&model=res.config.settings&view_type=form';
            window.location.replace(url);
        },
    });

    core.action_registry.add('dashboard_action', DashboardAction);
});