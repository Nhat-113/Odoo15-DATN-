odoo.define('human_resource_template.Dashboard', function (require) {
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

    var HumanResourceTemplate = AbstractAction.extend({
        template: 'Human_resource',
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
                    input.addEventListener('keyup', self.searchFunction)
                    // after event search run, event compute_avg call again to calculator avg effort 
                    input.addEventListener('keyup', () => self.compute_avg())
                    input.addEventListener('keyup', () => self.compute_avg_all_res_rate())

                    var input_available_list = document.getElementById("search_input_avai");
                    if(!input_available_list)  
                         return
                    // Event search in when input onchange
                    input_available_list.addEventListener('keyup', self.searchFunctionAvaiList);

                    // Event filter  in when selection onchange
                    var selection = document.getElementById("countriesDropdown");
                    if(!selection)  
                        return
                    selection.addEventListener('change', self.searchFunction)
                    selection.addEventListener('change', () => self.compute_avg())
                    selection.addEventListener('change', () => self.compute_avg_all_res_rate())
  
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

                    // sort table member free
                    var lastRowFreeTable = document.getElementById('bottom_table');

                    var th = document.querySelectorAll('th.header_member_free')
                    var avgRow = document.getElementById('avg-row');
                    var totalRow = document.getElementById('total-row');
                    th.forEach(th => th.addEventListener('click', (() => {
                        let table = th.closest('tbody');
                        Array.from(table.querySelectorAll('tr.detail'))
                            .sort(comparer(Array.from(th.parentNode.children).indexOf(th), window.asc = !window.asc))
                            .forEach(tr => table.appendChild(tr));
                            table.appendChild(lastRowFreeTable);
                        // append 2 this row in last row
                    })));

                    self.replace_value_human_resource()
                    self.replace_value_human_resource_free()
                    self.compute_avg();
                    // self.hide_value_old_month();
                    self.compute_avg_all_res_rate();
                    self.compute_avg_all_avai_rate();
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
                model: "human.resource.management",
                method: "get_list_human_resource",
            })
                .then(function (res) {
                    if (res["list_human_resource"].length > 0) {
                        self.list_human_resource = self.processMonthAvailable(res["list_human_resource"])
                    } else {
                        self.list_human_resource = res["list_human_resource"]
                    }
                });

            var def2 = this._rpc({
                model: "human.resource.management",
                method: "get_human_resource_free",
            })
                .then(function (res) {
                    if (res["list_human_resource_free"].length > 0) {
                        self.list_human_resource_free = self.processMonthAvailableFree(res["list_human_resource_free"])
                    } else {
                        self.list_human_resource_free = res["list_human_resource_free"]
                    }
                });
            return $.when(def1, def2);
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
            for (let index = 0; index < arr.length; index++) {
                let sum = 0,
                    cnt = 0,
                    cntGreaterThanZero = 0;
                /*
                    January column's index in array is 7
                    December column's index in arrayy is 18
                 */
                for (let i = 7; i <= 18; i++) {
                    if (!arrCheckMonth[index].has(i - 6)) {
                        arr[index][i] = -1;
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
                        arrFree[index][i] = -1;
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
            let selection = document.getElementById("countriesDropdown");
            let filterSelection = selection.value.toUpperCase();

            var input, filter, table, tr, td, i, txtValue;
            input = document.getElementById("search_input");
            filter = input.value.toUpperCase();

            table = document.getElementById("human_resource_table");
            if (!table) return;
            tr = table.getElementsByTagName("tr");  

            for (i = 1; i < tr.length - value_row_not_search; i++) {
                td = tr[i];

                // project ALL in human
                if (filterSelection == 'ALL') {
                    if (td) {
                        txtValue = td.textContent || td.innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {
                            tr[i].style.display = '';
                        } else {
                            tr[i].style.display = 'none';
                        }
                    }
                }
                // project INTERNAL
                if (filterSelection == 'PROJECT INTERNAL') {
                    txtValue = td.textContent || td.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {
                        tr[i].style.display = '';
                    }                           
                    if (txtValue.toUpperCase().indexOf('ODC') > -1 || txtValue.toUpperCase().indexOf('PROJECT BASE') > -1 || txtValue.toUpperCase().indexOf(filter) <= -1) {
                        tr[i].style.display = 'none';
                    } 
                    // else if (txtValue.toUpperCase().indexOf(filter) <= -1) {
                    //     tr[i].style.display = 'none';
                    // }
                }

                // project BILLABLE
                if (filterSelection == 'PROJECT BILLABLE') {
                    txtValue = td.textContent || td.innerText;
                    if ((txtValue.toUpperCase().indexOf('ODC') > -1 || txtValue.toUpperCase().indexOf('PROJECT BASE') > -1) && txtValue.toUpperCase().indexOf(filter) > -1) {
                        tr[i].style.display = '';
                    } else {
                        tr[i].style.display = 'none';
                    }
                }
            }

            // if (filterSelection == 'INTERNAL') {
            //         for (i = 1; i < tr.length - value_row_not_search; i++) {
            //             td = tr[i];
            //             if (td) {
            //                 txtValue = td.textContent || td.innerText;
            //                 if (txtValue.toUpperCase().indexOf(filter) > -1) {
            //                     tr[i].style.display = '';
            //                 }                           
            //                 if ((txtValue.toUpperCase().indexOf('ODC') > -1 || txtValue.toUpperCase().indexOf('PROJECT BASE') > -1)) {
            //                     tr[i].style.display = 'none';
            //                 } 
            //                 else if (txtValue.toUpperCase().indexOf(filter) <= -1) {
            //                     tr[i].style.display = 'none';
            //                 }
                           
            //             }
            //         }
            // }
            // if (filterSelection == 'PROJECT BILLABLE') {
            //     for (i = 1; i < tr.length - value_row_not_search; i++) {
            //         td = tr[i];
            //         if (td) {
            //             txtValue = td.textContent || td.innerText;
            //             if ((txtValue.toUpperCase().indexOf('ODC') > -1 || txtValue.toUpperCase().indexOf('PROJECT BASE') > -1) && txtValue.toUpperCase().indexOf(filter) > -1) {
            //                 tr[i].style.display = '';
            //             } else {
            //                 tr[i].style.display = 'none';
            //             }
            //         }
            //     }
            // }
        },
        searchFunctionAvaiList: function(e) {
            const value_row_not_search = 1;
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
            var howManyCols = tbody.rows[1].cells.length;
            var total_member_company = document.getElementById("count_member_of_company");
            var arrEffortCompany = []
            // Start compute in column number seven
            for (var j = 7; j < howManyCols - 1; j++) {
                count_compute_available_member = self.compute_available_member(j);

                // count_number_row = self.compute_count_number_row(j);
                total_available_member.cells[j].innerText = count_compute_available_member;
                final = self.computeTableColumnTotal(j);
                arrEffortCompany.push(final);
                // avg = (total effort( > 0 and another N/A  )) / total members in column with effort another N/A 
                total_row.cells[j].innerText = parseFloat(final / count_compute_available_member).toFixed(2);
            }
            //count members of company with value from second column
            total_member_company.innerText = String( 'Current Month Active Members: ' +  self.compute_member_company());

            return arrEffortCompany;
        },

        compute_avg_all_res_rate: function () {
            let self = this;
            var final = 0;
            const row_value_effort = 1;
            const row_value_member = 2;
            var tbody = document.getElementById("human_reource_tbody");
            var total_row = tbody.rows[tbody.rows.length - row_value_member];
            var total_available_member = tbody.rows[tbody.rows.length -row_value_effort];
            var count_compute_available_member = 0;
            var howManyCols = tbody.rows[1].cells.length;

            // Start compute in column number seven
            for (var j = 7; j < howManyCols - 1; j++) {
                count_compute_available_member = self.compute_available_member_res_rate(j);

                // count_number_row = self.compute_count_number_row(j);
                total_available_member.cells[j].innerText = count_compute_available_member;
                final = self.computeTableColumnTotal(j);
                // avg = (total effort( > 0 and another N/A  )) / total members in column with effort another N/A 
                total_row.cells[j].innerText = parseFloat(final / count_compute_available_member).toFixed(2);
            }   
         
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

        compute_member_company: function (colNumber = 1) {
            var table = document.getElementById("human_resource_table");
            var howManyRows = 0;
            let count_members_of_company = 0;
            let listId = [];
            try {
                var howManyRows = table.rows.length;
                for (var i = 1; i < howManyRows - number_rows_not_count; i++) {
                    let row = table.rows[i];
                    let id_employee = table.rows[i].cells[1].innerText;
                    let parent_style = row.cells[colNumber].parentElement.style.display;

                    if (parent_style != 'none' && !listId.includes(id_employee)) {
                        count_members_of_company += 1
                        listId.push(id_employee);
                    }
                }
            } finally {
                return count_members_of_company;
            }
        },

        export_excel: function () {
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
            
            var result = [];
            var table =  document.getElementById("human_resource_table")
            var rows = table.rows;
            var cells, arrTemp;
          
            for (var i=0, iLen=rows.length; i<iLen; i++) {
                cells = rows[i].cells;
                arrTemp = [];
                if(rows[i].style.display != 'none') {
                    for (var j = 0, jLen = cells.length; j < jLen; j++) {
                        arrTemp.push(cells[j].textContent.replace(/\n/g,'').replace(/\r/g,' ').trim());
                    }
                }
              result.push(arrTemp);
            }

            let dataExport = [];

            for(let i=0; i <  result.length ; i ++) {
                if (result[i].length > 0) {
                    dataExport.push(result[i]);
                } 
            }
            var csvContent = ""
            dataExport.forEach(function(RowItem, RowIndex) {
                RowItem.forEach(function(ColItem, ColIndex) {
                csvContent += ColItem + ',';
                });
                csvContent += "\r\n";
            });
            var ele = document.createElement("A");
            ele.setAttribute("href",  "data:text/csv;charset=utf-8,%EF%BB%BF"+ encodeURI(csvContent) );
            ele.setAttribute("download","human_resource.csv");
            document.body.appendChild(ele);
            ele.click();
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

        replace_value_human_resource: function () {
            var table, cell_elements;
            table = document.getElementById('human_resource_table');
            if (!table) return;
            cell_elements = table.getElementsByTagName('td');
            for (var i = 0, len = cell_elements.length; i < len; i++) {

                if (cell_elements[i].innerHTML < 0) {
                    cell_elements[i].innerText = "NaN";
                }
                if (cell_elements[i].innerText == "" && cell_elements[i].className == "AVG_colum") {
                    cell_elements[i].innerText = "0";
                }
            }
        },

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
                for (var i = 1; i < howManyRows - 1; i++) {
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
            var tbody = document.getElementById("tbody_free_table");
            const number_column_calcu_in_table = 1
            var total_available_member = tbody.rows[tbody.rows.length - number_column_calcu_in_table];

            var howManyCols = tbody.rows[1].cells.length;
            var arrFreeEffort = [];
            var arrEffortHuman = self.compute_avg();
            var avgEffortInFreeTable = []

            //start calculator effort from  Fifth column => j = 5
            for (var j = 5 ; j < howManyCols; j++) {
                final = self.computeTableColumnTotalFree(j);
                arrFreeEffort.push(final);
            }

            for (let i = 0 ; i < arrFreeEffort.length ;i++ ) {
                if( arrEffortHuman[i] == 0) {
                    avgEffortInFreeTable[i] = 0;
                }
                else 
                    avgEffortInFreeTable[i] = (arrFreeEffort[i] /  arrEffortHuman[i]) * 100;
                //column start replace value from number four
                total_available_member.cells[i+4].innerText = avgEffortInFreeTable[i].toFixed(2);
            }
        },

        
        // filterTable : function () {
        //     var input, filter, table, tr, td, i, txtValue;
        //     const value_row_not_search = 4
        //     input = document.getElementById("countriesDropdown");
        //     filter = input.value.toUpperCase();
        //     table = document.getElementById("human_resource_table");
        //         if (!table) return;
        //     tr = table.getElementsByTagName("tr");
            
        //     if (filter == 'ALL') {
        //         for (i = 1; i < tr.length - value_row_not_search; i++) 
        //         {
        //             tr[i].style.display = '';
        //         }
        //     }

        //     if (filter ==  'PROJECT BILLABLE')  {
        //         for (i = 1; i < tr.length - value_row_not_search; i++) {
        //             td = tr[i];
        //             if (td) {
        //                 txtValue = td.textContent || td.innerText;
        //                 if (txtValue.toUpperCase().indexOf('ODC') > -1 || txtValue.toUpperCase().indexOf('PROJECT BASE') > -1){
        //                     tr[i].style.display = '';
        //                 } 
        //                 else {
        //                     tr[i].style.display = 'none';
        //                 }
        //             }
        //         }
        //     }
        //     if (filter ==  'INTERNAL')  {
        //         for (i = 1; i < tr.length - value_row_not_search; i++) {
        //             td = tr[i];
        //             if (td) {
        //                 txtValue = td.textContent || td.innerText;
        //                 if (txtValue.toUpperCase().indexOf('ODC') > -1 || txtValue.toUpperCase().indexOf('PROJECT BASE') > -1){
        //                     tr[i].style.display = 'none';
        //                 } 
        //                 else {
        //                     tr[i].style.display = '';
        //                 }
        //             }
        //         }
        //     }
               
        // },


    });

    core.action_registry.add('human_resource_template', HumanResourceTemplate);

    return HumanResourceTemplate;
});