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
    
        for overview in estimation.add_lines_overview[-1]:
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

        ls_fields = self.env['estimation.summary.totalcost'].get_field_effort({})
        max_col_tbl = 10
        if len(ls_fields) > 6:
            max_col_tbl += len(ls_fields) - 6
        else:
            max_col_tbl -= 6 - len(ls_fields)
            
        # table Total cost
        #syntax merge_range(firstRow, firstCol, lastRow, lastCol, data, format)
        sheet_summarize.merge_range(0, 0, 9, max_col_tbl,
            'COST SUMMARIZE FOR PROJECT '+(estimation.project_name).upper(), format['merge'])
        sheet_summarize.merge_range(12, 1, 12, max_col_tbl,
            'Total cost', format['merge_header'])
        sheet_summarize.merge_range('B14:B15', 'No', format['merge_header'])
        sheet_summarize.merge_range(
            'C14:C15', 'Components', format['merge_header'])
        sheet_summarize.merge_range(
            'D14:D15', 'Total Effort (MD)', format['merge_header'])
        sheet_summarize.merge_range(13, 4, 13, max_col_tbl - 1,
            'Detailed Effort (MD)', format['merge_header'])
        sheet_summarize.merge_range(13, max_col_tbl, 14, max_col_tbl,
            'COST ('+estimation.currency_id.name+')', format['merge_header'])

        # Set Column Ranges in Summarize
        sheet_summarize.set_column(0, 0, 1)
        sheet_summarize.set_column(1, 1, 10)
        sheet_summarize.set_column(2, 2, 25)
        sheet_summarize.set_column(3, max_col_tbl, 20)
        
        
        col_names_sheet_summarize = []
        total_effort_column = []
        total_effort_column.append(sum(tt_cost.total_effort for tt_cost in estimation.add_lines_summary_totalcost))
        for field in ls_fields:
            # get title column
            col_names_sheet_summarize.append(ls_fields[field])
            
            # compute total effort column
            total_effort_column.append(sum(tt_cost[field] for tt_cost in estimation.add_lines_summary_totalcost))
        
        total_effort_column.append(sum(tt_cost.cost for tt_cost in estimation.add_lines_summary_totalcost))

        row_header_summarize, col_header_summarize = 14, 4
        for i, name in enumerate(col_names_sheet_summarize):
            sheet_summarize.write(
                row_header_summarize, col_header_summarize + i, name, format['merge_header'])

        row_data_summarize, col_data_summarize = 14, 1
        no = 0
        for total in estimation.add_lines_summary_totalcost:
            row_data_summarize += 1
            no += 1
            col_values_summarize = [
                no,
                total.name,
                total.total_effort,
            ]
            for field in ls_fields:
                col_values_summarize.append(total[field])
            col_values_summarize.append(total.cost)

            for i, value in enumerate(col_values_summarize):
                sheet_summarize.write(
                    row_data_summarize, col_data_summarize + i, value, format['border'])
                
        sheet_summarize.write(row_data_summarize + 1, 2, 'Total', format['bold'])
        for i, value in enumerate(total_effort_column):
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

        # get cost rate from last module
        if len(estimation.add_lines_module) != 0:
            costrates = estimation.env['estimation.summary.costrate'].search([('estimation_id', '=', estimation.id), 
                                                                            ('key_primary', '=', estimation.add_lines_module[-1].key_primary)],
                                                                            order="sequence")
            for costrate in costrates:
                row_cost_rate += 1
                col_value_cost_rate = [
                    costrate.sequence,
                    costrate.job_position.job_position,
                    costrate.yen_month,
                    costrate.yen_day
                ]
                for i, value in enumerate(col_value_cost_rate):
                    sheet_summarize.write(
                        row_cost_rate, col_cost_rate + i, value, format['border'])

        sheet_summarize.hide_gridlines(2)    

    def sheetResourcePlan(self, workbook, estimation, format):
        sheet_resource = workbook.add_worksheet('Resource Plan')
        sheet_resource.insert_image(
            'C3', 'custom-addons/ds_project_estimation/static/description/d-soft.jpg', {'x_offset': 450, 'y_offset': 0.5})
        
        ls_fields = self.env['estimation.summary.totalcost'].get_field_effort({})
        max_col_tbl = 9
        if len(ls_fields) > 6:
            max_col_tbl += len(ls_fields) - 6
        else:
            max_col_tbl -= 6 - len(ls_fields)
        
        sheet_resource.set_column(0, 0, 1)
        sheet_resource.set_column(1, 1, 10)
        sheet_resource.set_column(2, max_col_tbl, 20)
        sheet_resource.set_column(max_col_tbl + 1, max_col_tbl + 4, 20)
        sheet_resource.set_column(max_col_tbl + 5, 500, 2)
        
        #syntax merge_range(firstRow, firstCol, lastRow, lastCol, data, format)
        sheet_resource.merge_range(0, 0, 9, max_col_tbl,
            'RESOURCE PLAN FOR PROJECT '+(estimation.project_name).upper(), format['merge'])
        
        sheet_resource.merge_range(12, 1, 12, max_col_tbl,
            'Total effort', format['merge_header'])
        
        sheet_resource.merge_range('B14:B15', 'No', format['merge_header'])
        
        sheet_resource.merge_range('C14:C15', 
            'Components', format['merge_header'])
        
        sheet_resource.merge_range('D14:D15', 
            'Total Effort (MD)', format['merge_header'])
        
        sheet_resource.merge_range(13, 4, 13, max_col_tbl,
            'Detailed Effort (MD)', format['merge_header'])

        format_center = workbook.add_format(
                {'align': 'center', 'border': 1})
        
        format_total = workbook.add_format({'align': 'center', 'border': 1, 'fg_color': '#E0E3E3', 'bold': True})
        col_names_sheet_resource = self.get_title_columns()
        row_header_resource, col_header_resource = 14, 4
        for i, name in enumerate(col_names_sheet_resource):
            sheet_resource.write(
                row_header_resource, col_header_resource + i, name, format['merge_header'])

        row_data_total_effort, col_data_total_effort = 14, 1
        for resource in estimation.add_lines_resource_effort:
            row_data_total_effort += 1
            col_values = [
                resource.sequence,
                resource.name,
                resource.total_effort,
            ]
            for field in ls_fields:
                col_values.append(resource[field])
            
            for i, value in enumerate(col_values):
                sheet_resource.write(
                    row_data_total_effort, col_data_total_effort + i, value, format['border'])
        
        # print result effort planning resource
        for rs in estimation.resource_plan_result_effort:
            row_data_total_effort += 1
            rs_values = [
                '',
                rs.name,
                rs.total_effort
            ]
            for field in ls_fields:
                rs_values.append(rs[field])
            
            for i, value in enumerate(rs_values):
                cnt = 1 if i == 0 else i
                sheet_resource.write(
                    row_data_total_effort, col_data_total_effort + cnt, value, format['bold'])


        # Print gantt
        row_data_chartt , col_data_chartt = 12, max_col_tbl + 2
        
        sheet_resource.merge_range(row_data_chartt, col_data_chartt, row_data_chartt, col_data_chartt + 1, 'Resource Plan', format['merge_header'])
        sheet_resource.write(row_data_chartt + 1, col_data_chartt, 'Resource', format['merge_header'])
        sheet_resource.write(row_data_chartt + 1, col_data_chartt + 1, 'Resource Count', format['merge_header'])
        sheet_resource.write(row_data_chartt + 1, col_data_chartt + 2, 'Duration (Month)', format['merge_header'])

        count = 0
        index = 0
        cnt_job_pos = len(estimation.gantt_view_line) + row_data_chartt + 2
        
        for item in estimation.gantt_view_line:
            sheet_resource.write(row_data_chartt + 2 + index, col_data_chartt, item.job_position_id.job_position, format['border'])
            sheet_resource.write(row_data_chartt + 2 + index, col_data_chartt + 2, item.value_man_month, format_center)
            
            # print Resource Count
            if (int(str(round(item.value_man_month, 1)).split('.')[1])) >= 5:
                sheet_resource.write(row_data_chartt + 2 + index, col_data_chartt + 1, math.ceil(item.value_man_month), format_center)
                count += math.ceil(item.value_man_month)
            else:
                sheet_resource.write(row_data_chartt + 2 + index, col_data_chartt + 1, round(item.value_man_month), format_center)
                count += round(item.value_man_month)
            index += 1
        sheet_resource.write(cnt_job_pos, col_data_chartt, 'Total', format_total)
        sheet_resource.write(cnt_job_pos, col_data_chartt + 1, count, format_total)
            
        # Paint gantt
        month = 0
        if len(estimation.gantt_view_line) != 0:
            month += math.ceil(max(item.value_man_month for item in estimation.gantt_view_line))
        col = 0
        num_days = 10
        
        col_start_gantt = col_data_chartt + 3
        for i in range(1, month + 1):                       
            sheet_resource.merge_range(
                row_data_chartt + 1, 
                col_start_gantt + col, 
                row_data_chartt + 1, 
                col_data_chartt + col + num_days + 2, 
                'Month - ' + str(i), format['merge_header'])
            col += num_days

        gantt_format = workbook.add_format({
            'border': 1,
            'fg_color': 'green'})

        cnt = 0
        for vals in estimation.gantt_view_line:
            if math.ceil(vals.value_man_month * 10) > 0:
                sheet_resource.merge_range(
                    row_data_chartt + 2 + cnt, col_start_gantt, 
                    row_data_chartt + 2 + cnt, col_start_gantt - 1 + math.ceil(vals.value_man_month * 10), 
                    '', gantt_format)
            else:
                sheet_resource.merge_range(
                    row_data_chartt + 2 + cnt, col_start_gantt, 
                    row_data_chartt + 2 + cnt, col_start_gantt + math.ceil(vals.value_man_month * 10), 
                    '', gantt_format)
            cnt += 1
        sheet_resource.hide_gridlines(2)
            
    def sheetModule(self, workbook, estimation, format):
        # modules = estimation.env['estimation.module'].search([('estimation_id','=',estimation.id)])

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

        for module in estimation.add_lines_module:
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
            # assumptions = self.env['estimation.module.assumption'].search([('module_id', '=', module.id)])
            # if assumptions:
            for ass in module.module_assumptions[:-1]:
                sheet_module.merge_range(row_assumption, 1, row_assumption, 2, 'Å', format_icon)
                sheet_module.merge_range(
                    row_assumption , 3, row_assumption, 10, ass.assumption, border_right)
                row_assumption += 1
            
            sheet_module.merge_range(row_assumption, 1, row_assumption, 2, 'Å', format_icon_border_bottom)
            sheet_module.merge_range(row_assumption, 3, row_assumption, 10, module.module_assumptions[:-1].assumption, border_bottom)

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

            # modules_summary = self.env['estimation.module.summary'].search([('module_id', '=', module.id)])
            row_summary_value = row_summary + 1
            for summary in module.module_summarys[:-2]:
                sheet_module.write(row_summary_value, 10, summary.value, merge_value)
                row_summary_value += 1
            sheet_module.write(row_summary_value, 10, module.module_summarys[-2].value, merge_row_value)
            sheet_module.write(row_summary_value + 1, 10, module.module_summarys[-1].value, merge_row_value_bold)

            row_effort_dis = row_summary_value + 3
            sheet_module.merge_range(row_effort_dis, 1, row_effort_dis, 10, 'Effort distribution', merge_header)
            sheet_module.merge_range(row_effort_dis + 1, 2, row_effort_dis + 1, 8, 'Item', merge_row)
            sheet_module.write(row_effort_dis + 1, 9, 'Effort', merge_row)
            sheet_module.write(row_effort_dis + 1, 10, '%', merge_row)

            row_effort_value = row_effort_dis + 1
            # effort_distributions = self.env['module.effort.activity'].search([('module_id', '=', module.id)])
            for effort in module.module_effort_activity:
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
            
            # config_activitys = self.env['config.activity'].search([('module_id', '=', module.id)])
            row_breakdown_value = row_breakdown + 1
            for breakdown in module.module_config_activity:
                row_breakdown_value += 1
                sheet_module.write(row_breakdown_value, 1, breakdown.sequence, merge_breakdown)
                sheet_module.merge_range(row_breakdown_value, 2, row_breakdown_value, 8, breakdown.activity, merge_breakdown)
                sheet_module.write(row_breakdown_value, 9, breakdown.effort, merge_breakdown)
                sheet_module.write(row_breakdown_value, 10, '', border_right)
                # activitys = self.env['module.breakdown.activity'].search([('activity_id', '=', breakdown.id)])
                for activity in breakdown.add_lines_breakdown_activity:
                    sheet_module.write(row_breakdown_value + 1, 1, '', border_left)
                    sheet_module.write(row_breakdown_value + 1, 2, str(breakdown.sequence)+'.'+str(activity.sequence), merge_value)
                    sheet_module.merge_range(row_breakdown_value + 1, 3, row_breakdown_value + 1, 9, activity.activity, merge_value)
                    sheet_module.write(row_breakdown_value + 1, 10, activity.mandays, merge_value)
                    row_breakdown_value += 1
            sheet_module.merge_range(row_breakdown_value + 1, 3, row_breakdown_value + 1, 9, 'Total (man-day)', merge_row)
            sheet_module.merge_range(row_breakdown_value + 1, 1, row_breakdown_value + 1, 2, '', border_left)
            sheet_module.write(row_breakdown_value + 1, 10, module.total_manday, merge_row)
            sheet_module.hide_gridlines(2)



    def get_title_columns(self):
        ls_fields = self.env['estimation.summary.totalcost'].get_field_effort({})
        col_names_sheet_summarize = []
        for field in ls_fields:
            # get title column
            col_names_sheet_summarize.append(ls_fields[field])
        return col_names_sheet_summarize