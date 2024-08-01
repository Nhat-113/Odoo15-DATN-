odoo.define('ds_company_management.company_management_common', function (require) {
    "use strict";

    const total_year = 5

    const get_most_recent_year = (selectionHistory) => {
        let currentYear = new Date().getFullYear();
        for (let i = 0; i < total_year; i++){
            let option = document.createElement("option");
            option.value = currentYear - i
            option.text = currentYear - i
            selectionHistory.add(option)
        }
    }

    return {
        get_most_recent_year: get_most_recent_year,
    };
});