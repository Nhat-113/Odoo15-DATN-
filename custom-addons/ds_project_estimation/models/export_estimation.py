import math
from odoo import models
from odoo.exceptions import UserError
import xlsxwriter


class EstimationXlsx(models.AbstractModel):
    _name = 'report.ds_project_estimation.estimation_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, estimation):

        if len(estimation) > 1:
           raise UserError('Please select only one estimate')
        else:        
            merge_format = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'font_size': 20,
                'font_color': 'red'})

            merge_format_header = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'})

            bold = workbook.add_format({
                'bold': 1,
                'border': 1})

            bold_center = workbook.add_format(
                {'bold': True, 'align': 'center', 'border': 1})

            border = workbook.add_format({'border': 1, 'text_wrap': True})

            # sheet COVER
            self.sheetCover(workbook, estimation,
                            {
                                "merge": merge_format,
                                "merge_header": merge_format_header,
                                "bold": bold,
                                "bold_center": bold_center,
                                "border": border
                            })

            # sheet Summarize
            self.sheetSummarize(workbook, estimation,
                            {
                                "merge": merge_format,
                                "merge_header": merge_format_header,
                                "bold": bold,
                                "bold_center": bold_center,
                                "border": border
                            })

            # sheet Resource Plan
            self.sheetResourcePlan(workbook, estimation,
                            {
                                "merge": merge_format,
                                "merge_header": merge_format_header,
                                "bold": bold,
                                "bold_center": bold_center,
                                "border": border
                            })

            # sheet Module
            self.sheetModule(workbook, estimation,
                            {
                                "merge": merge_format,
                                "merge_header": merge_format_header,
                                "bold": bold,
                                "bold_center": bold_center,
                                "border": border
                            })
        
    def sheetCover(self, workbook, estimation, format):
        sheet_cover = workbook.add_worksheet('Cover')

        sheet_cover.set_column(0, 0, 1)
        sheet_cover.insert_image(
            'C3', 'custom-addons/ds_project_estimation/static/description/d-soft.jpg', {'x_offset': 170, 'y_offset': 5})
        sheet_cover.merge_range(
            'B2:E10', 'ESTIMATION FOR PROJECT '+(estimation.project_name).upper(), format['merge'])
        sheet_cover.merge_range('B13:E13', 'HISTORY LOG', format['merge_header'])

        row, col = 13, 1
        col_names_sheet_cover = [
            "Revision",
            "Description",
            "User Update",
            "Update Date"
        ]

        # Set Column Ranges
        sheet_cover.set_column(col, col + 10, 30)
        sheet_cover.set_column(2, 2, 40)

        for i, name in enumerate(col_names_sheet_cover):
            sheet_cover.write(row, col + i, name, format['bold_center'])

        for obj in estimation:
            overviews = obj.env['estimation.overview'].search(
                [('connect_overview', '=', obj.id)])
            for overview in overviews[-1]:
                row += 1
                revision = overview.revision
                description = overview.description
                author = overview.author.employee_id.name
                update_date = overview.write_date.strftime("%d/%m/%Y")
                col_values = [
                    revision,
                    description,
                    author,
                    update_date
                ]
                for i, value in enumerate(col_values):
                    sheet_cover.write(row, col + i, value, format['border'])

        sheet_cover.hide_gridlines(2)

    def sheetSummarize(self, workbook, estimation, format):

        sheet_summarize = workbook.add_worksheet('Summarize')

        sheet_summarize.insert_image(
            'C3', 'custom-addons/ds_project_estimation/static/description/d-soft.jpg', {'x_offset': 370, 'y_offset': 0.5})

        # table Total cost
        sheet_summarize.merge_range(
            'A1:K10', 'COST SUMMARIZE FOR PROJECT '+(estimation.project_name).upper(), format['merge'])
        sheet_summarize.merge_range(
            'B13:K13', 'Total cost', format['merge_header'])
        sheet_summarize.merge_range('B14:B15', 'No', format['merge_header'])
        sheet_summarize.merge_range(
            'C14:C15', 'Components', format['merge_header'])
        sheet_summarize.merge_range(
            'D14:D15', 'Total Effort (MD)', format['merge_header'])
        sheet_summarize.merge_range(
            'E14:J14', 'Detailed Effort (MD)', format['merge_header'])
        sheet_summarize.merge_range(
            'K14:K15', 'COST ('+estimation.currency_id.name+')', format['merge_header'])

        # Set Column Ranges in Summarize
        sheet_summarize.set_column(0, 0, 1)
        sheet_summarize.set_column(1, 1, 6)
        sheet_summarize.set_column(2, 2, 25)
        sheet_summarize.set_column(3, 4, 20)
        sheet_summarize.set_column(5, 9, 12)
        sheet_summarize.set_column(10, 10, 15)

        col_names_sheet_summarize = [
            "Designer",
            "Dev",
            "Tester",
            "Comtor",
            "BSE",
            "PM"
        ]

        row_header_summarize, col_header_summarize = 14, 4
        for i, name in enumerate(col_names_sheet_summarize):
            sheet_summarize.write(
                row_header_summarize, col_header_summarize + i, name, format['merge_header'])

        row_data_summarize, col_data_summarize = 14, 1
        totalcosts = estimation.env['estimation.summary.totalcost'].search(
            [('estimation_id', '=', estimation.id)])
        no = 1
        total_effort = 0
        design_effort = 0
        dev_effort = 0
        tester_effort = 0
        comtor_effort = 0
        brse_effort = 0
        pm_effort = 0
        cost = 0
        for total in totalcosts:
            row_data_summarize += 1
            col_values_summarize = [
                no,
                total.name,
                total.total_effort,
                total.design_effort,
                total.dev_effort,
                total.tester_effort,
                total.comtor_effort,
                total.brse_effort,
                total.pm_effort,
                total.cost,
            ]
            total_effort += total.total_effort
            design_effort += total.design_effort
            dev_effort += total.dev_effort
            tester_effort += total.tester_effort
            comtor_effort += total.comtor_effort
            brse_effort += total.brse_effort
            pm_effort += total.pm_effort
            cost += total.cost
            no += 1
            for i, value in enumerate(col_values_summarize):
                sheet_summarize.write(
                    row_data_summarize, col_data_summarize + i, value, format['border'])
        total_values = [
            total_effort,
            design_effort,
            dev_effort,
            tester_effort,
            comtor_effort,
            brse_effort,
            pm_effort,
            cost
        ]
        sheet_summarize.write(row_data_summarize + 1, 2, 'Total', format['merge_header'])
        for i, value in enumerate(total_values):
            sheet_summarize.write(row_data_summarize + 1, 3 + i, value, format['bold'])

        # table Cost rate
        sheet_summarize.merge_range(
            row_data_summarize + 4, 1, row_data_summarize + 4, 4, 'Cost rate', format['merge_header'])
        sheet_summarize.write(row_data_summarize + 5, 1, 'No', format['merge_header'])
        sheet_summarize.write(row_data_summarize + 5, 2, 'Type', format['merge_header'])
        sheet_summarize.write(
            row_data_summarize + 5, 3, 'Unit ('+estimation.currency_id.name+'/Month)', format['merge_header'])
        sheet_summarize.write(
            row_data_summarize + 5, 4, 'Unit ('+estimation.currency_id.name+'/Day)', format['merge_header'])

        row_cost_rate, col_cost_rate = row_data_summarize + 5, 1

        modules = estimation.env['estimation.module'].search([('estimation_id','=',estimation.id)])
        if modules:
            costrates = estimation.env['estimation.summary.costrate'].search(
                [('connect_summary_costrate', '=', estimation.id), ('name', '=', modules[-1].component)])
            for costrate in costrates:
                row_cost_rate += 1
                col_value_cost_rate = [
                    costrate.sequence,
                    costrate.types,
                    costrate.yen_month,
                    costrate.yen_day
                ]
                for i, value in enumerate(col_value_cost_rate):
                    sheet_summarize.write(
                        row_cost_rate, col_cost_rate + i, value, format['border'])

        sheet_summarize.hide_gridlines(2)    

    def sheetResourcePlan(self, workbook, estimation, format):
        sheet_resource = workbook.add_worksheet('Resource Plan')

        sheet_resource.set_column(0, 0, 1)
        sheet_resource.insert_image(
            'C3', 'custom-addons/ds_project_estimation/static/description/d-soft.jpg', {'x_offset': 450, 'y_offset': 0.5})

        sheet_resource.merge_range(
            'A1:J10', 'RESOURCE PLAN FOR PROJECT '+(estimation.project_name).upper(), format['merge'])
        sheet_resource.merge_range(
            'B13:J13', 'Total effort', format['merge_header'])
        sheet_resource.merge_range('B14:B15', 'No', format['merge_header'])
        sheet_resource.merge_range(
            'C14:C15', 'Components', format['merge_header'])
        sheet_resource.merge_range(
            'D14:D15', 'Total Effort (MD)', format['merge_header'])
        sheet_resource.merge_range(
            'E14:J14', 'Detailed Effort (MD)', format['merge_header'])

        format_center = workbook.add_format(
                {'align': 'center', 'border': 1})

        merge_total = workbook.add_format({
                'bold': 1,
                'border': 1})

        sheet_resource.set_column(0, 0, 1)
        sheet_resource.set_column(1, 1, 10)
        sheet_resource.set_column(2, 4, 20)
        sheet_resource.set_column(5, 9, 20)
        sheet_resource.set_column(11, 13, 20)

        sheet_resource.set_column(14, 140, 2)
        col_names_sheet_resource = [
            "Designer",
            "Dev",
            "Tester",
            "Comtor",
            "Brse",
            "PM"
        ]
        duration = []
        row_header_resource, col_header_resource = 14, 4
        for i, name in enumerate(col_names_sheet_resource):
            sheet_resource.write(
                row_header_resource, col_header_resource + i, name, format['merge_header'])


        row_data_total_effort, col_data_total_effort = 14, 1
        resources = estimation.env['estimation.resource.effort'].search([('estimation_id','=',estimation.id)])
        for resource in resources[:-3]:
            row_data_total_effort += 1
            col_values = [
                resource.sequence,
                resource.name,
                resource.total_effort,
                resource.design_effort,
                resource.dev_effort,
                resource.tester_effort,
                resource.comtor_effort,
                resource.brse_effort,
                resource.pm_effort
            ]
            for i, value in enumerate(col_values):
                sheet_resource.write(
                    row_data_total_effort, col_data_total_effort + i, value, format['border'])

        for resource in resources[-2:]:
            row_data_total_effort += 1
            col_values = [
                '',
                resource.name,
                resource.total_effort,
                resource.design_effort,
                resource.dev_effort,
                resource.tester_effort,
                resource.comtor_effort,
                resource.brse_effort,
                resource.pm_effort
            ]
            for i, value in enumerate(col_values):
                sheet_resource.write(
                    row_data_total_effort, col_data_total_effort + i, value, merge_total)

            if resource.name == 'Total (MM)':
                duration = [
                    resource.design_effort,
                    resource.dev_effort,
                    resource.comtor_effort,
                    resource.tester_effort,
                    resource.brse_effort,
                    resource.pm_effort
                ]

        row_data_chartt , col_data_chartt = 12, 11

        sheet_resource.merge_range(
            row_data_chartt, col_data_chartt, row_data_chartt, col_data_chartt + 1, 'Resource Plan', format['merge_header'])
        sheet_resource.write(row_data_chartt + 1, col_data_chartt, 'Resource', format['merge_header'])
        sheet_resource.write(row_data_chartt + 1, col_data_chartt + 1, 'Resource Count', format['merge_header'])
        sheet_resource.write(row_data_chartt + 1, col_data_chartt + 2, 'Duration (Month)', format['merge_header'])

        job_position = [
            'Designer',
            'Dev',
            'Comtor',
            'Tester',
            'Brse',
            'PM'
        ]
        count = 0
        if len(duration) > 0:
            for i, value in enumerate(job_position):
                sheet_resource.write(row_data_chartt + 2 + i, col_data_chartt, value, format['border'])
                sheet_resource.write(row_data_chartt + 2 + i, col_data_chartt + 2, duration[i], format_center)
                if (int(str(round(duration[i], 1)).split('.')[1])) >= 5:
                    sheet_resource.write(row_data_chartt + 2 + i, col_data_chartt + 1, math.ceil(duration[i]), format_center)
                    count += math.ceil(duration[i])
                else:
                    sheet_resource.write(row_data_chartt + 2 + i, col_data_chartt + 1, round(duration[i]), format_center)
                    count += round(duration[i])
            
            sheet_resource.write(row_data_chartt + 8, col_data_chartt + 1, count, format['bold_center'])
            month = math.ceil(max(duration))
            col = 0
            num_days = 10
            for i in range(1, month+1):                       
                sheet_resource.merge_range(
                    row_data_chartt + 1, 14 + col, row_data_chartt + 1, 13 + col + num_days, 'Month - '+str(i), format['merge_header'])
                col += num_days

            gantt_format = workbook.add_format({
                'border': 1,
                'fg_color': 'green'})

            for i in range(len(duration)):
                if math.ceil(duration[i]*10) > 0:
                    sheet_resource.merge_range(
                        row_data_chartt + 2 + i, 14, row_data_chartt + 2 + i, 13 + math.ceil(duration[i]*10), '', gantt_format)
                else:
                    sheet_resource.merge_range(
                        row_data_chartt + 2 + i, 14, row_data_chartt + 2 + i, 14 + math.ceil(duration[i]*10), '', gantt_format)

        sheet_resource.hide_gridlines(2)
            
    def sheetModule(self, workbook, estimation, format):
        modules = estimation.env['estimation.module'].search([('estimation_id','=',estimation.id)])

        merge_value = workbook.add_format({
                'border': 1
                })

        border_right = workbook.add_format({
                'border': 0,
                'right': 1,
                })
        border_left = workbook.add_format({
                'border': 0,
                'left': 1,
                'bottom':1
                })

        border_bottom = workbook.add_format({
                'border': 0,
                'right': 1,
                'bottom': 1
                })

        format_icon = workbook.add_format({
                'border': 0,
                'font_name' : 'Wingdings 2',
                'align':'right',
                'left': 1
                })
        
        format_icon_border_bottom = workbook.add_format({
                'border': 0,
                'font_name' : 'Wingdings 2',
                'align':'right',
                'left': 1,
                'bottom': 1
                })
        
        merge_breakdown = workbook.add_format({
                'border': 1,
                'bold': 1,
                'fg_color': '#E0E3E3'
                })

        merge_header = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': '#86F5F0'})

        merge_row = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': '#E0E3E3'})

        merge_row_rotate = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'rotation': 90,
                'fg_color': '#E0E3E3'})

        merge_activity = workbook.add_format({
                'bold': 1,
                'border': 1,
                'fg_color': '#75FCC1'})

        merge_row_value = workbook.add_format({
                'border': 1,
                'align':'right',
                'fg_color': '#E0E3E3'})

        merge_row_value_bold = workbook.add_format({
                'bold': 1,
                'border': 1,
                'fg_color': '#E0E3E3'})

        for module in modules:
            sheet_module = workbook.add_worksheet(module.component)
            # Set Column Ranges in Summarize
            sheet_module.set_column(0, 0, 1.5)
            sheet_module.set_column(1, 2, 3.5)
            sheet_module.set_column(3, 3, 23)
            sheet_module.set_column(4, 5, 10)
            sheet_module.set_column(6, 6, 16)
            sheet_module.set_column(7, 8, 9)
            sheet_module.set_column(9, 9, 28)
            sheet_module.set_column(10, 10, 20)
            sheet_module.insert_image(
                'C2', 'custom-addons/ds_project_estimation/static/description/d-soft.jpg', {'x_offset': 370, 'y_offset': 10})
            sheet_module.merge_range(
                'A1:K10', 'ESTIMATION FOR '+(module.component).upper()+' - PROJECT '+(estimation.project_name).upper(), format['merge'])
            sheet_module.merge_range(
            'B13:K13', 'Assumption', merge_header)
            row_assumption = 13
            assumptions = self.env['estimation.module.assumption'].search([('module_id', '=', module.id)])
            if assumptions:
                for ass in assumptions[:-1]:
                    sheet_module.merge_range(row_assumption, 1, row_assumption, 2, 'Å', format_icon)
                    sheet_module.merge_range(
                        row_assumption , 3, row_assumption, 10, ass.assumption, border_right)
                    row_assumption += 1
                sheet_module.merge_range(row_assumption, 1, row_assumption, 2, 'Å', format_icon_border_bottom)
                sheet_module.merge_range(
                        row_assumption , 3, row_assumption, 10, assumptions[-1].assumption, border_bottom)

            row_summary = row_assumption + 2
            sheet_module.merge_range(row_summary, 1, row_summary, 10, 'Summary', merge_header)
            sheet_module.merge_range(row_summary + 1, 2, row_summary + 2, 2, 'Standard', merge_row_rotate)
            sheet_module.set_row(row_summary + 1, 27)
            sheet_module.set_row(row_summary + 2, 27)
            sheet_module.merge_range(row_summary + 3, 2, row_summary + 4, 2, 'Project', merge_row_rotate)
            sheet_module.set_row(row_summary + 3, 21)
            sheet_module.set_row(row_summary + 4, 21)
            sheet_module.merge_range(row_summary + 1, 3, row_summary + 1, 9, 'Working hours per day', merge_value)
            sheet_module.merge_range(row_summary + 2, 3, row_summary + 2, 9, 'Working days per month', merge_value)
            sheet_module.merge_range(row_summary + 3, 3, row_summary + 3, 9, 'Total efforts in man-day unit', merge_value)
            sheet_module.merge_range(row_summary + 4, 3, row_summary + 4, 9, 'Total efforts in man-month unit', merge_value)

            modules_summary = self.env['estimation.module.summary'].search([('module_id', '=', module.id)])
            row_summary_value = row_summary + 1
            for summary in modules_summary[:-2]:
                sheet_module.write(row_summary_value, 10, summary.value, merge_value)
                row_summary_value += 1
            sheet_module.write(row_summary_value, 10, modules_summary[-2].value, merge_row_value)
            sheet_module.write(row_summary_value + 1, 10, modules_summary[-1].value, merge_row_value_bold)

            row_effort_dis = row_summary_value + 3
            sheet_module.merge_range(row_effort_dis, 1, row_effort_dis, 10, 'Effort distribution', merge_header)
            sheet_module.merge_range(row_effort_dis + 1, 2, row_effort_dis + 1, 8, 'Item', merge_row)
            sheet_module.write(row_effort_dis + 1, 9, 'Effort', merge_row)
            sheet_module.write(row_effort_dis + 1, 10, '%', merge_row)

            row_effort_value = row_effort_dis + 1
            effort_distributions = self.env['module.effort.activity'].search([('module_id', '=', module.id)])
            for effort in effort_distributions:
                row_effort_value += 1
                sheet_module.write(row_effort_value, 2, effort.sequence, format['border'])
                sheet_module.merge_range(row_effort_value, 3, row_effort_value, 8, effort.activity, merge_value)
                col_effort_dis_value = [
                    effort.effort,
                    str(effort.percent)+'%'
                ]
                for i, value in enumerate(col_effort_dis_value):
                    sheet_module.write(row_effort_value, 9 + i, value, merge_row_value)

            row_breakdown = row_effort_value + 3
            sheet_module.merge_range(row_breakdown, 1, row_breakdown, 10, 'Work Breakdown Structure & Estimate', merge_header)
            sheet_module.write(row_breakdown + 1, 1, '#', merge_activity)
            sheet_module.merge_range(row_breakdown + 1, 2, row_breakdown + 1, 9, 'Activities', merge_activity)
            sheet_module.write(row_breakdown + 1, 10, 'Expected (man-days)', merge_activity)
            
            config_activitys = self.env['config.activity'].search([('module_id', '=', module.id)])
            row_breakdown_value = row_breakdown + 1
            for breakdown in config_activitys:
                row_breakdown_value += 1
                sheet_module.write(row_breakdown_value, 1, breakdown.sequence, merge_breakdown)
                sheet_module.merge_range(row_breakdown_value, 2, row_breakdown_value, 8, breakdown.activity, merge_breakdown)
                sheet_module.write(row_breakdown_value, 9, breakdown.effort, merge_breakdown)
                sheet_module.write(row_breakdown_value, 10, '', border_right)
                activitys = self.env['module.breakdown.activity'].search([('activity_id', '=', breakdown.id)])
                for activity in activitys:
                    sheet_module.write(row_breakdown_value + 1, 1, '', border_left)
                    sheet_module.write(row_breakdown_value + 1, 2, str(breakdown.sequence)+'.'+str(activity.sequence), merge_value)
                    sheet_module.merge_range(row_breakdown_value + 1, 3, row_breakdown_value + 1, 9, activity.activity, merge_value)
                    sheet_module.write(row_breakdown_value + 1, 10, activity.mandays, merge_value)
                    row_breakdown_value += 1
            sheet_module.merge_range(row_breakdown_value + 1, 3, row_breakdown_value + 1, 9, 'Total (man-day)', merge_row)
            sheet_module.merge_range(row_breakdown_value + 1, 1, row_breakdown_value + 1, 2, '', border_left)
            sheet_module.write(row_breakdown_value + 1, 10, module.total_manday, merge_row)
            sheet_module.hide_gridlines(2)

