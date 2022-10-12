odoo.define('human_resource_template.Dashboard', function(require) {
    "use strict";

    const ActionMenus = require("web.ActionMenus");
    const ComparisonMenu = require("web.ComparisonMenu");
    const ActionModel = require("web.ActionModel");
    const FavoriteMenu = require("web.FavoriteMenu");
    const FilterMenu = require("web.FilterMenu");
    const GroupByMenu = require("web.GroupByMenu");
    const Pager = require("web.Pager");
    const SearchBar = require("web.SearchBar");
    const { useModel } = require("web.Model");
    const { Component, hooks } = owl;

    var concurrency = require("web.concurrency");
    var config = require("web.config");
    var field_utils = require("web.field_utils");
    var time = require("web.time");
    var utils = require("web.utils");
    var AbstractAction = require("web.AbstractAction");
    var ajax = require("web.ajax");
    var Dialog = require("web.Dialog");
    var field_utils = require("web.field_utils");
    var core = require("web.core");
    var rpc = require("web.rpc");
    var web_client = require("web.web_client");
    var abstractView = require("web.AbstractView");
    var _t = core._t;
    var QWeb = core.qweb;

    const { useRef, useSubEnv } = hooks;
    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var web_client = require('web.web_client');
    var _t = core._t;
    var QWeb = core.qweb;

    var HumanResourceTemplate = AbstractAction.extend({
        template: 'Human_resource',
        jsLibs: ["ds_company_management/static/src/js/lib/table2excel.js"],
        events: {
            "click .export_excel": "export_excel",
            "click .header_tabel": "sort_table",

        },

        init: function(parent, context) {
            this.action_id = context['id'];
            this._super(parent, context);
            this.list_human_resource = [];
        },

        start: function() {
            let self = this;
            this.set("title", 'Human Resource Management');
            return this._super().then(function() {
                // self.render_dashboards();
                setTimeout(() => {
                    var table, cell_elements;
                    table = document.getElementById('human_resource_table');
                    cell_elements = table.getElementsByTagName('td');
                    for (var i = 0, len = cell_elements.length; i < len; i++) {

                        if (cell_elements[i].innerHTML < 0) {
                            cell_elements[i].innerText = "NaN";
                        }
                        if (cell_elements[i].innerText == "" && cell_elements[i].className == "AVG_colum") {
                            cell_elements[i].innerText = "0";
                        }
                    }
                    var input = document.getElementById("search_input");
                    // Event search in when input onchange
                    input.addEventListener('keyup', self.searchFunction)
                        // after event search run, event compute_avg call again to calculator avg effort 
                    input.addEventListener('keyup', () => self.compute_avg())
                        // compute avg effort member in table when render DOM element

                        //sort table
                    const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;
                    const comparer = (idx, asc) => (a, b) => ((v1, v2) => v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2))
                        (getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));
                    var th = document.querySelectorAll('th')
                    var avgRow = document.getElementById('avg-row');
                    var totalRow = document.getElementById('total-row');
                    th.forEach(th => th.addEventListener('click', (() => {
                        let table = th.closest('tbody');
                        Array.from(table.querySelectorAll('tr.detail'))
                            .sort(comparer(Array.from(th.parentNode.children).indexOf(th), window.asc = !window.asc))
                            .forEach(tr => table.appendChild(tr));
                            // append 2 this row in last row
                        table.appendChild(avgRow);
                        table.appendChild(totalRow);
                    })));

                    self.compute_avg();
                }, 200);
            });
        },


        willStart: function() {
            let self = this;
            return $.when(ajax.loadLibs(this), this._super()).then(function() {
                return self.fetch_data();

            });
        },

        fetch_data: function() {
            let self = this;
            var def2 = this._rpc({
                    model: "human.resource.management",
                    method: "get_list_human_resource",
                })
                .then(function(res) {
                    self.list_human_resource = res["list_human_resource"];
                });
            // return $.when(def1, def2);
            return $.when(def2);

        },

        searchFunction: function(e) {
            var input, filter, table, tr, td, i, txtValue;
            input = document.getElementById("search_input");
            filter = input.value.toUpperCase();
            table = document.getElementById("human_resource_table");
            tr = table.getElementsByTagName("tr");
            for (i = 1; i < tr.length - 2; i++) {
                td = tr[i];
                if (td) {
                    txtValue = td.textContent || td.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {
                        tr[i].style.display = '';
                    } else {
                        tr[i].style.display = 'none';
                    }
                }
            }
        },

        compute_avg: function() {
            let self = this;
            var final = 0;
            var tbody = document.querySelector("tbody");
            var total_row = tbody.rows[tbody.rows.length - 2];
            var total_available_member = tbody.rows[tbody.rows.length - 1];
            var count_compute_available_member = 0;
            var howManyCols = tbody.rows[1].cells.length;
            var total_member_company = document.getElementById("count_member_of_company");

            // Start compute in column number seven
            for (var j = 7; j < howManyCols; j++) {
                count_compute_available_member = self.compute_available_member(j);

                // count_number_row = self.compute_count_number_row(j);
                total_available_member.cells[j].innerText = count_compute_available_member;
                final = self.computeTableColumnTotal(j);

                // avg = (total effort( > 0 and another N/A  )) / total members in column with effort another N/A 
                total_row.cells[j].innerText = parseFloat(final / count_compute_available_member).toFixed(2);
            }
            //count members of company with value from second column
            total_member_company.innerText = String(self.compute_member_company() + ' Members' );

        },

        computeTableColumnTotal: function(colNumber) {
            var table = document.getElementById("human_resource_table");
            let result = 0;
            var howManyRows = 0;
            try {
                var howManyRows = table.rows.length;
                for (var i = 1; i < howManyRows - 2; i++) {
                    let row = table.rows[i];
                    let parent_style = row.cells[colNumber].parentElement.style.display
                    var thisNumber = parseFloat(table.rows[i].cells[colNumber].childNodes.item(0).data);
                    if (parent_style != 'none' && !isNaN(thisNumber) && thisNumber > 0) {
                        result = result + thisNumber;
                    }
                }
            } finally {
                return result;
            }
        },

        compute_available_member: function(colNumber) {
            var table = document.getElementById("human_resource_table");
            var howManyRows = 0;
            let count_row = 0;
            let listId = [];
            try {
                var howManyRows = table.rows.length;
                for (var i = 1; i < howManyRows - 2; i++) {
                    let row = table.rows[i];
                    let id_employee = table.rows[i].cells[1].innerText;
                    let parent_style = row.cells[colNumber].parentElement.style.display;
                    var thisNumber = parseFloat(table.rows[i].cells[colNumber].childNodes.item(0).data);
                    // var employee_id_before = table.rows[i].cells[1].innerText;
                    // var employee_id_after = table.rows[i+1].cells[1].innerText;                  

                    if (parent_style != 'none' && !isNaN(thisNumber) && !listId.includes(id_employee) ) {
                        count_row += 1;
                        listId.push(id_employee);
                    }

                }
            } finally {
                return count_row;
            }
        },

        compute_member_company: function(colNumber = 1) {
            var table = document.getElementById("human_resource_table");
            var howManyRows = 0;
            let count_members_of_company = 0;
            let listId = [];
            try {
                var howManyRows = table.rows.length;
                for (var i = 1; i < howManyRows - 2; i++) {
                    let row = table.rows[i];
                    let id_employee = table.rows[i].cells[1].innerText;
                    let parent_style = row.cells[colNumber].parentElement.style.display;            

                    if (parent_style != 'none'  && !listId.includes(id_employee) ) {
                        count_members_of_company += 1
                        listId.push(id_employee);
                    }
                }
            } finally {
                return count_members_of_company;
            }
        },


        //     var table = document.getElementById("human_resource_table");
        //     var howManyRows = 0;
        //     let count_number_row = 0;
        //     try {
        //         var howManyRows = table.rows.length;
        //         for (var i = 1; i < howManyRows - 2; i++) {
        //             let row = table.rows[i];
        //             let parent_style = row.cells[colNumber].parentElement.style.display;
        //             if (parent_style != 'none') {
        //                 count_number_row += 1
        //             }
        //         }
        //     } finally {
        //         return count_number_row;
        //     }
        // },


        export_excel: function() {
            Table2Excel.extend((cell, cellText) => {
                return $(cell).attr('type') == 'string' ? {
                  t: 's',
                  v: cellText
                } : null;
            });
            
            var table2excel = new Table2Excel();
            table2excel.export(document.querySelectorAll("#human_resource_table"));
        },
        sort_table: function() {

        }
    });
    core.action_registry.add('human_resource_template', HumanResourceTemplate);

    return HumanResourceTemplate;
});