from odoo import models, fields


class ExcelReport(models.AbstractModel):
    _name = 'report.hr_attendances.report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Report Xlsx'
    
    
    
    def generate_xlsx_report(self, workbook, data, attendances):
        merge_format_header = workbook.add_format({
                            'bold': 1,
                            # 'font_size': 20,
                            'align': 'center',
                            'valign': 'vcenter'
                        })
        date_style = workbook.add_format({
                    'border': 1, 
                    'text_wrap': True, 
                    'num_format': 'dd-mm-yyyy'
                })
        bold = workbook.add_format({
                'bold': 1,
                'fg_color': '#76afe9',
                'border': 1
            })

        border = workbook.add_format({
                'border': 1, 
                'text_wrap': True
            })
        format = {
            "merge_header": merge_format_header,
            "bold": bold,
            "border": border,
            "datetime": date_style
        }
        self.action_export_data(workbook, attendances, format)


    def action_export_data(self, workbook, attendances, format):
        sheet = workbook.add_worksheet('Report Attandances')
        
        unapproved = attendances.filtered(lambda x: x.status_timeoff not in ['refuse', 'validate', 'validate1', False] and bool(x.public_holiday) == False)
        attendance_missing = attendances.filtered(lambda d: (bool(d.timeoff) == False or d.status_timeoff == 'refuse') and bool(d.public_holiday) == False)
        
        index_row, index_col = 5, 1
        tbl_row_start = index_row + 1
        last_col = index_col + 6
        last_row = 2
        sheet.set_column(0, 0, 1)
        sheet.set_column(index_col + 1, index_col + 7, 25)
        sheet.set_column(index_col, index_col, 4)
        if unapproved:
            tbl_title_unapproved = 'DANH SÁCH NHÂN VIÊN NGHỈ PHÉP CHƯA ĐƯỢC APPROVE'
            #syntax merge_range(firstRow, firstCol, lastRow, lastCol, data, format)
            sheet.merge_range(1, 1, last_row, last_col, tbl_title_unapproved, format['merge_header'])
        
            col_names = [
                'STT',
                'Employee',
                'Time Off Type',
                'Start Date',
                'End Date',
                'Duration',
                'Status'
            ]
            
            # insert title columns
            for i, name in enumerate(col_names):
                sheet.write(index_row, index_col + i, name, format['bold'])
            
            index = 0
            for tm in unapproved.timeoff:
                datas = [
                    int(index + 1),
                    tm.employee_id.name,
                    tm.holiday_status_id.display_name,
                    tm.date_start,
                    tm.date_end,
                    tm.duration_display,
                    dict(tm._fields['state'].selection).get(tm.state)
                ]
                for i, vals in enumerate(datas):
                    sheet.write(tbl_row_start, i + 1, vals, format['border'] if i not in [3, 4] else format['datetime'])
                
                tbl_row_start += 1
                index += 1
            
        if attendance_missing:
            tbl_title_attendance_missing = 'DANH SÁCH NHÂN VIÊN THIẾU DỮ LIỆU CHẤM CÔNG'
            first_col = last_col + 2 if unapproved else 4
            sheet.set_column(first_col, first_col, 4)
            sheet.set_column(index_col + 7, index_col + 10, 25)
            sheet.merge_range(1, first_col, last_row, first_col + 2, tbl_title_attendance_missing, format['merge_header'])
            col_names = [
                'STT',
                'Employee',
                'Date'
            ]
            for i, name in enumerate(col_names):
                sheet.write(index_row, first_col + i, name, format['bold'])
            index = 0
            for i, record in enumerate(attendance_missing):
                index_row += 1
                datas = [
                    int(index + 1),
                    record.employee_id.name,
                    record.date
                ]
                for i, vals in enumerate(datas):
                    sheet.write(index_row, first_col + i, vals, format['border'] if i != 2 else format['datetime'])
                index += 1
            
        sheet.hide_gridlines(2)
