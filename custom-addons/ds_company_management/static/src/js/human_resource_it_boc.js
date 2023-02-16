odoo.define('human_resource_it_boc.template', function(require) {
    "use strict";

    var AbstractAction = require("web.AbstractAction");
    var ajax = require("web.ajax");
    var core = require("web.core");
    var rpc = require("web.rpc");
    var ajax = require('web.ajax');
    // var Normalize = require('web.normalize');

    var hrmItBoc = AbstractAction.extend({
        template: 'hrm_it_boc_template',
        jsLibs: ["ds_company_management/static/src/js/lib/table2excel.js"],
        events: {
            "click .export_excel": "export_excel"
        },


        init: function(parent, action) {
            let month = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ];

            let columns = ["Company", "Department", "Project", "Project Type"] //"Employee", 
            columns = columns.concat(month)
            month.unshift("")
            this._super(parent, action);
            this.columns = columns
            this.hrmItBocData = [];
            this.listMonths = month;
            this.totalManMonthBillable = [];
            this.memberCurrentMonth = 0;
        },

        willStart: function() {
            let self = this;
            return $.when(ajax.loadLibs(this), this._super()).then(function() {
                return self.fetch_data();
            })
        },

        fetch_data: function() {
            let self = this;
            return this._rpc({
                model: "human.resource.management",
                method: "human_resource_it_boc_management"
            }).then(function(data) {
                // convert data effort to Man Month
                let hrms = data.data;
                let mmEstimate = data.total;

                // let contracts = data.contracts;
                let arrTotalMember = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
                let arrEstimate = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
                let arrActualMM = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
                let totalManMonthBillable = [];
                let dateCurrent = new Date();
                let currentYear = dateCurrent.getFullYear();
                let currentMonth = dateCurrent.getMonth();
                for (let index = 0; index < hrms.length; index++) {
                    let arrDuration = hrms[index].at(-1).split(","); // at(-1): get last item in hrms[index]
                    let arrDurationFinal = [];
                    self.computeDurationContract(arrDuration, arrDurationFinal, currentYear)

                    for (let i = 5; i < hrms[index].length - 1; i++) {
                        let monthIndex = i - 4;
                        let isActive = false;
                        for (let j = 0; j < arrDurationFinal.length; j++) {
                            if (monthIndex >= arrDurationFinal[j][0] && monthIndex <= arrDurationFinal[j][1]) {
                                isActive = true;
                                break;
                            }
                        }
                        if (isActive == false) {
                            hrms[index][i] = 'NaN';
                        } else {
                            if (hrms[index][i] > 0) {
                                hrms[index][i] = hrms[index][i] / 100;
                                arrTotalMember[i - 5] += hrms[index][i];
                            }
                        }
                    }
                    // debugger
                    // hrms[index].shift(); //remove first element from data hrms (employee_id)
                    hrms[index].splice(-1); // remove last element from data hrms (durationContract)
                }

                for (let index = 0; index < mmEstimate.length; index++) {
                    let positionMonth = mmEstimate[index][0] - 1
                    arrEstimate[positionMonth] += mmEstimate[index][1]
                }

                for(let index = 0; index < arrEstimate.length; index++) {
                    if (arrTotalMember[index] != 0) {
                        arrActualMM[index] = (arrEstimate[index] / arrTotalMember[index] * 100).toFixed(2);
                    }
                }

                arrEstimate.unshift("Contract Values");
                arrTotalMember.unshift("Total Member");
                arrActualMM.unshift("Bill Rate Based - Contract (%)");

                totalManMonthBillable.push(arrEstimate, arrTotalMember, arrActualMM);
                // console.log("data: ", data);
                // // console.log("contracts: ", contracts);
                // console.log("totalManMonthBillable: ", totalManMonthBillable);
                // console.log("arrEstimate: ", arrEstimate);
                // console.log("arrTotalMember: ", arrTotalMember);
                // console.log("arrActualMM: ", arrActualMM);
                // console.log("mmEstimate: ", mmEstimate);
                // console.log("hrms: ", hrms);
                self.hrmItBocData = hrms;
                self.totalManMonthBillable = totalManMonthBillable;
                self.memberCurrentMonth = arrTotalMember[currentMonth];
                
                // self.totalManMonthEstimate = arrEstimate;
                // self.totalEffort = arrTotalMember;
            })

        },

        start: function() {
            let searchValue = this.el.querySelector('#searchValue');
            searchValue.addEventListener('keyup', () => {
                // let content = searchValue.value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                this.searchAction(searchValue.value.toLowerCase());
            })
            this.actionSortTable();

            return this._super.apply(this, arguments);
        },
        searchAction: function (vals) {
            let hrmDatas = this.el.querySelector('.human_resource_template');
            let recordHrms = hrmDatas.getElementsByClassName('detail');
            let recordOverviews = hrmDatas.getElementsByClassName('value-over');
            // debugger
            let currentMonth = new Date().getMonth();
            let memberCurrentMonth = this.el.getElementsByClassName('member_current_month')[0];
            
            for (let i = 0; i < recordHrms.length; i++) {
                if (recordHrms[i].cells[0].innerText.toLowerCase().search(vals) == -1) {
                    recordHrms[i].classList.add('hrm_record_inactive');
                    recordHrms[i].classList.remove('hrm_record_active');
                } else {
                    recordHrms[i].classList.remove('hrm_record_inactive');
                    recordHrms[i].classList.add('hrm_record_active');
                }
            }

            for (let j = 1; j < recordOverviews.length; j++) {
                for (let item = 1; item < recordOverviews[j].cells.length; item++) {    //loop month column overview
                    if (j == 1) {
                        let result = 0;
                        for (let i = 0; i < recordHrms.length; i ++) {
                            // if (recordHrms[i].className.search('hrm_record_active') != -1) {
                            if (recordHrms[i].classList.contains('hrm_record_active')) {
                                let text = recordHrms[i].cells[item + 4].innerText;
                                if (text != 'NaN') {
                                    result += parseFloat(text);
                                }
                            }
                        }
                        recordOverviews[j].cells[item].innerText = result;
                    } else if (j == 2) {
                        let member = parseFloat(recordOverviews[j - 1].cells[item].innerText);
                        let contractVals = parseFloat(recordOverviews[0].cells[item].innerText);
                        
                        recordOverviews[j].cells[item].innerText = member > 0 ? (contractVals/ member * 100).toFixed(2) : 0;
                    }
                }
            }

            memberCurrentMonth.innerText = recordOverviews[1].cells[currentMonth].innerText;
        },

        computeDurationContract: function(arrDuration, arrDurationFinal, currentYear) {
            for (let item = 0; item < arrDuration.length; item++) {
                let dateTimes = arrDuration[item].split(" "); // dateTimes have 4 item [startMonth, startYear, endMonth, endYear]
                let arrTemp = [];
                if (parseInt(dateTimes[1]) < currentYear) {
                    arrTemp.push(1);
                    if (parseInt(dateTimes[3]) == currentYear) {
                        arrTemp.push(parseInt(dateTimes[2]));
                    } else {
                        arrTemp.push(12);
                    }
                } else { // startYear = CurrentYear
                    arrTemp.push(parseInt(dateTimes[0]));
                    if (parseInt(dateTimes[3]) == currentYear) {
                        arrTemp.push(parseInt(dateTimes[2]));
                    } else {
                        arrTemp.push(12);
                    }
                }

                if (arrTemp.length > 0) {
                    arrDurationFinal.push(arrTemp);
                }
            }
        },

        actionSortTable: function() {
            const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;
            const comparer = (idx, asc) => (a, b) => ((v1, v2) => 
                v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
                )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));

            const getCellValueNameEmployee = (tr, idx) => tr.children[idx].innerText.slice(tr.children[idx].innerText.lastIndexOf(' ') + 1)
                                        || tr.children[idx].textContent.slice(tr.children[idx].textContent.lastIndexOf(' ') + 1);
            const comparerNameEmployee = (idx, asc) => (a, b) => ((v1, v2) => v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2))
                (getCellValueNameEmployee(asc ? a : b, idx), getCellValueNameEmployee(asc ? b : a, idx));

            let colsHeader = this.el.querySelectorAll('th.header_human_table');
            let colsName = this.el.querySelectorAll('th.header_human_table_name');
            this.contentActionSort(colsHeader, comparer);
            this.contentActionSort(colsName, comparerNameEmployee);
        },

        contentActionSort: function (cols, compareAction) {
            cols.forEach(col => col.addEventListener('click', (() => {
                let table = col.closest('tbody');
                Array.from(table.querySelectorAll('tr.detail'))
                .sort(compareAction(Array.from(col.parentNode.children).indexOf(col), this.asc = !this.asc))
                .forEach(tr => table.appendChild(tr));
            })))
        },

        export_excel: function () {
            Table2Excel.extend((cell, cellText) => {
                return $(cell).attr('type') == 'string' ? {
                    t: 's',
                    v: cellText
                } : null;
            });
            let tblExport = new Table2Excel();
            let dataRecords = this.el.getElementsByClassName('human_resource_itboc')[0].cloneNode(true);
            let record = dataRecords.querySelectorAll('tr')

            for (let i = 1; i < record.length; i++) {
                if (record[i].classList.contains('hrm_record_inactive')) {
                    record[i].remove();
                }
            }
            document.body.appendChild(dataRecords);
            tblExport.export(dataRecords);
            dataRecords.remove();
        }


    });

    core.action_registry.add('human_resource_it_boc', hrmItBoc);
    return hrmItBoc;
});