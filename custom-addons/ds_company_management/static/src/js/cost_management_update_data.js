odoo.define('cost_management.upgrade_data', function(require) {
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
            });

            self.$buttons.on("click", ".upgrade_salary_cost_support", function() {
                self._rpc({
                    model: 'compare.salary.cost.data',
                    method: 'upgrade_salary_cost_support'
                }).then(() => {
                    self.messageNotify();
                    setTimeout(function (){
                        return location.reload();
                    }, 500);
                })
            }),

            self.$buttons.on("click", ".upgrade_project_booking_support", function() {
                self._rpc({
                    model: 'project.planning.booking.data',
                    method: 'upgrade_project_booking_support'
                }).then(() => {
                    self.messageNotify();
                    setTimeout(function (){
                        return location.reload();
                    }, 500);
                })
            }),

            self.$buttons.on("click", ".upgrade_compare_payslip_contract_support", function() {
                self._rpc({
                    model: 'compare.payslip.contract.data',
                    method: 'upgrade_compare_payslip_contract_support'
                }).then(() => {
                    self.messageNotify();
                    setTimeout(function (){
                        return location.reload();
                    }, 500);
                })
            }),

            self.$buttons.on("click", ".upgrade_booking_resource_month_support", function() {
                self._rpc({
                    model: 'booking.resource.month.data',
                    method: 'upgrade_booking_resource_month_support'
                }).then(() => {
                    self.messageNotify();
                    setTimeout(function (){
                        return location.reload();
                    }, 500);
                })
            }),

            self.$buttons.on("click", ".upgrade_compare_salary_booking_available_support", function() {
                self._rpc({
                    model: 'compare.salary.booking.available.data',
                    method: 'upgrade_compare_salary_booking_available_support'
                }).then(() => {
                    self.messageNotify();
                    setTimeout(function (){
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