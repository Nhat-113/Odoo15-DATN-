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

    var DynamicDashboard = AbstractAction.extend({
        template: "dynamic_bom_dashboard",
        jsLibs: ["/ds_company_management/static/src/js/lib/chart.js"],

        events: {},

        init: function(parent, context) {
            this.action_id = context["id"];
            this._super(parent, context);
        },

        start: function() {
            var self = this;
            this.set("title", "Dashboard Bom");
            setTimeout(() => {
                self.projectTypePierChart();
                self.jobPositionPierChart();
                self.chartProjectODC();
                self.chartProjectBase();
                self.chartProjectInternal();
                self.chartProjectAvg();
                self.departmentBarChart();
                self.contractBarChart();
                self.payrollDashboard();
            }, 1000);
            setTimeout(() => {
                self.chartCompanyAvg();
            }, 4000);
        },

        willStart: function() {
            var self = this;
            return $.when(ajax.loadLibs(this), this._super()).then(function() {
                return self.fetch_data();
            });
        },

        fetch_data: function() {},
        projectTypePierChart: function() {
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_project_status",
                })
                .then(function(data) {
                    var ele = document.getElementById("project_status");
                    if (!ele) 
                        return
                    const ctx = ele.getContext("2d");
                    const project_status = new Chart(ctx, {
                        type: "pie",
                        data: {
                            labels: [],
                            datasets: [{
                                label: "Project Status Chart",
                                data: [],
                                backgroundColor: [
                                    "rgba(255, 99, 132, 0.2)",
                                    "rgba(54, 162, 235, 0.2)",
                                    "rgba(255, 206, 86, 0.2)",
                                    "rgba(75, 192, 192, 0.2)",
                                    "rgba(153, 102, 255, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                ],
                                borderColor: [
                                    "rgba(255, 99, 132, 1)",
                                    "rgba(54, 162, 235, 1)",
                                    "rgba(255, 206, 86, 1)",
                                    "rgba(75, 192, 192, 1)",
                                    "rgba(153, 102, 255, 1)",
                                    "rgba(255, 159, 64, 1)",
                                ],
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
                        },
                    });
                    const dataTemp = project_status.data;
                    for (let i = 0; i < data.length; i++) {
                        dataTemp.labels.push(data[i].label);
                        dataTemp.datasets[0].data.push(data[i].value);
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
                    const ctx = ele.getContext("2d");
                    // Chart.defaults.scales.linear.min = 0;
                    const jobPosition = new Chart(ctx, {
                        type: "bar",
                        data: {
                            labels: [],
                            datasets: [{
                                label: "Job Position",
                                data: [],
                                backgroundColor: [
                                    "rgba(255, 99, 132, 0.2)",
                                    "rgba(54, 162, 235, 0.2)",
                                    "rgba(255, 206, 86, 0.2)",
                                    "rgba(75, 192, 192, 0.2)",
                                    "rgba(153, 102, 255, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                ],
                                borderColor: [
                                    "rgba(255, 99, 132, 1)",
                                    "rgba(54, 162, 235, 1)",
                                    "rgba(255, 206, 86, 1)",
                                    "rgba(75, 192, 192, 1)",
                                    "rgba(153, 102, 255, 1)",
                                    "rgba(255, 159, 64, 1)",
                                ],
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
        chartProjectODC: function() {
            let self = this;
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_effort_human_resource",
                })
                .then(function(data) {
                    var data_employee = self.valueProjectODC(data);
                    var ele = document.getElementById("chart_ODC");
                    if (!ele) 
                        return
                    const ctx = ele.getContext("2d");

                    const chartODC = new Chart(ctx, {
                        type: "line",
                        data: {
                            labels: [
                                "Jan",
                                "Feb",
                                "Mar",
                                "Apr",
                                "May",
                                "Jun",
                                "Jul",
                                "Aug",
                                "Sep",
                                "Oct",
                                "Nov",
                                "Dec",
                            ],
                            datasets: [{
                                label: "Line Chart project ODC",
                                data: [],
                                backgroundColor: [
                                    "rgba(255, 99, 132, 0.2)",
                                    "rgba(54, 162, 235, 0.2)",
                                    "rgba(255, 206, 86, 0.2)",
                                    "rgba(75, 192, 192, 0.2)",
                                    "rgba(153, 102, 255, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                ],
                                borderColor: [
                                    "rgba(255, 99, 132, 1)",
                                    "rgba(54, 162, 235, 1)",
                                    "rgba(255, 206, 86, 1)",
                                    "rgba(75, 192, 192, 1)",
                                    "rgba(153, 102, 255, 1)",
                                    "rgba(255, 159, 64, 1)",
                                ],
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
                        },
                    });
                    const dataTemp = chartODC.data;
                    for (let i = 2; i <= Object.keys(data_employee).length; i++) {
                        dataTemp.datasets[0].data.push(data_employee[i]);
                    }
                    chartODC.data.datasets[0].data = dataTemp.datasets[0].data;
                    chartODC.update();
                });
        },

        valueProjectODC: function(arr) {
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
            var res = [];
            var res_2 = [];
            var res_3 = [];
            let a = 0;
            for (let i = 0; i < count_row_array; i++) {
                for (let j = 0; j <= 14; j++) {
                    if (arr[i][j] > 0 && arr[i][j] != isNaN) {
                        res_2[j] = (res_2[j] || 0) + parseFloat(arr[i][j]);
                    }

                    if (arr[i][1] == "ODC" && arr[i][j] > 0 && arr[i][j] != isNaN) {
                        res[j] = (res[j] || 0) + parseFloat(arr[i][j]);
                    }
                    res_3[j] = (res[j] / res_2[j]) * 100;
                }

                if (!isNaN(parseFloat(arr[i][14]))) a += parseFloat(arr[i][14]);
            }
            res = Array.from(res, (item) => item || 0);
            res_2 = Array.from(res_2, (item) => item || 0);
            res_3 = Array.from(res_3, (item) => item || 0);

            var rv = {};
            for (var i = 0; i <= res_3.length; ++i) rv[i] = res_3[i];
            return rv;
        },

        chartProjectBase: function() {
            let self = this;
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_effort_human_resource",
                })
                .then(function(data) {
                    var data_employee = self.valueProjectBase(data);
                    var ele = document.getElementById("chart_project_base");
                    if (!ele) 
                        return
                    const ctx = ele.getContext("2d");

                    const chartProjectBase = new Chart(ctx, {
                        type: "line",
                        data: {
                            labels: [
                                "Jan",
                                "Feb",
                                "Mar",
                                "Apr",
                                "May",
                                "Jun",
                                "Jul",
                                "Aug",
                                "Sep",
                                "Oct",
                                "Nov",
                                "Dec",
                            ],
                            datasets: [{
                                label: "Line Chart Project Base",
                                data: [],
                                backgroundColor: [
                                    "rgba(255, 99, 132, 0.2)",
                                    "rgba(54, 162, 235, 0.2)",
                                    "rgba(255, 206, 86, 0.2)",
                                    "rgba(75, 192, 192, 0.2)",
                                    "rgba(153, 102, 255, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                ],
                                borderColor: [
                                    "rgba(255, 99, 132, 1)",
                                    "rgba(54, 162, 235, 1)",
                                    "rgba(255, 206, 86, 1)",
                                    "rgba(75, 192, 192, 1)",
                                    "rgba(153, 102, 255, 1)",
                                    "rgba(255, 159, 64, 1)",
                                ],
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
                        },
                    });
                    const dataTemp = chartProjectBase.data;
                    for (let i = 2; i <= Object.keys(data_employee).length; i++) {
                        dataTemp.datasets[0].data.push(data_employee[i]);
                    }
                    chartProjectBase.data.datasets[0].data = dataTemp.datasets[0].data;
                    chartProjectBase.update();
                });
        },

        valueProjectBase: function(arr) {
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
            var res = [];
            var res_2 = [];
            var res_3 = [];
            let a = 0;
            for (let i = 0; i < count_row_array; i++) {
                for (let j = 0; j <= 14; j++) {
                    if (arr[i][j] > 0 && arr[i][j] != isNaN) {
                        res_2[j] = (res_2[j] || 0) + parseFloat(arr[i][j]);
                    }

                    if (
                        arr[i][1] == "Project Base" &&
                        arr[i][j] > 0 &&
                        arr[i][j] != isNaN
                    ) {
                        res[j] = (res[j] || 0) + parseFloat(arr[i][j]);
                    }
                    res_3[j] = (res[j] / res_2[j]) * 100;
                }

                if (!isNaN(parseFloat(arr[i][14]))) a += parseFloat(arr[i][14]);
            }
            res = Array.from(res, (item) => item || 0);
            res_2 = Array.from(res_2, (item) => item || 0);
            res_3 = Array.from(res_3, (item) => item || 0);

            var rv = {};
            for (var i = 0; i <= res_3.length; ++i) 
                rv[i] = res_3[i];

            return rv;
        },

        chartProjectInternal: function() {
            let self = this;
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_effort_human_resource",
                })
                .then(function(data) {
                    var data_employee = self.valueProjectInternal(data);
                    var ele = document.getElementById("chart_project_internal");
                    if (!ele) 
                        return
                    const ctx = ele.getContext("2d");

                    const chartProjectInternal = new Chart(ctx, {
                        type: "line",
                        data: {
                            labels: [
                                "Jan",
                                "Feb",
                                "Mar",
                                "Apr",
                                "May",
                                "Jun",
                                "Jul",
                                "Aug",
                                "Sep",
                                "Oct",
                                "Nov",
                                "Dec",
                            ],
                            datasets: [{
                                label: "Project Internal",
                                data: [],
                                backgroundColor: [
                                    "rgba(255, 99, 132, 0.2)",
                                    "rgba(54, 162, 235, 0.2)",
                                    "rgba(255, 206, 86, 0.2)",
                                    "rgba(75, 192, 192, 0.2)",
                                    "rgba(153, 102, 255, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                    "rgba(255, 159, 64, 0.2)",
                                ],
                                borderColor: [
                                    "rgba(255, 99, 132, 1)",
                                    "rgba(54, 162, 235, 1)",
                                    "rgba(255, 206, 86, 1)",
                                    "rgba(75, 192, 192, 1)",
                                    "rgba(153, 102, 255, 1)",
                                    "rgba(255, 159, 64, 1)",
                                ],
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
                        },
                    });
                    const dataTemp = chartProjectInternal.data;
                    for (let i = 2; i <= Object.keys(data_employee).length; i++) {
                        dataTemp.datasets[0].data.push(data_employee[i]);
                    }
                    chartProjectInternal.data.datasets[0].data =
                        dataTemp.datasets[0].data;
                    chartProjectInternal.update();
                });
        },

        valueProjectInternal: function(arr) {
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
            var res = [];
            var res_2 = [];
            var res_3 = [];
            let a = 0;
            for (let i = 0; i < count_row_array; i++) {
                for (let j = 0; j <= 14; j++) {
                    if (arr[i][j] > 0 && arr[i][j] != isNaN) {
                        res_2[j] = (res_2[j] || 0) + parseFloat(arr[i][j]);
                    }

                    if (arr[i][1] == "Internal" && arr[i][j] > 0 && arr[i][j] != isNaN) {
                        res[j] = (res[j] || 0) + parseFloat(arr[i][j]);
                    }
                    res_3[j] = (res[j] / res_2[j]) * 100;
                }

                if (!isNaN(parseFloat(arr[i][14]))) a += parseFloat(arr[i][14]);
            }
            res = Array.from(res, (item) => item || 0);
            res_2 = Array.from(res_2, (item) => item || 0);
            res_3 = Array.from(res_3, (item) => item || 0);

            var rv = {};
            for (var i = 0; i <= res_3.length; ++i) 
                rv[i] = res_3[i];

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
                    var data_employee = self.valueProjectAVG(data);
                    var ele = document.getElementById("chart_avg_project");
                    if (!ele) 
                        return
                    const ctx = ele.getContext("2d");

                    const chartAvgProject = new Chart(ctx, {
                        type: "line",
                        data: {
                            labels: [ "Project ODC", "Project Internal", "Project Base"],
                            datasets: [{
                                label: "Project Avg",
                                data: [],
                                backgroundColor: [
                                    "rgba(255, 99, 132, 0.2)",
                                    "rgba(54, 162, 235, 0.2)",
                                    "rgba(255, 206, 86, 0.2)",
                                ],
                                borderColor: [
                                    "rgba(255, 99, 132, 1)",
                                    "rgba(54, 162, 235, 1)",
                                    "rgba(255, 206, 86, 1)",
                                ],
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
                        },
                    });
                    const dataTemp = chartAvgProject.data;
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
            var sum_internal = [];
            var sum_odc = [];
            var sum_pro_base = [];
            var sum_total = [];
            let a = 0;
            for (let i = 0; i < count_row_array; i++) {
                for (let j = 0; j < 14; j++) {
                    if (arr[i][j] > 0 && arr[i][j] != isNaN) {
                        sum_total[j] = (sum_total[j] || 0) + parseFloat(arr[i][j]);
                    }

                    if (arr[i][1] == "Internal" && arr[i][j] > 0 && arr[i][j] != isNaN) {
                        sum_internal[j] = (sum_internal[j] || 0) + parseFloat(arr[i][j]);
                    }

                    if (arr[i][1] == "ODC" && arr[i][j] > 0 && arr[i][j] != isNaN) {
                        sum_odc[j] = (sum_odc[j] || 0) + parseFloat(arr[i][j]);
                    }

                    if (arr[i][1] == "Project Base" && arr[i][j] > 0 && arr[i][j] != isNaN) {
                        sum_pro_base[j] = (sum_pro_base[j] || 0) + parseFloat(arr[i][j]);
                    }
                }

                if (!isNaN(parseFloat(arr[i][14]))) a += parseFloat(arr[i][14]);
            }

            sum_internal = Array.from(sum_internal, (item) => item || 0);
            sum_odc = Array.from(sum_odc, (item) => item || 0);
            sum_pro_base = Array.from(sum_pro_base, (item) => item || 0);
            sum_total = Array.from(sum_total, (item) => item || 0);

            var sum_value_internal,
                sum_value_odc,
                sum_value_pro_base,
                sum_value_total;

            sum_value_internal = sum_internal.reduce((a, b) => a + b, 0);
            sum_value_odc = sum_odc.reduce((a, b) => a + b, 0);
            sum_value_pro_base = sum_pro_base.reduce((a, b) => a + b, 0);
            sum_value_total = sum_total.reduce((a, b) => a + b, 0);
            
            var effort_avg_odc = (sum_value_odc / sum_value_total) * 100;
            var effort_avg_internal = (sum_value_internal / sum_value_total) * 100;
            var effort_avg_pro_base = (sum_value_pro_base / sum_value_total) * 100;

            let avg = [effort_avg_odc, effort_avg_internal, effort_avg_pro_base];

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
                    var ele = document.getElementById("chart_company_revenue");
                    if (!ele) 
                        return
                    const ctx = ele.getContext("2d");

                    const chartCompanyRevenue = new Chart(ctx, {
                        type: "line",
                        data: {
                            labels: [],
                            datasets: [{
                                    yAxisID: "A", // <-- the Y axis to use for this data set
                                    label: "Revenue",
                                    data: [],
                                    borderWidth: 1,
                                    backgroundColor: "rgba(255, 99, 132, 0.2)",
                                    borderColor: "rgba(255, 99, 132, 1)",
                                },
                                {
                                    yAxisID: "B", // <-- the Y axis to use for this data set
                                    label: "Members",
                                    data: [],
                                    backgroundColor: "rgba(54, 162, 235, 0.2)",
                                    borderColor: "rgba(54, 162, 235, 1)",
                                },
                            ],
                        },

                        options: {
                            responsive: true,
                            scales: {
                                A: {
                                    type: "linear",
                                    position: "left",
                                    ticks: { beginAtZero: true, color: "rgba(255, 99, 132, 1)" },
                                    grid: { display: false },
                                },
                                B: {
                                    type: "linear",
                                    position: "right",
                                    ticks: { beginAtZero: true, color: "rgba(54, 162, 235, 1)" },
                                    grid: { display: false },
                                },
                                x: { ticks: { beginAtZero: true } },
                            },
                        },
                    });

                    const dataTemp = chartCompanyRevenue.data;

                    for (let i = 0; i < data.length; i++) {
                        dataTemp.labels.push(data[i][0]);
                        dataTemp.datasets[0].data.push(data[i][1]);
                        dataTemp.datasets[1].data.push(data[i][2]);
                    }

                    chartCompanyRevenue.data.labels = dataTemp.labels;
                    chartCompanyRevenue.data.datasets[0].data = dataTemp.datasets[0].data;

                    chartCompanyRevenue.data.datasets[1].data = dataTemp.datasets[1].data;
                    chartCompanyRevenue.update();
                });
        },

        departmentBarChart: function() {
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_dept_employee",
                })
                .then(function(data) {
                    const ctx = document.getElementById('department').getContext('2d');
                    const department = new Chart(ctx, {
                        type: "bar",
                        data: {
                            labels: [],
                            datasets: [{
                                label: "Department",
                                data: [],
                                backgroundColor: [
                                    "rgba(255, 99, 132, 0.2)",
                                    "rgba(54, 162, 235, 0.2)",
                                    "rgba(255, 206, 86, 0.2)",
                                ],
                                borderColor: [
                                    "rgba(255, 99, 132, 1)",
                                    "rgba(54, 162, 235, 1)",
                                    "rgba(255, 206, 86, 1)",
                                ],
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
                        },
                    });
                    const dataTemp = department.data;
                    for (let i = 0; i < data.length; i++) {
                        dataTemp.labels.push(data[i].label);
                        dataTemp.datasets[0].data.push(data[i].value)
                    }
                    department.data.labels = dataTemp.labels;
                    department.data.datasets[0].data = dataTemp.datasets[0].data;
                    department.update();

                });

        },
        contractBarChart: function() {
            rpc
                .query({
                    model: "dashboard.block",
                    method: "get_contract_type",
                })
                .then(function(data) {
                    const ctx = document.getElementById('contract').getContext('2d');
                    const contract = new Chart(ctx, {
                        type: "bar",
                        data: {
                            labels: [],
                            datasets: [{
                                label: "Contract",
                                data: [],
                                backgroundColor: [
                                    "rgba(255, 99, 132, 0.2)",
                                    "rgba(54, 162, 235, 0.2)",
                                    "rgba(255, 206, 86, 0.2)",
                                ],
                                borderColor: [
                                    "rgba(255, 99, 132, 1)",
                                    "rgba(54, 162, 235, 1)",
                                    "rgba(255, 206, 86, 1)",
                                ],
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
                        },
                    });
                    const dataTemp = contract.data;
                    for (let i = 0; i < data.length; i++) {
                        dataTemp.labels.push(data[i].label);
                        dataTemp.datasets[0].data.push(data[i].value)
                    }
                    contract.data.labels = dataTemp.labels;
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
                    const ctx = document.getElementById('payroll').getContext('2d');
                    const payroll = new Chart(ctx, {
                        type: "line",
                        data: {
                            labels: [],
                            datasets: [{
                                label: "Payroll ana",
                                data: [],
                                backgroundColor: [
                                    "rgba(255, 99, 132, 0.2)",
                                ],
                                borderColor: [
                                    "rgba(255, 99, 132, 1)",
                                ],
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
                        },
                    });
                    const dataTemp = payroll.data;
                    for (let i = 0; i < data.length; i++) {
                        dataTemp.labels.push(data[i].label);
                        dataTemp.datasets[0].data.push(data[i].value)
                    }
                    payroll.data.labels = dataTemp.labels;
                    payroll.data.datasets[0].data = dataTemp.datasets[0].data;
                    payroll.update();

                });

        },
    });

    core.action_registry.add("dynamic_bom_dashboard", DynamicDashboard);

    return DynamicDashboard;
});