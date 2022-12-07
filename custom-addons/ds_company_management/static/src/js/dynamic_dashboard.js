odoo.define("odoo_dynamic_dashboard.Dashboard", function(require) {
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
    var AbstractAction = require("web.AbstractAction");
    var ajax = require("web.ajax");
    var field_utils = require("web.field_utils");
    var core = require("web.core");
    var rpc = require("web.rpc");
    var _t = core._t;
    var QWeb = core.qweb;

    const { useRef, useSubEnv } = hooks;
    var AbstractAction = require("web.AbstractAction");
    var ajax = require("web.ajax");
    var core = require("web.core");
    var rpc = require("web.rpc");
    var web_client = require("web.web_client");
    var _t = core._t;
    var QWeb = core.qweb;
    var backgroundColorRandom = ['#6869AC', '#4CAF50', '#00ACC1', '#FFB300', '#E53935', '#6060EC', '#119989', '#E53935', '#00B981']

    var currentTime = new Date()
    var currentYear = currentTime.getFullYear()
    
    var DynamicDashboard = AbstractAction.extend({
        template: "dynamic_bom_dashboard",
        jsLibs: ["/ds_company_management/static/src/js/lib/chart.js"],

        events: {
            "click #chart_employee": "swap_menu",
            "click #chart_project": "swap_menu",
        },

        swap_menu: function(events) {
            var i, tabcontent, tablinks, targetClass, target;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
            }
            tablinks = document.getElementsByClassName("tablinks_dashboard");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }

            target = events.target;
            targetClass = target.className.includes("btn-chart_employee") ?
                "data_employee_chart" :
                target.className.includes("btn-chart_project") ?
                "chart_project" :
                "chart_company_revenue";
            document.querySelector(`.${targetClass}`).removeAttribute("style");
            events.currentTarget.className += " active";
        },

        init: function(parent, context) {
            this.action_id = context["id"];
            this._super(parent, context);
        },
        start: function() {
            var self = this;
            this.set("title", "Dashboard Bom");
            // setTimeout(() => {
            //     self.denyClick();
            // }, 500);
            setTimeout(() => {
                self.jobPositionPierChart();
                self.contractBarChart();
                self.payrollDashboard();
            }, 1000);
            setTimeout(() => {
                self.projectTypePierChart();
                self.chartProjectFree();
                self.chartProjectAvg();
                self.chartProjectBill();
                self.chartProjectNotBill();
                self.chartPayrollRevenueFollowMonth();
            }, 2500);
            setTimeout(() => {
                self.chartCompanyAvg();
            }, 3000);
        },

        willStart: function() {
            var self = this;
            return $.when(ajax.loadLibs(this), this._super()).then(function() {
                return self.fetch_data();
            });
        },

        fetch_data: function() {},

        // denyClick: function() {
        //     const box = document.getElementById('deny-click');
        //         if (!box)
        //             return
        //     var  loading_img= document.getElementById('loading-img-dashboard');
        //         if (!loading_img)
        //                 return
        //     loading_img.style.display = "none";
        //     box.removeAttribute('style');
        // },

        projectTypePierChart: function() {
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_project_status",
                })
                .then(function(data) {
                    const sum_status_project = data.reduce((accumulator, object) => {
                        return accumulator + object.value;
                      }, 0);

                    for (let i  = 0 ; i < data.length ; i ++ ) {
                        data[i].value =   (data[i].value / sum_status_project) * 100
                    }
                    
                    var ele = document.getElementById("project_status");
                    if (!ele)
                        return
                    if (Chart.getChart("project_status")){
                        Chart.getChart("project_status").destroy();
                    }
                    let arrayColor = []
                    const ctx = ele.getContext("2d");
                    const project_status = new Chart(ctx, {
                        type: "pie",
                        data: {
                            labels: [],
                            datasets: [{
                                label: "Project Status Chart",
                                data: [],
                                backgroundColor: arrayColor,
                                borderColor: arrayColor,
                                borderWidth: 0,     
                                showLine: false   
                            }, ],
                        },
                        options: {
                            scales: {
                                // yAxes: {
                                //     ticks: {
                                //         beginAtZero: true,
                                //     },
                                //     gridLines: {
                                //         drawOnChartArea: false
                                //     }
                        
                                // },
                                // xAxes: {
                                //     gridLines: {
                                //         drawOnChartArea: false
                                //     }
                        
                                // },
                            },
                        },
                    });
                    for (let i = 0; i < data.length; i++) {
                        data[i].label = data[i].label.replace("_", " ").replace(/(^\w|\s\w)/g, m => m.toUpperCase());
                    }
                    const dataTemp = project_status.data;
                    
                   
                    for (let i = 0; i < data.length; i++) {
                        dataTemp.labels.push(data[i].label);
                        dataTemp.datasets[0].data.push(data[i].value);
                    }

                    for (let i = 0; i < dataTemp.labels.length; i ++) {

                        if (dataTemp.labels[i] == 'Off Track' ) {
                            arrayColor[i] = '#6869AC'
                        }
                        if (dataTemp.labels[i] == 'At Risk' ) {
                             arrayColor[i] = '#4CAF50'
                        }
                        if (dataTemp.labels[i] == 'On Track' ) {
                             arrayColor[i] = '#00ACC1'
                        }
                        if (dataTemp.labels[i] == 'Missing Resource' ) {
                             arrayColor[i] = '#FFB300'
                        }
                    }

                    project_status.data.labels = dataTemp.labels;
                    project_status.data.datasets[0].data = dataTemp.datasets[0].data;
                    project_status.update();
                });
        },
        jobPositionPierChart: function() {
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_position_employee",
                })
                .then(function(data) {
                    var data_employee = data;
                    var ele = document.getElementById("job-position");
                    if (!ele)
                        return
                    if (Chart.getChart("job-position")){
                        Chart.getChart("job-position").destroy();
                    }
                    const ctx = ele.getContext("2d");
                    // Chart.defaults.scales.linear.min = 0;
                    const jobPosition = new Chart(ctx, {
                        type: "bar",
                        data: {
                            labels: [],
                            datasets: [{
                                label: "Job Position",
                                data: [],
                                backgroundColor: backgroundColorRandom,
                                borderColor: backgroundColorRandom,
                                borderWidth: 1,
                            }, ],
                        },
                        options: {
                            scales: {
                                yAxes: {
                                    ticks: {
                                        beginAtZero: true,
                                    },
                                },
                            },
                            plugins: {
                                legend: false // Hide legend
                            },
                        },
                    });
                    const dataTemp = jobPosition.data;
                    for (let i = 0; i < data_employee.length; i++) {
                        dataTemp.labels.push(data_employee[i].label);
                        dataTemp.datasets[0].data.push(data_employee[i].value);
                    }

                    jobPosition.data.labels = dataTemp.labels;
                    jobPosition.data.datasets[0].data = dataTemp.datasets[0].data;
                    jobPosition.update();
                });
        },
        chartProjectBill: function() {
            let self = this;
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_effort_human_resource",
                })
                .then(function(data) {
                    if (data.length > 0)
                    {
                        var data_employee = self.valueProjectBill(data);
                    }
                    var ele = document.getElementById("chart_ODC");
                    if (!ele)
                        return
                    if (Chart.getChart("chart_ODC")){
                        Chart.getChart("chart_ODC").destroy();
                    }
                    const ctx = ele.getContext("2d");

                    const chartODC = new Chart(ctx, {
                        type: "line",
                        data: {
                            labels: ["Jan","Feb","Mar","Apr", "May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
                            datasets: [{
                                label: "Project Billable",
                                data: [],
                                backgroundColor: ["#6869AC"],
                                borderColor: ["#6869AC"],
                                borderWidth: 2,
                            }, ],
                        },
                        options: {
                            scales: {
                                yAxes: {
                                    ticks: {
                                        beginAtZero: true,
                                    },
                                },
                            },
                            plugins: {
                                legend: false // Hide legend
                            },
                        },
                    });
                    const dataTemp = chartODC.data;
                    if(!data_employee)
                        return

                    for (let i = 0; i < chartODC.data.labels.length; i++) {
                        chartODC.data.labels[i]  = chartODC.data.labels[i] + ' ' + currentYear;
                    }
                    for (let i = 0; i <= Object.keys(data_employee).length; i++) {
                        dataTemp.datasets[0].data.push(data_employee[i]);
                    }
                    chartODC.data.datasets[0].data = dataTemp.datasets[0].data;
                    chartODC.update();
                });
        },

        valueProjectBill: function(arr) {
            const dimensions = [arr.length, arr[0].length];
            let arrCheckMonth = new Array();

            arr.forEach((childArr) => {
                if (childArr[dimensions[1] - 2] != null) {
                    let arrStartDate = childArr[dimensions[1] - 2].split(",");
                    let arrEndDate = childArr[dimensions[1] - 1].split(",");
                    let contractAvailableSet = new Set();
                    for (let index = 0; index < arrStartDate.length; index++) {
                        if (
                            parseInt(arrStartDate[index].split("-")[1]) <
                            new Date().getFullYear() &&
                            parseInt(arrEndDate[index].split("-")[1]) == 0
                        ) {
                            for (let i = 1; i <= 12; i++) {
                                contractAvailableSet.add(i);
                            }
                        } else if (
                            parseInt(arrStartDate[index].split("-")[1]) ==
                            new Date().getFullYear()
                        ) {
                            if (
                                parseInt(arrStartDate[index].split("-")[0]) <=
                                parseInt(arrEndDate[index].split("-")[0]) &&
                                parseInt(arrEndDate[index].split("-")[0]) != 0
                            ) {
                                for (
                                    let i = parseInt(arrStartDate[index].split("-")[0]); i <= parseInt(arrEndDate[index].split("-")[0]); i++
                                ) {
                                    contractAvailableSet.add(i);
                                }
                            } else if (parseInt(arrEndDate[index].split("-")[0]) == 0) {
                                for (
                                    let i = parseInt(arrStartDate[index].split("-")[0]); i <= 12; i++
                                ) {
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
                    cnt = 0;

                for (let i = 2; i <= 13; i++) {
                    if (!arrCheckMonth[index].has(i - 1)) {
                        arr[index][i] = -1;
                    } else {
                        sum += arr[index][i];
                        cnt++;
                    }
                }
                arr[index][14] =
                    cnt > 0 ? Number.parseFloat(sum / cnt).toFixed(2) : "NaN";
            }

            let count_row_array = arr.length;
            var effort_project_bill = [];
            var avg_effort_project_bill = [];
            var effort_company = [];
            for (let i = 0; i < 14; i++) {
                var set_arr = new Set()
                for (let j = 0; j < count_row_array; j++) {
                    if ((arr[j][1] == "Project Base" || arr[j][1] == "ODC") && arr[j][i] >= 0) {
                        effort_project_bill[i] = (effort_project_bill[i] || 0) + parseFloat(arr[j][i]);
                    }

                    if(arr[j][i] >= 0) {
                        set_arr.add(arr[j][0])
                    }
                }
                effort_company.push(set_arr.size * 100)
            }
            effort_project_bill = Array.from(effort_project_bill, (item) => item || 0);

            effort_project_bill.splice(0, 2);
            effort_company.splice(0, 2);

           for(let i = 0; i < effort_project_bill.length ; i ++) {
                avg_effort_project_bill[i] = (effort_project_bill[i] / effort_company[i]) * 100
            }

            var rv = {};
            for (var i = 0; i <= avg_effort_project_bill.length; ++i)
                rv[i] = avg_effort_project_bill[i];
            return rv;
        },

        chartProjectNotBill: function() {
            let self = this;
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_effort_human_resource",
                })
                .then(function(data) {
                    if (data.length > 0)
                    {
                        var data_employee = self.valueProjectNotBill(data);
                    }
                    var ele = document.getElementById("chart_project_base");
                    if (Chart.getChart("chart_project_base")){
                        Chart.getChart("chart_project_base").destroy();
                    }
                    if (!ele)
                        return
                    const ctx = ele.getContext("2d");

                    const chartProjectBase = new Chart(ctx, {
                        type: "line",
                        data: {
                            labels: ["Jan","Feb","Mar","Apr", "May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
                            datasets: [{
                                label: "Project Internal",
                                data: [],
                                backgroundColor: ['#6869AC'],
                                borderColor: ['#6869AC'],
                                borderWidth: 2,
                            }, ],
                        },
                        options: {
                            scales: {
                                yAxes: {
                                    ticks: {
                                        beginAtZero: true,
                                    },
                                },
                            },
                            plugins: {
                                legend: false // Hide legend
                            },
                        },
                    });
                    const dataTemp = chartProjectBase.data;
                    if(!data_employee)
                        return
                    for (let i = 0; i < chartProjectBase.data.labels.length; i++) {
                        chartProjectBase.data.labels[i]  = chartProjectBase.data.labels[i] + ' ' + currentYear;
                    }
                    for (let i = 0; i <= Object.keys(data_employee).length; i++) {
                        dataTemp.datasets[0].data.push(data_employee[i]);
                    }
                    chartProjectBase.data.datasets[0].data = dataTemp.datasets[0].data;
                    chartProjectBase.update();
                });
        },

        valueProjectNotBill: function(arr) {
            const dimensions = [arr.length, arr[0].length];
            let arrCheckMonth = new Array();

            arr.forEach((childArr) => {
                if (childArr[dimensions[1] - 2] != null) {
                    let arrStartDate = childArr[dimensions[1] - 2].split(",");
                    let arrEndDate = childArr[dimensions[1] - 1].split(",");
                    let contractAvailableSet = new Set();
                    for (let index = 0; index < arrStartDate.length; index++) {
                        if (
                            parseInt(arrStartDate[index].split("-")[1]) <
                            new Date().getFullYear() &&
                            parseInt(arrEndDate[index].split("-")[1]) == 0
                        ) {
                            for (let i = 1; i <= 12; i++) {
                                contractAvailableSet.add(i);
                            }
                        } else if (
                            parseInt(arrStartDate[index].split("-")[1]) ==
                            new Date().getFullYear()
                        ) {
                            if (
                                parseInt(arrStartDate[index].split("-")[0]) <=
                                parseInt(arrEndDate[index].split("-")[0]) &&
                                parseInt(arrEndDate[index].split("-")[0]) != 0
                            ) {
                                for (
                                    let i = parseInt(arrStartDate[index].split("-")[0]); i <= parseInt(arrEndDate[index].split("-")[0]); i++
                                ) {
                                    contractAvailableSet.add(i);
                                }
                            } else if (parseInt(arrEndDate[index].split("-")[0]) == 0) {
                                for (
                                    let i = parseInt(arrStartDate[index].split("-")[0]); i <= 12; i++
                                ) {
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
                    cnt = 0;

                for (let i = 2; i <= 13; i++) {
                    if (!arrCheckMonth[index].has(i - 1)) {
                        arr[index][i] = -1;
                    } else {
                        sum += arr[index][i];
                        cnt++;
                    }
                }
                arr[index][14] =
                    cnt > 0 ? Number.parseFloat(sum / cnt).toFixed(2) : "NaN";
            }

            let count_row_array = arr.length;
            var effort_project_not_bill = [];
            var avg_effort_project_bill = [];
            var effort_company = [];
            for (let i = 0; i < 14; i++) {
                var set_arr = new Set()
                for (let j = 0; j < count_row_array; j++) {
                    if ((arr[j][1] == "Internal") && arr[j][i] >= 0) {
                        effort_project_not_bill[i] = (effort_project_not_bill[i] || 0) + parseFloat(arr[j][i]);
                    }

                    if(arr[j][i] >= 0) {
                        set_arr.add(arr[j][0]);
                    }
                }
                effort_company.push(set_arr.size * 100)
            }
            effort_project_not_bill = Array.from(effort_project_not_bill, (item) => item || 0);
            effort_project_not_bill.splice(0, 2);
            effort_company.splice(0, 2);
           for(let i = 0; i < effort_project_not_bill.length ; i ++) {
                avg_effort_project_bill[i] = (effort_project_not_bill[i] / effort_company[i]) * 100
            }

            var rv = {};
            for (var i = 0; i <= avg_effort_project_bill.length; ++i)
                rv[i] = avg_effort_project_bill[i];
            return rv;
        },

        chartProjectFree: function() {
            let self = this;
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_effort_human_resource",
                })
                .then(function(data) {
                    if (data.length > 0)
                    {
                        var data_employee = self.valueProjectFree(data);
                    }
                    var ele = document.getElementById("chart_project_free");
                    if (!ele)
                        return

                    if (Chart.getChart("chart_project_free")){
                        Chart.getChart("chart_project_free").destroy();
                    }
                    const ctx = ele.getContext("2d");

                    const chartProjectInternal = new Chart(ctx, {
                        type: "line",
                        data: {
                            labels: ["Jan","Feb","Mar", "Apr", "May","Jun", "Jul", "Aug","Sep","Oct","Nov", "Dec",],
                            datasets: [{
                                label: "Project Available",
                                data: [],
                                backgroundColor: ["#6869AC"],
                                borderColor: ["#6869AC"],
                                borderWidth: 2,
                            }, ],
                        },
                        options: {
                            scales: {
                                yAxes: {
                                    ticks: {
                                        beginAtZero: true,
                                    },
                                },
                            },
                            plugins: {
                                legend: false // Hide legend
                            },
                        },
                    });
                    const dataTemp = chartProjectInternal.data;
                    if(!data_employee)
                        return
                    for (let i = 0; i < chartProjectInternal.data.labels.length; i++) {
                        chartProjectInternal.data.labels[i]  = chartProjectInternal.data.labels[i] + ' ' + currentYear;
                    }
                    for (let i = 0; i <= Object.keys(data_employee).length; i++) {
                        dataTemp.datasets[0].data.push(data_employee[i]);
                    }
                    chartProjectInternal.data.datasets[0].data =
                        dataTemp.datasets[0].data;
                    chartProjectInternal.update();
                });
        },

        valueProjectFree: function(arr) {
            const dimensions = [arr.length, arr[0].length];
            let arrCheckMonth = new Array();

            arr.forEach((childArr) => {
                if (childArr[dimensions[1] - 2] != null) {
                    let arrStartDate = childArr[dimensions[1] - 2].split(",");
                    let arrEndDate = childArr[dimensions[1] - 1].split(",");
                    let contractAvailableSet = new Set();
                    for (let index = 0; index < arrStartDate.length; index++) {
                        if (
                            parseInt(arrStartDate[index].split("-")[1]) <
                            new Date().getFullYear() &&
                            parseInt(arrEndDate[index].split("-")[1]) == 0
                        ) {
                            for (let i = 1; i <= 12; i++) {
                                contractAvailableSet.add(i);
                            }
                        } else if (
                            parseInt(arrStartDate[index].split("-")[1]) ==
                            new Date().getFullYear()
                        ) {
                            if (
                                parseInt(arrStartDate[index].split("-")[0]) <=
                                parseInt(arrEndDate[index].split("-")[0]) &&
                                parseInt(arrEndDate[index].split("-")[0]) != 0
                            ) {
                                for (
                                    let i = parseInt(arrStartDate[index].split("-")[0]); i <= parseInt(arrEndDate[index].split("-")[0]); i++
                                ) {
                                    contractAvailableSet.add(i);
                                }
                            } else if (parseInt(arrEndDate[index].split("-")[0]) == 0) {
                                for (
                                    let i = parseInt(arrStartDate[index].split("-")[0]); i <= 12; i++
                                ) {
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
                    cnt = 0;

                for (let i = 2; i <= 13; i++) {
                    if (!arrCheckMonth[index].has(i - 1)) {
                        arr[index][i] = -1;
                    } else {
                        sum += arr[index][i];
                        cnt++;
                    }
                }
                arr[index][14] =
                    cnt > 0 ? Number.parseFloat(sum / cnt).toFixed(2) : "NaN";
            }

            let count_row_array = arr.length;
            var effort_project_total = [];
            var avg_effort_project_not_free = [];
            var effort_company = [];
            for (let i = 0; i < 14; i++) {
                var set_arr = new Set()
                for (let j = 0; j < count_row_array; j++) {
                    if (arr[j][i] >= 0) {
                        effort_project_total[i] = (effort_project_total[i] || 0) + parseFloat(arr[j][i]);
                    }

                    if(arr[j][i] >= 0) {
                        set_arr.add(arr[j][0])
                    }
                }
                effort_company.push(set_arr.size * 100)
            }

            effort_project_total = Array.from(effort_project_total, (item) => item || 0);
            effort_project_total.splice(0, 2);
            effort_company.splice(0, 2);

            for(let i = 0; i < effort_project_total.length ; i ++) {
                    avg_effort_project_not_free[i] = ( (effort_company[i] - effort_project_total[i]) / effort_company[i] ) * 100
            }
            var rv = {};
            for (var i = 0; i <= avg_effort_project_not_free.length; ++i)
                rv[i] = avg_effort_project_not_free[i];
            return rv;
        },

        chartProjectAvg: function() {
            let self = this;
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_effort_human_resource",
                })
                .then(function(data) {
                    if (data.length > 0)
                        {
                        var data_employee = self.valueProjectAVG(data);
                    }
                    var ele = document.getElementById("chart_avg_project");
                    if (!ele)
                        return
                    if (Chart.getChart("chart_avg_project")){
                        Chart.getChart("chart_avg_project").destroy();
                    }
                    const ctx = ele.getContext("2d");

                    const chartAvgProject = new Chart(ctx, {
                        type: "pie",
                        data: {
                            labels: [ "Internal", "Billable", "Available"],
                            datasets: [{
                                label: "Project Avg",
                                data: [],
                                backgroundColor:backgroundColorRandom ,
                                borderColor: backgroundColorRandom,
                                borderWidth: 1,
                            }, ],
                        },
                        options: {
                            scales: {
                                // yAxes: {
                                //     gridLines: {
                                //         drawBorder: false,
                                //     }
                                // },
                                // xAxes: {
                                //     gridLines: {
                                //         drawBorder: false,
                                //     }
                                // },
                            },
                        },
                    });
                    const dataTemp = chartAvgProject.data;
                    if(!data_employee)
                        return
                    for (let i = 0; i <= Object.keys(data_employee).length; i++) {
                        dataTemp.datasets[0].data.push(data_employee[i]);
                    }
                    chartAvgProject.data.datasets[0].data = dataTemp.datasets[0].data;
                    chartAvgProject.update();
                });
        },

        valueProjectAVG: function(arr) {
            const dimensions = [arr.length, arr[0].length];
            let arrCheckMonth = new Array();

            arr.forEach((childArr) => {
                if (childArr[dimensions[1] - 2] != null) {
                    let arrStartDate = childArr[dimensions[1] - 2].split(",");
                    let arrEndDate = childArr[dimensions[1] - 1].split(",");
                    let contractAvailableSet = new Set();
                    for (let index = 0; index < arrStartDate.length; index++) {
                        if (
                            parseInt(arrStartDate[index].split("-")[1]) <
                            new Date().getFullYear() &&
                            parseInt(arrEndDate[index].split("-")[1]) == 0
                        ) {
                            for (let i = 1; i <= 12; i++) {
                                contractAvailableSet.add(i);
                            }
                        } else if (
                            parseInt(arrStartDate[index].split("-")[1]) ==
                            new Date().getFullYear()
                        ) {
                            if (
                                parseInt(arrStartDate[index].split("-")[0]) <=
                                parseInt(arrEndDate[index].split("-")[0]) &&
                                parseInt(arrEndDate[index].split("-")[0]) != 0
                            ) {
                                for (
                                    let i = parseInt(arrStartDate[index].split("-")[0]); i <= parseInt(arrEndDate[index].split("-")[0]); i++
                                ) {
                                    contractAvailableSet.add(i);
                                }
                            } else if (parseInt(arrEndDate[index].split("-")[0]) == 0) {
                                for (
                                    let i = parseInt(arrStartDate[index].split("-")[0]); i <= 12; i++
                                ) {
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
                    cnt = 0;

                for (let i = 2; i <= 13; i++) {
                    if (!arrCheckMonth[index].has(i - 1)) {
                        arr[index][i] = -1;
                    } else {
                        sum += arr[index][i];
                        cnt++;
                    }
                }
                arr[index][14] =
                    cnt > 0 ? Number.parseFloat(sum / cnt).toFixed(2) : "NaN";
            }

            let count_row_array = arr.length;
            var effort_company = [];
            var sum_not_bill = [];
            var sum_bill = [];
            var sum_null = [];

            for (let i = 0; i < 14; i++) {
                var set_arr = new Set()
                for (let j = 0; j < count_row_array; j++) {
                    if ( (arr[j][1] == "Internal") && arr[j][i] >= 0) {
                        sum_not_bill[i] = (sum_not_bill[i] || 0) + parseFloat(arr[j][i]);
                    }

                    if ( (arr[j][1] == "ODC" || arr[j][1] == "Project Base") && arr[j][i] >= 0) {
                        sum_bill[i] = (sum_bill[i] || 0) + parseFloat(arr[j][i]);
                    }
                    if ( (arr[j][1] == null) && arr[j][i] >= 0) {
                        sum_null[i] = (sum_null[i] || 0) + parseFloat(arr[j][i]);
                    }

                    if(arr[j][i] >= 0) {
                        set_arr.add(arr[j][0])
                    }
                }
                effort_company.push(set_arr.size * 100)
            }

            sum_not_bill = Array.from(sum_not_bill, (item) => item || 0);
            sum_bill = Array.from(sum_bill, (item) => item || 0);
            sum_null = Array.from(sum_null, (item) => item || 0);

            sum_not_bill.splice(0, 2)
            sum_bill.splice(0, 2)
            sum_null.splice(0, 2)
            effort_company.splice(0, 2)

            effort_company = Array.from(effort_company, (item) => item || 0);

            var sum_value_not_bill, sum_value_bill, total_effort_company, sum_value_free

            sum_value_not_bill = sum_not_bill.reduce((a, b) => a + b, 0);
            sum_value_bill = sum_bill.reduce((a, b) => a + b, 0);
            // sum_value_null = sum_null.reduce((a, b) => a + b, 0);
            total_effort_company = effort_company.reduce((a, b) => a + b, 0);
            sum_value_free = total_effort_company - (sum_value_not_bill + sum_value_bill);


            var effort_avg_value_not_bill = (sum_value_not_bill / total_effort_company) * 100;
            var effort_avg_value_bill = (sum_value_bill / total_effort_company) * 100;
            // var effort_avg_value_null = (sum_value_null / total_effort_company) * 100;
            var effort_avg_sum_value_free = (sum_value_free / total_effort_company) * 100;

            let avg = [effort_avg_value_not_bill, effort_avg_value_bill, effort_avg_sum_value_free];

            var avgProjectObj = {};
            for (var i = 0; i <= avg.length; ++i)
                avgProjectObj[i] = avg[i];

            return avgProjectObj;
        },

        chartCompanyAvg: function() {
            let self = this;
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_revenue_company",
                })
                .then(function(data) {
                    var speedCanvas = document.getElementById("chart_company_revenue");
                    if (Chart.getChart("chart_company_revenue")){
                        Chart.getChart("chart_company_revenue").destroy();
                    }
                    if (!speedCanvas)
                        return
                    var dataFirst = {
                        label: "Revenue",
                        data: [],
                        lineTension: 0,
                        fill: false,
                        borderColor: '#6869AC',
                        backgroundColor: '#6869AC'
                    };

                    var dataSecond = {
                        label: "Profit",
                        data: [],
                        lineTension: 0,
                        fill: false,
                        borderColor: '#4CAF50',
                        backgroundColor: '#4CAF50'
                    };
                    var dataThird = {
                        label: "Total Cost",
                        data: [],
                        lineTension: 0,
                        fill: false,
                        borderColor: '#FFB300',
                        backgroundColor: '#FFB300'

                    };

                    var speedData = {
                        labels: [],
                        datasets: [dataFirst, dataSecond, dataThird]
                    };

                    var chartOptions = {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                boxWidth: 80,
                                fontColor: 'black'
                            }
                        }
                    };

                    var lineChart = new Chart(speedCanvas, {
                        type: 'line',
                        data: speedData,
                        options: chartOptions
                    });

                    const dataTemp = lineChart.data;

                    for (let i = 0; i < data.length; i++) {
                        // change text label of chart
                        data[i][0] = data[i][0].slice(0, 3) + ' ' + currentYear  ;

                        //  push data of chart
                        dataTemp.labels.push(data[i][0]);
                        dataTemp.datasets[0].data.push(data[i][1]);
                        dataTemp.datasets[1].data.push(data[i][2]);
                        dataTemp.datasets[2].data.push(data[i][3]);
                    }

                    lineChart.data.labels = dataTemp.labels;
                    lineChart.data.datasets[0].data = dataTemp.datasets[0].data;
                    lineChart.data.datasets[1].data = dataTemp.datasets[1].data;
                    lineChart.data.datasets[2].data = dataTemp.datasets[2].data;
                    lineChart.update();
                });
        },


        contractBarChart: function() {
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_contract_type",
                })
                .then(function(data) {
                    var ele = document.getElementById('contract')
                    if (!ele)
                        return
                    if (Chart.getChart("contract")){
                        Chart.getChart("contract").destroy();
                    }
                    const ctx =ele.getContext('2d');

                    const contract = new Chart(ctx, {
                        type: "bar",
                        data: {
                            labels: [],
                            datasets: [{
                                label: "Contract",
                                data: [],
                                backgroundColor: [],
                                borderColor: '' ,
                                borderWidth: 1,
                            }, ],
                        },
                        options: {
                            scales: {
                                yAxes: {
                                    ticks: {
                                        beginAtZero: true,
                                    },
                                },
                            },
                            plugins: {
                                legend: false // Hide legend
                            },
                        },
                    });                    
                    for (let i = 0; i < data.length; i++) {
                        data[i].label = data[i].label.replace("_", " ").replace(/(^\w|\s\w)/g, m => m.toUpperCase());
                    }
                    const dataTemp = contract.data;
                    for (let i = 0; i < data.length; i++) {
                        dataTemp.labels.push(data[i].label);
                        dataTemp.datasets[0].data.push(data[i].value)
                    }
                    let dataLabel =  contract.data.labels
                    
                    for (let i = 0; i< dataLabel.length; i ++ )
                        {
                            if (dataLabel[i] == 'Collaborator' ) {
                                contract.data.datasets[0].backgroundColor[i] = '#6869AC'
                            }
                            if (dataLabel[i] == 'Internship' ) {
                                contract.data.datasets[0].backgroundColor[i] = '#4CAF50'
                            }
                            if (dataLabel[i] == 'Offical Labor' ) {
                                contract.data.datasets[0].backgroundColor[i] = '#00ACC1'
                            }
                            if (dataLabel[i] == 'Probationary' ) {
                                contract.data.datasets[0].backgroundColor[i] = '#FFB300'
                            }
                        }

                    dataLabel = dataTemp.labels;
                    contract.data.datasets[0].data = dataTemp.datasets[0].data;
                    contract.update();

                });

        },
        payrollDashboard: function() {
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_payroll_follow_month",
                })
                .then(function(data) {
                    var speedCanvas = document.getElementById("payroll");
                    if (Chart.getChart("payroll")) {
                        Chart.getChart("payroll").destroy();
                    }
                    if (!speedCanvas)
                        return
                    var dataFirst = {
                        label: "Revenue",
                        data: [],
                        lineTension: 0,
                        fill: false,
                        borderColor: '#6869AC',
                        backgroundColor: '#6869AC',
                        borderWidth: 2,
                    };

                    var dataSecond = {
                        label: "Salary",
                        data: [],
                        lineTension: 0,
                        fill: false,
                        borderColor: '#00ACC1',
                        backgroundColor: '#00ACC1',
                        borderWidth: 2,
                    };

                    var speedData = {
                        labels: [],
                        datasets: [dataFirst, dataSecond]
                    };

                    var chartOptions = {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                boxWidth: 2,
                                fontColor: 'black'
                            }
                        }
                    };

                    var lineChart = new Chart(speedCanvas, {
                        type: 'line',
                        data: speedData,
                        options: chartOptions
                    });

                    const dataTemp = lineChart.data;
              
                    for (let i = 0; i < data.length; i++) {
                        // change text label of chart
                        data[i][0] = data[i][0].slice(0, 3) + ' ' + currentYear  ;

                        //  push data of chart
                        dataTemp.labels.push(data[i][0]);
                        dataTemp.datasets[0].data.push(data[i][1]);
                        dataTemp.datasets[1].data.push(data[i][2]);
                    }

                    lineChart.data.labels = dataTemp.labels;
                    lineChart.data.datasets[0].data = dataTemp.datasets[0].data;
                    lineChart.data.datasets[1].data = dataTemp.datasets[1].data;
                    lineChart.update();
                });

        },

        chartPayrollRevenueFollowMonth: function() {
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_payroll_revenue_follow_month",
                })
                .then(function(data) {
                    for (let i = 0; i < data.length; i++) {
                        if (data[i][1] == null) 
                            {
                                data[i][1] = 0;
                            }
                    }

                    if (data.length > 0)
                    {
                        var data_employee = data;
                    }
                    var ele = document.getElementById("salary-cost-revenue");
                    if (Chart.getChart("salary-cost-revenue")){
                        Chart.getChart("salary-cost-revenue").destroy();
                    }
                    if (!ele)
                        return
                    const ctx = ele.getContext("2d");
                    const chartProjectBase = new Chart(ctx, {
                        type: "line",
                        data: {
                            labels: [],
                            datasets: [{
                                label: "Salary / Revenue",
                                data: [],
                                backgroundColor: ['#6869AC'],
                                borderColor: ['#6869AC'],
                                borderWidth: 2,
                            }, ],
                        },
                        options: {
                            scales: {
                                yAxes: {
                                    ticks: {
                                        beginAtZero: true,
                                    },
                                },
                            },
                            plugins: {
                                legend: false // Hide legend
                            },
                        },
                    });
                    const dataTemp = chartProjectBase.data;
                    if(!data_employee)
                        return
                    for (let i = 0; i < data_employee.length; i++) {
                        // change text label of chart
                        data[i][0] = data[i][0].slice(0, 3) + ' ' + currentYear  ;

                        //  push data of chart
                        dataTemp.labels.push(data_employee[i][0]);
                        dataTemp.datasets[0].data.push(data_employee[i][1]);
                    }

                    chartProjectBase.data.labels = dataTemp.labels;
                    chartProjectBase.data.datasets[0].data = dataTemp.datasets[0].data;

                    chartProjectBase.update();
                });
        },
    });

    core.action_registry.add("dynamic_bom_dashboard", DynamicDashboard);

    return DynamicDashboard;
});