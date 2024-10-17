odoo.define('smo.dashboard', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');
    const rpc = require('web.rpc');
    const Dialog = require("web.Dialog");
    const _t = core._t;
    
    const DashboardAction = AbstractAction.extend({
        start: function () {
            this._super.apply(this, arguments);
            this.getDashboardData().then(result => {
                if (result && result[1]) { 
                    this.renderDashboard(result); 
                } else {
                    const dialog = new Dialog(this, {
                        title: _t("Dashboard Widget."),
                        size: "medium",
                        $content: $("<div>").append(
                            `<p>Dashboard Widget URL not set!</p>
                             <div></div>`
                        ),
                        buttons: [
                            {
                                text: _t("OK"),
                                classes: "btn btn-primary",
                                click: () => {
                                    this.redirectToConfigSettings();
                                    dialog.close(); 
                                },
                            },
                        ],
                    });
                    $(document).on('click', '.close', () => {
                        this.redirectToConfigSettings();
                        dialog.close();
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
    
        getDashboardData: function () {
            return rpc.query({
                model: 'smo.device',
                method: 'get_dashboard_widget',
                args: [],
            }).then(result => result);
        },
        
        renderDashboard: function (result) {
            const self = this;
            const dashboardWidgetUrl = result[1]; 
            const iframe = `<iframe src="${dashboardWidgetUrl}" style="width: 100%; height: 100vh;" frameborder="0"></iframe>`;
            
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
            this.getDashboardData().then(result => {
                const cids = result[0]; 
                const action_id = result[2];
                const url = `/web#cids=${cids}&action=${action_id}&model=smo.device&view_type=list`;
                window.location.replace(url);
            });
        },
    });
    
    core.action_registry.add('dashboard_action', DashboardAction);
});