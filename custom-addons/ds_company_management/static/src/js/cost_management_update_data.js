odoo.define('cost_manamgenet.upgrade_data', function(require) {
    "use strict";
    var ListController = require('web.ListController');
    var core = require('web.core');
    var _t = core._t;
    var actionUpgradeData = {
        renderButtons: function() {
            this._super.apply(this, arguments);
            var self = this;
            self.$buttons.on("click", ".upgrade_data-button", function() {
                self._rpc({
                    model: 'cost.management.upgrade.action',
                    method: 'cost_management_reset_update_data'
                }).then(() => {
                    self.messageNotify();
                    setTimeout(function() { 
                        return location.reload();
                    }, 500);
                    
                })
            })
        },
        messageNotify: function() {
            return this.displayNotification({
                title: _t("Success"),
                message: _t("Upgrade Data Successfully!"),
                type: 'success'
            });
        }
    }

    ListController.include(actionUpgradeData);
});