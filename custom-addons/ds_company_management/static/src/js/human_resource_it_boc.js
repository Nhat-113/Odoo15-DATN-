odoo.define('human_resource_it_boc.template', function(require) {
    "use strict";

    var AbstractAction = require("web.AbstractAction");
    var ajax = require("web.ajax");
    var core = require("web.core");
    var rpc = require("web.rpc");
    var ajax = require('web.ajax');
    // var Normalize = require('web.normalize');

    const IndexMonth = 5; // cols start for list Month from HRM data record

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

            let columns = ["Employee", "Company", "Department", "Project", "Project Type"]
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
                let mmEstimate = data.overview;
                let memberCompany = data.total_member_company;

                let arrTotalMM = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
                let arrEstimate = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
                let arrActualMM = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
                let arrTotalMember = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
                let arrEffectiveRate = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
                let totalManMonthBillable = [];
                let dateCurrent = new Date();
                let currentYear = dateCurrent.getFullYear();
                let currentMonth = dateCurrent.getMonth() + 1;

                // handle total member company
                for(let i = 0; i < memberCompany.length; i++) {
                    arrTotalMember[memberCompany[i][0] - 1] = memberCompany[i][1];
                }
                // handle Human resource data
                for (let index = 0; index < hrms.length; index++) {
                    let arrDuration = hrms[index].at(-1).split(","); // at(-1): get last item in hrms[index]
                    let arrDurationFinal = [];
                    self.computeDurationContract(arrDuration, arrDurationFinal, currentYear)

                    for (let i = IndexMonth; i < hrms[index].length - 1; i++) {
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
                                hrms[index][i] = (parseFloat(hrms[index][i]) / 100).toFixed(2);
                                arrTotalMM[i - IndexMonth] += parseFloat(hrms[index][i]);
                            }
                        }
                    }
                    // hrms[index].shift(); //remove first element from data hrms (employee_id)
                    hrms[index].splice(-1); // remove last element from data hrms (durationContract)
                }

                // handle Contract values (Man month from project billable)
                for (let index = 0; index < mmEstimate.length; index++) {
                    let positionMonth = mmEstimate[index][0] - 1
                    arrEstimate[positionMonth] += mmEstimate[index][1]
                }

                for(let index = 0; index < arrEstimate.length; index++) {
                    if (arrTotalMember[index] != 0) {
                        arrActualMM[index] = (arrEstimate[index] / arrTotalMember[index] * 100).toFixed(2);
                        if (arrTotalMM[index] != 0) {
                            arrEffectiveRate[index] = (arrActualMM[index] / ((arrTotalMM[index] *100) / (arrTotalMember[index] * 100) * 100)).toFixed(3);
                        }
                    }
                }

                arrEstimate.unshift("Contract Values");
                arrTotalMember.unshift("Total Member Company");
                arrTotalMM.unshift("Total Member Billable");
                arrActualMM.unshift("Bill Rate Based - Contract (%)");
                arrEffectiveRate.unshift("Res Usage Effective Rate (%)");

                totalManMonthBillable.push(arrEstimate, arrTotalMember, arrTotalMM, arrActualMM, arrEffectiveRate);

                self.hrmItBocData = hrms;
                self.totalManMonthBillable = totalManMonthBillable;
                self.memberCurrentMonth = arrTotalMember[currentMonth];
            })

        },

        start: function() {
            let searchValue = this.el.querySelector('#searchValue');
            searchValue.addEventListener('keyup', () => {
                // let content = searchValue.value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                let vals = searchValue.value.toLowerCase();
                vals = this.recursiveValidateValsInput(vals);
                this.searchAction(vals);
            })
            this.actionSortTable();

            return this._super.apply(this, arguments);
        },

        recursiveValidateValsInput: function (vals) {
            const specialChars = /[\\]/;
            if (specialChars.test(vals) == true) { // check string have special characters ?
                vals = vals.replace("\\", "");
                return this.recursiveValidateValsInput(vals);
            } else {
                return vals;
            }
        },

        searchAction: function (vals) {
            let hrmDatas = this.el.querySelector('.human_resource_template');
            let recordHrms = hrmDatas.getElementsByClassName('detail');
            let recordOverviews = hrmDatas.getElementsByClassName('value-over');
            let currentMonth = new Date().getMonth() + 1;
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

            for (let j = 2; j < recordOverviews.length; j++) {
                for (let item = 1; item < recordOverviews[j].cells.length; item++) {    //loop month column overview
                    if (j == 2) {
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
                    } else if (j == 4) {
                        let actualMM = parseFloat(recordOverviews[j - 1].cells[item].innerText)
                        let totalEffortRate = parseFloat(recordOverviews[j - 2].cells[item].innerText) * 100;
                        let memberCompany = parseFloat(recordOverviews[j - 3].cells[item].innerText) * 100;
                        // let contractVals = parseFloat(recordOverviews[0].cells[item].innerText);
                        
                        recordOverviews[j].cells[item].innerText = memberCompany > 0 && totalEffortRate > 0 ? 
                                                                    (actualMM / ((totalEffortRate/ memberCompany) * 100)).toFixed(2) : 0;


                    } else {
                        break;
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