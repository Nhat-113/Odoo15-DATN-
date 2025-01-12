odoo.define('human_resource_template_history_support.Dashboard', function (require) {
    "use strict";

    const FilterMenu = require("web.FilterMenu");
    const SearchBar = require("web.SearchBar");
    const { useModel } = require("web.Model");
    const { Component, hooks } = owl;

    var AbstractAction = require("web.AbstractAction");
    var ajax = require("web.ajax");
    var core = require("web.core");
    var rpc = require("web.rpc");
    var _t = core._t;
    var QWeb = core.qweb;

    const { useRef, useSubEnv } = hooks;
    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var _t = core._t;
    const number_rows_not_count = 4;
    const common = require('ds_company_management.company_management_common')

    var HumanResourceHistorySupportTemplate = AbstractAction.extend({
        template: 'Human_resource_history_support',
        jsLibs: ["ds_company_management/static/src/js/lib/table2excel.js"],
        events: {

            "click .export_excel": "export_excel",
        },

        init: function (parent, context) {
            this.action_id = context['id'];
            this._super(parent, context);
            this.list_human_resource = [];
        },

        start: function () {
            let self = this;
            this.set("title", 'Human Resource Management Support History');
            return this._super().then(function () {
                // self.render_dashboards();
                setTimeout(() => {

                    var input = document.getElementById("search_input");
                    if(!input)  
                         return
                    // Event search in when input onchange, after event search run, event compute_avg call again to calculator avg effort 
                    input.addEventListener('keyup', () => self.callBackDataFunction())

                    // Event filter  in when selection onchange
                    var selection = document.getElementById("filter-project-type");
                    var selectionHistory = document.getElementById("filter-year");

                    if(!selection)  
                        return
                    selection.addEventListener('change', () => self.callBackDataFunction())
                    selectionHistory.addEventListener('change', () => self.callBackDataFunction())
                    common.get_most_recent_year(selectionHistory)

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

                    self.compute_avg();
                    self.compute_avg_all_res_rate();
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
                method: "get_list_human_resource_history_support",
            })
                .then(function (res) {
                    if (res["list_human_resource_history_support"].length > 0) {
                        self.list_human_resource_history_support = self.processMonthAvailable(res["list_human_resource_history_support"])
                    } else {
                        self.list_human_resource_history_support = res["list_human_resource_history_support"]
                    }
                });


            return $.when(def1);
        },

        callBackDataFunction: function () {
            let self = this;
            self.searchFunction();
            // after event search run, event compute_avg call again to calculator avg effort 
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
                    January column's index in array is 6
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
        searchFunction: function(e) {
            const value_row_not_search = 4
            let selection = document.getElementById("filter-project-type");
            let filterSelection = selection.value.toUpperCase();

            let selectionYearHistory = document.getElementById("filter-year");
            let filterSelectionYearHistory = selectionYearHistory.value.toUpperCase();
            var input, filter, table, tr, td, i, txtValue, year_of_history_value, year_of_history, project_type, project_type_value;
            input = document.getElementById("search_input");
            filter = input.value.toUpperCase();

            table = document.getElementById("human_resource_table");
            if (!table) return;
            tr = table.getElementsByTagName("tr");  
            
            for (i = 1; i < tr.length - value_row_not_search; i++) {
                td = tr[i];
                year_of_history = tr[i].querySelector('.Year_of_history');
                project_type = tr[i].querySelector('.project_type');
                year_of_history_value = year_of_history.textContent || year_of_history.innerText;
                project_type_value = project_type.textContent || project_type.innerText;
                
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
                if (filterSelection == 'PROJECT INTERNAL') {
                    txtValue = td.textContent || td.innerText;
                if  (   (txtValue.toUpperCase().indexOf('INTERNAL') > -1) && txtValue.toUpperCase().indexOf(filter) > -1
                        && (year_of_history_value.toUpperCase().indexOf(filterSelectionYearHistory) > -1 )
                        && (project_type_value.toUpperCase().indexOf('') > -1 )
                    )
                    {
                        tr[i].style.display = '';
                    }
                else 
                    {
                        tr[i].style.display = 'none';
                    }
                }

                // project BILLABLE
                if (filterSelection == 'PROJECT BILLABLE') {
                    txtValue = td.textContent || td.innerText;
                    if  (   (txtValue.toUpperCase().indexOf('ODC') > -1 || txtValue.toUpperCase().indexOf('PROJECT BASE') > -1) 
                            && txtValue.toUpperCase().indexOf(filter) > -1
                            && (year_of_history_value.toUpperCase().indexOf(filterSelectionYearHistory) > -1 )
                        )
                    {
                        tr[i].style.display = '';
                    } 
                    else {
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
                }
            } finally {
                return {
                    count_billable_member: count_billable_member, 
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
          
                    if (parent_style != 'none' && !isNaN(thisNumber) && !listId.includes(id_employee) && thisNumber > 0 &&  (project_type == 'Internal')) {
                        count_internal_member += 1;
                        listId.push(id_employee);
                    }

                }
            } finally {
                return {
                    count_internal_member: count_internal_member
                };
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
            let element_member_company = document.querySelectorAll('#total-row-member-of-company .available-headcounts-avg');
            let total_element_member_company = [];

            for (let i = 0; i < element_member_company.length; i++) {
                if (element_member_company[i].innerText != '' ) {
                    total_element_member_company.push(element_member_company[i].innerText);
                }
            }
            total_element_member_company = total_element_member_company.slice(5);

            for(let i = 0 ; i < textInternalHeadCountRate.length; i++ ){
                textInternalHeadCountRate[i].innerText = ((compute_effort_internal[i] / (total_element_member_company[i] * 100  )) * 100 ).toFixed(2) ;
            }
            for(let i = 0 ; i < textBillableHeadCountRate.length; i++ ){
                textBillableHeadCountRate[i].innerText = ( (compute_effort_billable[i] / (total_element_member_company[i] * 100  )) * 100 ).toFixed(2) ;
            }
        },
    });

    core.action_registry.add('human_resource_template_history_support', HumanResourceHistorySupportTemplate);

    return HumanResourceHistorySupportTemplate;
});