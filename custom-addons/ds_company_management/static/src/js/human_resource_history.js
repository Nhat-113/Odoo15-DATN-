odoo.define('human_resource_template_history.Dashboard', function (require) {
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
    const number_rows_not_count = 4;

    var HumanResourceHistoryTemplate = AbstractAction.extend({
        template: 'Human_resource_history',
        jsLibs: ["ds_company_management/static/src/js/lib/table2excel.js"],
        events: {

            "click .export_excel": "export_excel",
            "click .view-member-free": "view_effort_member_free",
            "click .close-table": "close_effort_member_free",
        },

        init: function (parent, context) {
            this.action_id = context['id'];
            this._super(parent, context);
            this.list_human_resource = [];
            this.list_human_resource_free = [];
        },

        start: function () {
            let self = this;
            this.set("title", 'Human Resource Management');
            return this._super().then(function () {
                // self.render_dashboards();
                setTimeout(() => {

                    var input = document.getElementById("search_input");
                    if(!input)  
                         return
                    // Event search in when input onchange
                    // after event search run, event compute_avg call again to calculator avg effort 
                    input.addEventListener('keyup', () => self.callBackFunction())

                    var input_available_list = document.getElementById("search_input_avai");
                    if(!input_available_list)  
                         return
                    // Event search in when input onchange
                    input_available_list.addEventListener('keyup', self.searchFunctionAvaiList);
                    input_available_list.addEventListener('keyup', () => self.value_table_over_view());


                    // Event filter  in when selection onchange
                    var selection = document.getElementById("filter-project-type");
                    var selectionHistory = document.getElementById("filter-year");

                    if(!selection)  
                        return
                    selection.addEventListener('change', () => self.callBackFunction())
                    selectionHistory.addEventListener('change', () => self.callBackFunction())

                    // compute avg effort member in table when render DOM element   

                    //sort table
                    const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;
                    const comparer = (idx, asc) => (a, b) => ((v1, v2) => v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2))
                        (getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));
                        
                    var th = document.querySelectorAll('th.header_human_table')
                    var avgRow = document.getElementById('avg-row');
                    var totalRow = document.getElementById('total-row');
                    var totalEffortAll = document.getElementById('total-effort-all-res-rate');
                    var totalRowMember = document.getElementById('total-row-member-of-company');


                    th.forEach(th => th.addEventListener('click', (() => {
                        let table = th.closest('tbody');
                        Array.from(table.querySelectorAll('tr.detail'))
                            .sort(comparer(Array.from(th.parentNode.children).indexOf(th), window.asc = !window.asc))
                            .forEach(tr => table.appendChild(tr));
                        // append 2 this row in last row
                        table.appendChild(avgRow);
                        table.appendChild(totalRow);
                        table.appendChild(totalEffortAll);
                        table.appendChild(totalRowMember);

                    })));
                    //sort name in tale

                    const getCellValueNameEmployee = (tr, idx) => tr.children[idx].innerText.slice(tr.children[idx].innerText.lastIndexOf(' ') + 1)
                                                                    || tr.children[idx].textContent.slice(tr.children[idx].textContent.lastIndexOf(' ') + 1);
                    const comparerNameEmployee = (idx, asc) => (a, b) => ((v1, v2) => v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2))
                        (getCellValueNameEmployee(asc ? a : b, idx), getCellValueNameEmployee(asc ? b : a, idx));

                    var th_name = document.querySelectorAll('th.header_human_table_name')
                    
                    th_name.forEach(th_name => th_name.addEventListener('click', (() => {
                        let table = th_name.closest('tbody');
                        Array.from(table.querySelectorAll('tr.detail'))
                            .sort(comparerNameEmployee(Array.from(th_name.parentNode.children).indexOf(th_name), window.asc = !window.asc))
                            .forEach(tr => table.appendChild(tr));
                        // append 2 th_name is row in last row
                        table.appendChild(avgRow);
                        table.appendChild(totalRow);
                        table.appendChild(totalEffortAll);
                        table.appendChild(totalRowMember);

                    })));


                    // sort table member free
                    var lastRowFreeTable = document.getElementById('bottom_table');
                    var row_table_not_sort = document.getElementById('bottom_avai_headcount');
                    var row_table_not_sort_2 = document.getElementById('bottom_avai_headcount_rate');
                    var th_2 = document.querySelectorAll('th.header_member_free')
                    var avgRow = document.getElementById('avg-row');
                    var totalRow = document.getElementById('total-row');
                    th_2.forEach(th_2 => th_2.addEventListener('click', (() => {
                        let table = th_2.closest('tbody');
                        Array.from(table.querySelectorAll('tr.detail'))
                            .sort(comparer(Array.from(th_2.parentNode.children).indexOf(th_2), window.asc = !window.asc))
                            .forEach(tr => table.appendChild(tr));
                            table.appendChild(lastRowFreeTable);
                            table.appendChild(row_table_not_sort);
                            table.appendChild(row_table_not_sort_2);
                        // append 2 this row in last row
                    })));


                    //sort name in table free
                    var th_name = document.querySelectorAll('th.header_member_free_name')
                    th_name.forEach(th_name => th_name.addEventListener('click', (() => {
                        let table = th_name.closest('tbody');
                        Array.from(table.querySelectorAll('tr.detail'))
                            .sort(comparerNameEmployee(Array.from(th_name.parentNode.children).indexOf(th_name), window.asc = !window.asc))
                            .forEach(tr => table.appendChild(tr));
                        // append last row th_name is row in last row
                        table.appendChild(lastRowFreeTable);
                        table.appendChild(row_table_not_sort);
                        table.appendChild(row_table_not_sort_2);
                    })));

                    self.compute_avg();
                    self.compute_avg_all_res_rate();
                    self.compute_avg_all_avai_rate();
                    self.value_table_over_view();
                }, 500);
            });
        },


        willStart: function () {
            let self = this;
            return $.when(ajax.loadLibs(this), this._super()).then(function () {
                return self.fetch_data();

            });
        },

        fetch_data: function () {
            let self = this;
            var def1 = this._rpc({
                model: "human.resource.management.history",
                method: "get_list_human_resource_history",
            })
                .then(function (res) {
                    if (res["list_human_resource_history"].length > 0) {
                        self.list_human_resource_history = self.processMonthAvailable(res["list_human_resource_history"])
                        console.log(`self.list_human_resource_history`, self.list_human_resource_history);
                    } else {
                        self.list_human_resource_history = res["list_human_resource_history"]
                    }
                });

            var def2 = this._rpc({
                model: "human.resource.management.history",
                method: "get_human_resource_free_history",
            })
                .then(function (res) {
                    if (res["get_human_resource_free_history"].length > 0) {
                        self.get_human_resource_free_history = self.processMonthAvailableFree(res["get_human_resource_free_history"])
                    } else {
                        self.get_human_resource_free_history = res["get_human_resource_free_history"]
                    }
                });
            return $.when(def1, def2);
        },

        callBackFunction: function () {
            let self = this;
             self.searchFunction();
            // after event search run,event compute_avg call again to calculator avg effort 
            self.compute_avg();
            self.compute_avg_all_res_rate();
            self.value_table_over_view();
        },

        // Function: Process effort rate's employee data depend on state (running or expired) of contract
        processMonthAvailable: function (arr) {
            // Get array of dimensions
            const dimensions = [arr.length, arr[0].length];

            let arrCheckMonth = new Array();
            arr.forEach(childArr => {
                if (childArr[dimensions[1] - 2] != null) {
                    /*
                        Start Date column's index is 2rd last of array
                        End Date column's index is the last index of array
                     */
                    let arrStartDate = childArr[dimensions[1] - 2].split(',');
                    let arrEndDate = childArr[dimensions[1] - 1].split(',');
                    let yearOfHistory = childArr[28];

                    let contractAvailableSet = new Set();

                    for (let index = 0; index < arrStartDate.length; index++) {
                        if (parseInt(arrStartDate[index].split('-')[1]) < (yearOfHistory) &&
                            parseInt(arrEndDate[index].split('-')[1]) == 0) {
                            for (let i = 1; i <= 12; i++) {
                                contractAvailableSet.add(i);
                            }
                        } else if (parseInt(arrStartDate[index].split('-')[1]) == (yearOfHistory)) {
                            if (parseInt(arrStartDate[index].split('-')[0]) <= parseInt(arrEndDate[index].split('-')[0]) &&
                                parseInt(arrEndDate[index].split('-')[0]) != 0) {
                                for (let i = parseInt(arrStartDate[index].split('-')[0]); i <= parseInt(arrEndDate[index].split('-')[0]); i++) {
                                    contractAvailableSet.add(i);
                                }
                            } else if (parseInt(arrEndDate[index].split('-')[0]) == 0) {
                                for (let i = parseInt(arrStartDate[index].split('-')[0]); i <= 12; i++) {
                                    contractAvailableSet.add(i);
                                }
                            }
                        }
                    }
                    arrCheckMonth.push(contractAvailableSet);
                } else {
                    arrCheckMonth.push(new Set());
                }
            });
            for (let index = 0; index < arr.length; index++) {
                let sum = 0,
                    cnt = 0,
                    cntGreaterThanZero = 0;
                /*
                    January column's index in array is 7
                    December column's index in arrayy is 18
                 */
                for (let i = 6; i <= 18; i++) {
                    if (!arrCheckMonth[index].has(i - 5)) {
                        arr[index][i] = "NaN";
                    } else {
                        sum += arr[index][i];
                        cnt++;
                        if (arr[index][i] > 0) cntGreaterThanZero++;
                    }
                }
                // Average column's index in array is 19
                arr[index][19] = cnt > 0 ? Number.parseFloat(sum / (cntGreaterThanZero > 0 ? cntGreaterThanZero : 1) ).toFixed(2) : "NaN";
            }
            return arr;
        },

        processMonthAvailableFree: function (arrFree) {

            const dimensions = [arrFree.length, arrFree[0].length];

            let arrCheckMonth = new Array();

            arrFree.forEach(childArr => {
                if (childArr[dimensions[1] - 2] != null) {
                    /*
                        Start Date column's index is 2rd last of array
                        End Date column's index is thearrCheckMonth last index of array
                     */
                    let arrStartDate = childArr[dimensions[1] - 2].split(',');
                    let arrEndDate = childArr[dimensions[1] - 1].split(',');

                    let contractAvailableSet = new Set();

                    for (let index = 0; index < arrStartDate.length; index++) {
                        if (parseInt(arrStartDate[index].split('-')[1]) < (new Date().getFullYear()) &&
                            parseInt(arrEndDate[index].split('-')[1]) == 0) {
                            for (let i = 1; i <= 12; i++) {
                                contractAvailableSet.add(i);
                            }
                        } else if (parseInt(arrStartDate[index].split('-')[1]) == (new Date().getFullYear())) {
                            if (parseInt(arrStartDate[index].split('-')[0]) <= parseInt(arrEndDate[index].split('-')[0]) &&
                                parseInt(arrEndDate[index].split('-')[0]) != 0) {
                                for (let i = parseInt(arrStartDate[index].split('-')[0]); i <= parseInt(arrEndDate[index].split('-')[0]); i++) {
                                    contractAvailableSet.add(i);
                                }
                            } else if (parseInt(arrEndDate[index].split('-')[0]) == 0) {
                                for (let i = parseInt(arrStartDate[index].split('-')[0]); i <= 12; i++) {
                                    contractAvailableSet.add(i);
                                }
                            }
                        }
                    }
                    arrCheckMonth.push(contractAvailableSet);
                } else {
                    arrCheckMonth.push(new Set());
                }
            });

            let notFreeEmployeeSet = new Array();

            for (let index = 0; index < arrFree.length; index++) {
                let cnt = 0, cntMonthNotContract = 0;
                /*
                    January column's index in array is 4
                    December column's index in array is 15
                 */
                for (let i = 4; i <= 15; i++) {
                    if (!arrCheckMonth[index].has(i - 3)) {
                        arrFree[index][i] = "NaN";
                        cntMonthNotContract++;
                    } else {
                        if (arrFree[index][i] == 100) {
                            cnt++;
                        }
                    }
                }
                if (cnt + cntMonthNotContract == 12) {
                    notFreeEmployeeSet.push(index);
                }
            }
            for (let i = notFreeEmployeeSet.length - 1; i >= 0; i--) {
                arrFree.splice(notFreeEmployeeSet[i], 1);
            }
            return arrFree;
        },

        searchFunction: function(e) {
            const value_row_not_search = 4
            let selection = document.getElementById("filter-project-type");
            let filterSelection = selection.value.toUpperCase();

            let selectionYearHistory = document.getElementById("filter-year");
            let filterSelectionYearHistory = selectionYearHistory.value.toUpperCase();
            var input, filter, table, tr, td, i, txtValue, year_of_history_value, year_of_history;
            input = document.getElementById("search_input");
            filter = input.value.toUpperCase();

            table = document.getElementById("human_resource_table");
            if (!table) return;
            tr = table.getElementsByTagName("tr");  
            
            for (i = 1; i < tr.length - value_row_not_search; i++) {
                td = tr[i];
                year_of_history = tr[i].querySelector('.Year_of_history')
                console.log(`tr[i]`, tr[i]);
                year_of_history_value = year_of_history.textContent || year_of_history.innerText

                // project ALL in human
                if (filterSelection == 'ALL') {
                    if (td) {
                        txtValue = td.textContent || td.innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1 && year_of_history_value.toUpperCase().indexOf(filterSelectionYearHistory) > -1 ) {
                            tr[i].style.display = '';
                        } else {
                            tr[i].style.display = 'none';
                        }
                    }
                }
                // project INTERNAL
                // if (filterSelection == 'PROJECT INTERNAL') {
                //     txtValue = td.textContent || td.innerText;
                //     if (txtValue.toUpperCase().indexOf(filter) > -1   && (year_of_history_value.toUpperCase().indexOf(filterSelectionYearHistory) > -1 ) ) {
                //         tr[i].style.display = '';
                //     }                           
                //     if (( txtValue.toUpperCase().indexOf('ODC') > -1 || txtValue.toUpperCase().indexOf('PROJECT BASE') > -1 || txtValue.toUpperCase().indexOf(filter) <= -1) 
                //             && (year_of_history_value.toUpperCase().indexOf(filterSelectionYearHistory) <= -1 )
                //     )
                //         {
                //             tr[i].style.display = 'none';
                //         } 
                // }
                if (filterSelection == 'PROJECT INTERNAL') {
                    txtValue = td.textContent || td.innerText;
                    if ( (txtValue.toUpperCase().indexOf('INTERNAL') > -1 || txtValue.toUpperCase().indexOf(null) > -1) 
                            && txtValue.toUpperCase().indexOf(filter) > -1
                            && (year_of_history_value.toUpperCase().indexOf(filterSelectionYearHistory) > -1 )
                            ){
                        tr[i].style.display = '';
                    } else {
                        tr[i].style.display = 'none';
                    }
                }

                // project BILLABLE
                if (filterSelection == 'PROJECT BILLABLE') {
                    txtValue = td.textContent || td.innerText;
                    if ( (txtValue.toUpperCase().indexOf('ODC') > -1 || txtValue.toUpperCase().indexOf('PROJECT BASE') > -1) 
                            && txtValue.toUpperCase().indexOf(filter) > -1
                            && (year_of_history_value.toUpperCase().indexOf(filterSelectionYearHistory) > -1 )
                            ){
                        tr[i].style.display = '';
                    } else {
                        tr[i].style.display = 'none';
                    }
                }
            }

        },
        searchFunctionAvaiList: function(e) {
            const value_row_not_search = 3;
            var input, filter, table, tr, td, i, txtValue;
            input = document.getElementById("search_input_avai");
            filter = input.value.toUpperCase();

            table = document.getElementById("human_resource_free_table");
            if (!table) return;
            tr = table.getElementsByTagName("tr");  

            for (i = 1; i < tr.length - value_row_not_search; i++) {
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

        compute_avg: function () {
            let self = this;
            var final = 0;
            const row_value_member = 4;
            const row_value_effort = 3;

            var tbody = document.getElementById("human_reource_tbody");
            var total_row = tbody.rows[tbody.rows.length - row_value_member];
            var total_available_member = tbody.rows[tbody.rows.length - row_value_effort];
            var count_compute_available_member = 0;
            var count_compute_member = 0;
            var arrMemberFollowMonth = [];

            var count_compute_available_member_billable = 0;
            var arrMemberBillFollowMonth = [];
            var effortBillFollowMonth = 0;
            var arrEffortBillFollowMonth = [];

            var count_compute_available_member_internal = 0;
            var arrMemberInterFollowMonth = [];
            var effortInternalFollowMonth = 0;
            var arrEffortInternalFollowMonth = [];


            var howManyCols = tbody.rows[1].cells.length;
            var arrEffortCompany = []
            // Start compute in column number seven
            for (var j = 7; j < howManyCols - 1; j++) {
                //compute member available company
                count_compute_available_member = self.compute_available_member(j);
                count_compute_member = self.compute_member_when_search(j);

                arrMemberFollowMonth.push(count_compute_member);

                //compute member billable in company
                count_compute_available_member_billable = self.compute_available_member_billable(j).count_billable_member;
                arrMemberBillFollowMonth.push(count_compute_available_member_billable);
                //compute effort billable in company
                effortBillFollowMonth =  self.computeTableColumnBillable(j).effortBill;
                arrEffortBillFollowMonth.push(effortBillFollowMonth);

                //compute member internal in company
                count_compute_available_member_internal = self.compute_available_member_internal(j).count_internal_member;
                arrMemberInterFollowMonth.push(count_compute_available_member_internal);
                effortInternalFollowMonth =  self.computeTableColumnBillable(j).effortInternal;
                arrEffortInternalFollowMonth.push(effortInternalFollowMonth);
                // count_number_row = self.compute_count_number_row(j);
                total_available_member.cells[j].innerText = count_compute_available_member;
                final = self.computeTableColumnTotal(j);
                arrEffortCompany.push(final);

                // avg = (total effort( > 0 and another N/A  )) / total members in column with effort another N/A 
                total_row.cells[j].innerText = parseFloat(final / count_compute_available_member).toFixed(2);
            }
            
            //count members of company with value from second column
            // total_member_company.innerText = String( 'Current Month Active Members: ' +  self.compute_member_company());

            return [arrEffortCompany, arrMemberFollowMonth, 
                    arrMemberBillFollowMonth, arrMemberInterFollowMonth,
                    arrEffortBillFollowMonth, arrEffortInternalFollowMonth];
        },

        compute_avg_all_res_rate: function () {
            let self = this;
            var effort_rate_company = 0;
            const row_value_effort = 1;
            const row_value_member = 2;
            var tbody = document.getElementById("human_reource_tbody");
            var total_row = tbody.rows[tbody.rows.length - row_value_member];
            var total_available_member = tbody.rows[tbody.rows.length -row_value_effort];
            var count_compute_available_member = 0;
            var howManyCols = tbody.rows[1].cells.length;
            let array_effort_rate_company = [];
            // Start compute in column number seven
            for (var j = 7; j < howManyCols - 1; j++) {
                count_compute_available_member = self.compute_available_member_res_rate(j);

                // count_number_row = self.compute_count_number_row(j);
                total_available_member.cells[j].innerText = count_compute_available_member;
                effort_rate_company = self.computeTableColumnTotal(j);
                // avg = (total effort( > 0 and another N/A  )) / total members in column with effort another N/A 
                total_row.cells[j].innerText = parseFloat(effort_rate_company / count_compute_available_member).toFixed(2);
                array_effort_rate_company.push(effort_rate_company);
            }   
            return array_effort_rate_company;
         
        },

        compute_available_member_res_rate: function (colNumber) {
            var table = document.getElementById("human_resource_table");
            var howManyRows = 0;
            let count_row = 0;
            // const number_rows_not_count = 4;
            let listId = [];
            try {
                var howManyRows = table.rows.length;
                for (var i = 1; i < howManyRows - number_rows_not_count; i++) {
                    // let row = table.rows[i];
                    let id_employee = table.rows[i].cells[1].innerText;
                    var thisNumber = parseFloat(table.rows[i].cells[colNumber].childNodes.item(0).data);         
                    
                    if (!isNaN(thisNumber) && !listId.includes(id_employee)) {
                        count_row += 1;
                        listId.push(id_employee);
                    }
                }
            } finally {
                return count_row;
            }
        },  

        compute_member_when_search: function (colNumber) {
            var table = document.getElementById("human_resource_table");
            var howManyRows = 0;
            let count_row = 0;
            // const number_rows_not_count = 4
            let listId = [];
            try {
                var howManyRows = table.rows.length;
                for (var i = 1; i < howManyRows - number_rows_not_count; i++) {
                    let row = table.rows[i];
                    let id_employee = table.rows[i].cells[1].innerText;
                    let parent_style = row.cells[colNumber].parentElement.style.display;
                    var thisNumber = parseFloat(table.rows[i].cells[colNumber].childNodes.item(0).data);
                    // var employee_id_before = table.rows[i].cells[1].innerText;
                    // var employee_id_after = table.rows[i+1].cells[1].innerText;                  

                    if (parent_style != 'none' && !isNaN(thisNumber) && !listId.includes(id_employee) && thisNumber >= 0) {
                        count_row += 1;
                        listId.push(id_employee);
                    }

                }
            } finally {
                return count_row;
            }
        },  

        computeTableColumnTotal: function (colNumber) {
            var table = document.getElementById("human_resource_table");
            let result = 0;
            // const number_rows_not_count = 4;
            var howManyRows = 0;
            try {
                var howManyRows = table.rows.length;
                for (var i = 1; i < howManyRows - number_rows_not_count; i++) {
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

        computeTableColumnBillable: function (colNumber) {
            var table = document.getElementById("human_resource_table");
            let effortBill = 0;
            let effortInternal = 0;

            // const number_rows_not_count = 4;
            var howManyRows = 0;
            try {
                var howManyRows = table.rows.length;
                for (var i = 1; i < howManyRows - number_rows_not_count; i++) {
                    let row = table.rows[i];
                    let parent_style = row.cells[colNumber].parentElement.style.display;
                    // project type is column number six 
                    let project_type = table.rows[i].cells[6].innerText;

                    var thisNumber = parseFloat(table.rows[i].cells[colNumber].childNodes.item(0).data);

                    if (parent_style != 'none' && !isNaN(thisNumber) && thisNumber > 0 && (project_type == 'ODC' || project_type == 'Project Base') ) {
                        effortBill = effortBill + thisNumber;
                    }
                    if (parent_style != 'none' && !isNaN(thisNumber) && thisNumber > 0 && project_type == 'Internal') {
                        effortInternal = effortInternal + thisNumber;
                    }
                }
            } finally {
                return {
                    effortBill: effortBill, 
                    effortInternal: effortInternal
                }
            }
        },

        compute_available_member: function (colNumber) {
            var table = document.getElementById("human_resource_table");
            var howManyRows = 0;
            let count_row = 0;
            // const number_rows_not_count = 4
            let listId = [];
            try {
                var howManyRows = table.rows.length;
                for (var i = 1; i < howManyRows - number_rows_not_count; i++) {
                    let row = table.rows[i];
                    let id_employee = table.rows[i].cells[1].innerText;
                    let parent_style = row.cells[colNumber].parentElement.style.display;
                    var thisNumber = parseFloat(table.rows[i].cells[colNumber].childNodes.item(0).data);
                    // var employee_id_before = table.rows[i].cells[1].innerText;
                    // var employee_id_after = table.rows[i+1].cells[1].innerText;                  

                    if (parent_style != 'none' && !isNaN(thisNumber) && !listId.includes(id_employee) && thisNumber > 0) {
                        count_row += 1;
                        listId.push(id_employee);
                    }

                }
            } finally {
                return count_row;
            }
        },

        compute_available_member_billable: function (colNumber) {
            var table = document.getElementById("human_resource_table");
            var howManyRows = 0;
            let count_billable_member = 0;
            let count_internal_member = 0;

            // const number_rows_not_count = 4
            let listId = [];
            try {
                var howManyRows = table.rows.length;
                for (var i = 1; i < howManyRows - number_rows_not_count; i++) {
                    let row = table.rows[i];
                    let id_employee = table.rows[i].cells[1].innerText;
                    let project_type = table.rows[i].cells[6].innerText;
                    let parent_style = row.cells[colNumber].parentElement.style.display;
                    var thisNumber = parseFloat(table.rows[i].cells[colNumber].childNodes.item(0).data);
          
                    if (parent_style != 'none' && !isNaN(thisNumber) && !listId.includes(id_employee) && thisNumber > 0 && (project_type == 'ODC' || project_type == 'Project Base')) {
                        count_billable_member += 1;
                        listId.push(id_employee);
                    }

                    // if (parent_style != 'none' && !isNaN(thisNumber) && !listId.includes(id_employee) && thisNumber > 0 &&  (project_type != 'ODC' || project_type != 'Project Base')) {
                    //     count_internal_member += 1;
                    //     listId.push(id_employee);
                    // }

                }
            } finally {
                return {
                    count_billable_member: count_billable_member, 
                    // count_internal_member: count_internal_member
                };
            }
        },

        compute_available_member_internal: function (colNumber) {
            var table = document.getElementById("human_resource_table");
            var howManyRows = 0;
            // let count_billable_member = 0;
            let count_internal_member = 0;

            // const number_rows_not_count = 4
            let listId = [];
            try {
                var howManyRows = table.rows.length;
                for (var i = 1; i < howManyRows - number_rows_not_count; i++) {
                    let row = table.rows[i];
                    let id_employee = table.rows[i].cells[1].innerText;
                    let project_type = table.rows[i].cells[6].innerText;
                    let parent_style = row.cells[colNumber].parentElement.style.display;
                    var thisNumber = parseFloat(table.rows[i].cells[colNumber].childNodes.item(0).data);
          
                    // if (parent_style != 'none' && !isNaN(thisNumber) && !listId.includes(id_employee) && thisNumber > 0 && (project_type == 'ODC' || project_type == 'Project Base')) {
                    //     count_billable_member += 1;
                    //     console.log(`a`);
                    //     listId.push(id_employee);
                    // }

                    if (parent_style != 'none' && !isNaN(thisNumber) && !listId.includes(id_employee) && thisNumber > 0 &&  (project_type == 'Internal')) {
                        count_internal_member += 1;
                        listId.push(id_employee);
                    }

                }
            } finally {
                return {
                    // count_billable_member: count_billable_member, 
                    count_internal_member: count_internal_member
                };
                // return count_billable_member, count_internal_member;
            }
        },


        export_excel: function () {
            Table2Excel.extend((cell, cellText) => {
                return $(cell).attr('type') == 'string' ? {
                    t: 's',
                    v: cellText
                } : null;
            });

            var table2excel = new Table2Excel();

            var myTableHuman = document.getElementsByTagName("table")[1];

            var myCloneTable = myTableHuman.cloneNode(true);

            var element_none = myCloneTable.querySelectorAll('tr');

            for (let i = 0; i < element_none.length; i++) {
                if (element_none[i].style.display == 'none') {
                    element_none[i].remove();
                }
            }
            document.body.appendChild(myCloneTable);

            table2excel.export(myCloneTable);

            myCloneTable.remove();
            // Table2Excel.extend((cell, cellText) => {
            //     return $(cell).attr('type') == 'string' ? {
            //         t: 's',
            //         v: cellText
            //     } : null;
            // });

            // var table2excel = new Table2Excel();
            // // let table_to_exp = document.getElementById("human_resource_table").not("tr .total_member_avai_company");
            // let table_to_exp_2 = $("table #human_resource_table td").not("tr .total_member_avai_company")

            // // console.log(`table_to_exp`, table_to_exp);

            // // let tr_exp = table_to_exp.querySelectorAll("tr");

            // table2excel.export(table_to_exp_2);
            
            // var result = [];
            // var table =  document.getElementById("human_resource_table")
            // var rows = table.rows;
            // var cells, arrTemp;
          
            // for (var i=0, iLen=rows.length; i<iLen; i++) {
            //     cells = rows[i].cells;
            //     arrTemp = [];
            //     if(rows[i].style.display != 'none') {
            //         for (var j = 0, jLen = cells.length; j < jLen; j++) {
            //             arrTemp.push(cells[j].textContent.replace(/\n/g,'').replace(/\r/g,' ').trim());
            //         }
            //     }
            //   result.push(arrTemp);
            // }

            // let dataExport = [];

            // for(let i=0; i <  result.length ; i ++) {
            //     if (result[i].length > 0) {
            //         dataExport.push(result[i]);
            //     } 
            // }
            // var csvContent = ""
            // dataExport.forEach(function(RowItem, RowIndex) {
            //     RowItem.forEach(function(ColItem, ColIndex) {
            //     csvContent += ColItem + ',';
            //     });
            //     csvContent += "\r\n";
            // });
            // var ele = document.createElement("A");
            // ele.setAttribute("href",  "data:application/xls;charset=utf-8,%EF%BB%BF"+ encodeURI(csvContent) );
            // ele.setAttribute("download","human_resource.xls");
            // document.body.appendChild(ele);
            // ele.click();
        },

        view_effort_member_free: function () {
            document.getElementById('back-ground').style.display = "block"
        },

        close_effort_member_free: function () {
            var ele = document.getElementById('back-ground')
            if (ele.style.display === "block") {
                ele.style.display = "none"
            }
        },

        // replace_value_human_resource: function () {
        //     var table, cell_elements;
        //     table = document.getElementById('human_resource_table');
        //     if (!table) return;
        //     cell_elements = table.getElementsByTagName('td');
        //     for (var i = 0, len = cell_elements.length; i < len; i++) {

        //         if (cell_elements[i].innerHTML < 0) {
        //             cell_elements[i].innerText = "NaN";
        //         }
        //         if (cell_elements[i].innerText == "" && cell_elements[i].className == "AVG_colum") {
        //             cell_elements[i].innerText = "0";
        //         }
        //     }

        // },

        replace_value_human_resource_free: function () {
            var table_free, cell_elements_free;
            table_free = document.getElementById('human_resource_free_table');
            cell_elements_free = table_free.querySelectorAll('td.td_value');
            for (var i = 0, len = cell_elements_free.length; i < len; i++) {
                if (cell_elements_free[i].innerHTML < 0) {
                    cell_elements_free[i].innerText = "NaN";
                }
            }
            for (var i = 0, len = cell_elements_free.length; i < len; i++) {
                cell_elements_free[i].innerText = (100 - parseFloat(cell_elements_free[i].innerText)).toFixed(2);
            }
        },
        // hide_value_old_month: function() {
        //     var dateObj = new Date();

        //     var table = document.getElementById('human_resource_free_table');
        //     var month = dateObj.getUTCMonth() + 1;
        //     const number_month_in_year = 12;
        //     const current_month = (number_month_in_year - month) + 1;
        //     for (let i = 0; i < table.rows.length; i++) {
        //         var start_month_in_table = 4
        //         for (start_month_in_table; start_month_in_table < table.rows[i].cells.length - current_month; start_month_in_table++) {
        //             table.rows[i].cells[start_month_in_table].style.display = "none";
        //         }
        //     }
        // },


        // //compute avavai label rate
        computeTableColumnTotalFree: function (colNumber) {
            var table = document.getElementById("human_resource_free_table");
            let result = 0;
            // const number_rows_not_count = 4;
            var howManyRows = 0;
            try {
                var howManyRows = table.rows.length;
                for (var i = 1; i < howManyRows - 3; i++) {
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

        compute_avg_all_avai_rate: function () {
            let self = this;
            var final = 0;
            var member_free = 0;
            var tbody = document.getElementById("tbody_free_table");
            const number_column_calcu_in_table = 3
            var total_available_member = tbody.rows[tbody.rows.length - number_column_calcu_in_table];

            var howManyCols = tbody.rows[1].cells.length;
            var arrFreeEffort = [];
            var arrFreeMember = [];

            // var arrEffortHuman = self.compute_avg();
            var avgEffortInFreeTable = []

            //start calculator effort from  Fifth column => j = 5
            for (var j = 5 ; j < howManyCols; j++) {
                final = self.computeTableColumnTotalFree(j);
                arrFreeEffort.push(final);
                member_free = self.compute_member_free_company(j);
                arrFreeMember.push(member_free);
            }

            let data_array_effort_res_rate = self.compute_avg_all_res_rate()
            for (let i = 0 ; i < arrFreeEffort.length ;i++ ) {
                avgEffortInFreeTable[i] = ( arrFreeEffort[i] /  (data_array_effort_res_rate[i] + arrFreeEffort[i]) ) * 100 ;
                //column start replace value from number four
                total_available_member.cells[i+4].innerText = avgEffortInFreeTable[i].toFixed(2);
            }
            return [arrFreeMember, arrFreeEffort];
        },

        compute_member_free_company: function (colNumber) {
            var table = document.getElementById("human_resource_free_table");
            var howManyRows = 0;
            let count_members_of_company = 0;
            let listId = [];
            const number_rows_not_count_avai_resource = 3;
            try {
                var howManyRows = table.rows.length;
                for (var i = 1; i < howManyRows - number_rows_not_count_avai_resource; i++) {
                    let row = table.rows[i];
                    let id_employee = table.rows[i].cells[1].innerText;
                    let parent_style = row.cells[colNumber].parentElement.style.display;
                    var thisNumber = parseFloat(table.rows[i].cells[colNumber].childNodes.item(0).data);
                    if (parent_style != 'none' && !listId.includes(id_employee) &&  !isNaN(thisNumber) && thisNumber > 0) {
                        count_members_of_company += 1
                        listId.push(id_employee);
                    }
                }
            } finally {
                return count_members_of_company;
            }
        },

        value_table_over_view: function() {
            // let self = this;
            var  count_member_filter = this.compute_avg()[1];
            var  compute_effort_filter = this.compute_avg()[0];

            let textCountMember = document.getElementsByClassName('value-member-count');

            let textAverageUsageRate = document.getElementsByClassName('value-member-aver-usage');

            let textBillableHeadCount = document.getElementsByClassName('bill-able-headcounts');
            var count_member_billable = this.compute_avg()[2];
            let textBillableHeadCountRate = document.getElementsByClassName('bill-able-avg');
            var compute_effort_billable = this.compute_avg()[4];


            let textInternalHeadCount = document.getElementsByClassName('internal-headcounts');
            var count_member_internal = this.compute_avg()[3];
            let textInternalHeadCountRate = document.getElementsByClassName('internal-headcounts-avg');
            var compute_effort_internal = this.compute_avg()[5];
            let element_avg_eff = document.querySelectorAll('.Avg_effort_member .td_value');
            let value_aver = [];
         

            let textAvailableHeadCount = document.getElementsByClassName('available-headcounts');
            var count_member_available = this.compute_avg_all_avai_rate()[0];
            let textAvailableHeadCountRate = document.getElementsByClassName('available-headcounts-avg');
            var compute_effort_member_available = this.compute_avg_all_avai_rate()[1];

            var TodayDate = new Date();
            var current_month = TodayDate.getMonth();
            var total_member_company = document.getElementById("count_member_of_company");
            total_member_company.innerText = String( 'Current Month Active Members: ' +  count_member_filter[current_month] );

            var total_effort = []
            for (let i = 0; i < count_member_filter.length; i ++)  {
                total_effort.push(count_member_filter[i] * 100)
            }
            //add value in over view table 
            for(let i = 0; i < element_avg_eff.length ; i ++  ) {
                if (element_avg_eff[i].innerText != '' ) {
                    value_aver.push(element_avg_eff[i].innerText);
                }
            }

            //get value when search in tr total member 
            let count_member_in_company = document.querySelectorAll('#total-row .td_value');
            // console.log('count_member_in_company', count_member_in_company);
            //
            let count_member_in_company_when_search = [];

            //push for array
            for (let i = 0; i < count_member_in_company.length; i++) {
                if (count_member_in_company[i].innerText != '' ) {
                    // push data in array if has value
                    count_member_in_company_when_search.push(count_member_in_company[i].innerText);
                }
            }
            let selection = document.getElementById("filter-project-type");
            let filterSelection = selection.value.toUpperCase();

            //replace value
            for(let i = 0 ; i < textCountMember.length; i++ ){
                //with filter PROJECT BILLABLE value count member = member bill have effort > 0
                if (filterSelection == 'PROJECT BILLABLE' ) {
                    textCountMember[i].innerText = count_member_billable[i];
                }
                //with filter PROJECT INTERNAL value count member = member bill have effort > 0
                else if (filterSelection == 'PROJECT INTERNAL' ) {
                    textCountMember[i].innerText = count_member_internal[i];
                }
                else 
                    textCountMember[i].innerText = count_member_filter[i];
            }
            for(let i = 0 ; i <   textAverageUsageRate.length;  i++ ){
                textAverageUsageRate[i].innerText = ( compute_effort_filter[i] / count_member_filter[i] ).toFixed(2) ;
            }

            for(let i = 0 ; i < textBillableHeadCount.length; i++ ){
                textBillableHeadCount[i].innerText = count_member_billable[i];
            }

            for(let i = 0 ; i < textInternalHeadCount.length; i++ ){
                textInternalHeadCount[i].innerText = count_member_internal[i];
            }
          


            // value member company in human
            let element_member_company = document.querySelectorAll('#total-row-member-of-company .td_value');
            let total_element_member_company = [];

            for (let i = 0; i < element_member_company.length; i++) {
                if (element_member_company[i].innerText != '' ) {
                    total_element_member_company.push(element_member_company[i].innerText);
                }
            }

            for(let i = 0 ; i < textAvailableHeadCount.length; i++ ){
                textAvailableHeadCount[i].innerText = count_member_available[i];
            }
            for(let i = 0 ; i < textInternalHeadCountRate.length; i++ ){
                textInternalHeadCountRate[i].innerText = ((compute_effort_internal[i] / (total_element_member_company[i] * 100  )) * 100 ).toFixed(2) ;
            }
            for(let i = 0 ; i < textBillableHeadCountRate.length; i++ ){
                textBillableHeadCountRate[i].innerText = ( (compute_effort_billable[i] / (total_element_member_company[i] * 100  )) * 100 ).toFixed(2) ;
            }
            for(let i = 0 ; i < textAvailableHeadCountRate.length; i++ ){
                textAvailableHeadCountRate[i].innerText = ( ( compute_effort_member_available[i] / (total_element_member_company[i] * 100  )) * 100  ).toFixed(2) ;
            }
        },
    });

    core.action_registry.add('human_resource_template_history', HumanResourceHistoryTemplate);

    return HumanResourceHistoryTemplate;
});