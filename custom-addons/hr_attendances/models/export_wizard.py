from odoo import models, fields
from datetime import date, datetime, timedelta
import calendar
import pandas as pd
from odoo.tools import date_utils
import json, pytz
import xlsxwriter, io
from xlsxwriter.utility import xl_rowcol_to_cell
from odoo.exceptions import ValidationError

LIST_MONTHS = [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')]

# VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')
# UTC_TZ = pytz.timezone('UTC')
# DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
OFF = "OFF"
PN = "PN"
CONFIRM = "CONFIRM"
HOUR_SMALL = 4


class ExportWizard(models.TransientModel):
    _name = 'export.wizard'
    _description = 'Export Excel Wizard'
    
    
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    
    
    
    
    def export_excel(self):
        if self.start_date > self.end_date:
            raise ValidationError("The start date must be less than the end date!")
        if (self.end_date - self.start_date).days <= 7:
            raise ValidationError("The export time is too short!")
        cnt_days = (self.end_date - self.start_date).days + 1
        allowed_companies = self.env.context.get('allowed_company_ids', [])
        datas = {
            'end_month': cnt_days,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'allowed_companies': allowed_companies
        }
        kwargs = {
            'model': self._name,
            'output_format': 'xlsx',
            'options': json.dumps(datas, default=date_utils.json_default),
        }
        kwargs = json.dumps(kwargs)

        return {
            'type': 'ir.actions.act_url',
            'url': f'/api/attendance/xlsx_reports?kw={kwargs}',
            'target': 'new'
        }
    
    
    def handle_data_export(self, attendances):
        datas = {}
        pseudo_records = {}
        fail_record = {}
        for att in attendances:
            if att[3]is None and att[4] is None:
                datas[str(att[0])] = {
                    "name": att[1],
                    "job_title": att[6],
                    "check_in": att[3],
                    "check_out": att[4],
                    "worked_hours": att[5]
                }
                continue
            
            if att[3] is None or att[4] is None:
                day_vals = {
                    "name": att[1],
                    "job_title": att[6],
                    "check_in": att[3],
                    "check_out": att[4],
                    "worked_hours": 0
                }
                day_number = str(att[3].day) + "/" + str(att[3].month) if att[3] else str(att[4].day) + "/" + str(att[4].month) 
                if str(att[0]) not in datas:
                    datas[str(att[0])] = {
                        day_number: day_vals
                    }
                else:
                    if day_number not in datas[str(att[0])]:
                        datas[str(att[0])][day_number]= day_vals
                continue
            
            endpoint = att[4]
            worked_hours = att[5]
            condition = (att[4] - att[4].replace(hour=0, minute=0, second=0)).total_seconds() / 3600.0
            # in case: period of attendance record between two dates -> separate it into two records for two dates.
            if att[3].day < att[4].day and condition > 0:
                endpoint = att[4].replace(hour=0, minute=0, second=0)
                delta = att[4] - endpoint
                worked_hours_remaining = delta.total_seconds() / 3600.0
                worked_hours -= worked_hours_remaining
                day_vals = {
                    "name": att[1],
                    "job_title": att[6],
                    "check_in": endpoint,
                    "check_out": att[4],
                    "worked_hours": worked_hours_remaining
                }
                day_number = str(endpoint.day) + "/" + str(endpoint.month)
                if str(att[0]) not in pseudo_records:
                    pseudo_records[str(att[0])] = {
                        day_number: day_vals
                       
                    }
                else:
                    if day_number not in pseudo_records[str(att[0])]:
                        pseudo_records[str(att[0])][day_number] = day_vals
                    else:
                        # case data failed - duplidate time
                        # pseudo_records[str(att[0])][str(endpoint.day)]["worked_hours"] += worked_hours_remaining
                        pseudo_records[str(att[0])][day_number]["worked_hours"] = 0
                        if str(att[0]) in fail_record:
                            fail_record[str(att[0])].append(str(att[3].day) + "/" + str(att[3].month))
                        else:
                            fail_record[str(att[0])] = [str(att[3].day) + "/" + str(att[3].month)]
            
            day_vals = {
                "name": att[1],
                "job_title": att[6],
                "check_in": att[3],
                "check_out": endpoint,
                "worked_hours": worked_hours
            }
            day_number = str(att[3].day) + "/" + str(att[3].month)
            if str(att[0]) not in datas:
                datas[str(att[0])] = {
                    day_number: day_vals
                }
            else:
                if day_number not in datas[str(att[0])]:
                    datas[str(att[0])][day_number] = day_vals
                else:
                    datas[str(att[0])][day_number]["worked_hours"] += worked_hours
                    
        for key, vals in pseudo_records.items():
            for day, val in vals.items():
                if day not in datas[key]:
                    datas[key][day] = val
                else:
                    datas[key][day]["worked_hours"] += val["worked_hours"]
        
        result = []
        for key, vals in datas.items():
            if type(vals[list(vals.keys())[0]]) != dict:
                result.append({
                        'employee_id': int(key),
                        'name': vals['name'],
                        'job_title': vals['job_title'],
                        'day_working': vals['check_in'],
                        'worked_hours': vals['worked_hours'],
                    })
                continue
            is_failed = fail_record.get(str(key))
            for day, val in vals.items():
                day_failed = day in is_failed if is_failed else False
                result.append({
                    'employee_id': int(key),
                    'name': val['name'],
                    'job_title': val['job_title'],
                    'day_working': day,
                    'worked_hours': val['worked_hours'] if not day_failed else 0,
                })
        
        return result
            
    
    def generate_xlsx_report(self, data, response, allowed_companies):
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Attendance Report')

        format = {
                'align': 'center',
                'bold': True, 
                'font_size': 11,
                'font_name': 'Times New Roman',
                'valign': 'vcenter',
        }
        border_default = {
            'border': 0, 
            'bottom': 1,
            'right': 1,
            'left': 1,
            'top': 1
        }
        off_format = {
            'bg_color': '#BFBFBF',
            **format,
            **border_default
        }
        cell_default = {
            **format,
            **border_default,
            'bold': False,
        }
        day_format = {
            'bg_color': 'afabab',
            'bottom': 1,
            'right': 1,
            'left': 1,
            **border_default
        }
        
        header_footer = {
            'bg_color': 'd0d0d0',
            'border': 0, 
            'bottom': 2,
            'right': 2,
            'left': 2,
            'top': 2,
            **format
        }

        companies = self.env['res.company'].search([('id', 'in', allowed_companies)])
        companies = ", ".join([item.name for item in companies])
        B1 = f"Bang Cham Cong {companies} {data['start_date']} - {data['end_date']}"
        self.merge_range(sheet, 0, 0, 1, 6, B1, self.format(workbook, format))
        
        A6 = "ST\nT"
        self.set_column(sheet, 0, 0, 3)
        self.merge_range(sheet, 3, 5, 0, 0, A6, self.format(workbook, header_footer))
        
        B6 = "Họ và tên"
        self.set_column(sheet, 1, 1, 30)
        self.merge_range(sheet, 3, 5, 1, 1, B6, self.format(workbook, header_footer))
        
        C6 = "Chức danh"
        self.set_column(sheet, 2, 2, 30)
        self.merge_range(sheet, 3, 5, 2, 2, C6, self.format(workbook, header_footer))
        
        D6 = "Ca làm\nviệc"
        self.set_column(sheet, 3, 3, 7)
        self.merge_range(sheet, 3, 5, 3, 3, D6, self.format(workbook, header_footer))
        
        
        # Days Column data
        start_index_col = 4
        end_index_col = data['end_month'] + start_index_col - 1
        working_day = self.working_days(data['start_date'], data['end_date'])
        self.merge_range(sheet, 1, 1, start_index_col + 10, end_index_col - 10, f"Công tiêu chuẩn: {working_day}", self.format(workbook, format))
        
        date_from = f"Từ ngày {data['start_date']}"
        self.merge_range(sheet, 2, 2, start_index_col + 6, start_index_col + 12, date_from, self.format(workbook, format))
        date_to = f"Đến ngày {data['end_date']}"
        self.merge_range(sheet, 2, 2, end_index_col - 12, end_index_col - 6, date_to, self.format(workbook, format))
        
        E4 = "Chấm công ngày"
        self.merge_range(sheet, 3, 3, start_index_col, end_index_col, E4, self.format(workbook, header_footer))
        
        self.set_column(sheet, start_index_col, end_index_col, 6)
        start_date_obj = datetime.strptime(data['start_date'], DATE_FORMAT)
        day_indexs = {}
        for i in range(data['end_month']):
            dayobj = start_date_obj + timedelta(days=i)
            day_number = str(dayobj.day) + "/" + str(dayobj.month)
            day_indexs[day_number] = i + 1
            
            sheet.write(4, start_index_col + i, str(dayobj.day), self.format(workbook, header_footer, **day_format))
            sheet.write(5, start_index_col + i, '', self.format(workbook, header_footer, **{**day_format, 'bg_color': 'd0d0d0', 'bottom': 2}))
        
        # set height row
        sheet.set_row(5, 40)
        
        self.set_column(sheet, end_index_col + 1, end_index_col + 3, 10)
        final_col = "Ngày công/giờ làm (chuẩn)"
        self.merge_range(sheet, 3, 3, end_index_col + 1, end_index_col + 3, final_col, self.format(workbook, header_footer))
        self.merge_range(sheet, 4, 4, end_index_col + 1, end_index_col + 3, "Chính thức", self.format(workbook, header_footer))
        sheet.write(5, end_index_col + 1, "Tổng Giờ\nLàm Việc", self.format(workbook, header_footer))
        sheet.write(5, end_index_col + 2, "Tổng Công\nLàm Việc", self.format(workbook, header_footer))
        sheet.write(5, end_index_col + 3, "Phép năm", self.format(workbook, header_footer))
        
        self.main_action_export_data(data, day_indexs, sheet, workbook, off_format, cell_default, header_footer, border_default, format)
        
        
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        
        
    
    def main_action_export_data(self, data, day_indexs, sheet, workbook, off_format, cell_default, header_footer, border_default, format):
        wd_format = {
            'bg_color': 'e2f0d9',
            'bold': False
        }
        fmLeft = {
            'align': 'left'
        }
        fmlastCol = {
            'align': 'right',
            'num_format': '0.00'
        }
        fmLRBorder = {
            **fmlastCol,
            'right': 2,
            'left': 2
        }
        fm_bottom = {
            'valign': 'bottom',
            'top': 1,
            'right': 1,
            'left': 1,
            'num_format': '0.00'
        }
        border_b = {
                'left': 2,
                'right': 2
        }
        attendances = data['data']
        row = 6
        boxRowFirst = row
        boxColFirst = 4
        boxColLast = boxColFirst + data['end_month'] - 1
        boxRowLast = len({item['employee_id'] for item in attendances}) + row - 1
        
        # write all cells to default values OFF
        for r in range(boxRowFirst, boxRowLast + 1):
            for c in range(boxColFirst, boxColLast + 1):
                sheet.write_string(r, c, OFF, self.format(workbook, off_format))
        
        index = 0
        employee_writeds = {}   # {"employee_id": "row_index"}
        sum_columns = {str(i): 0 for i in range(1, boxColLast + 1)}
        sum_rows = {}
        for item in attendances:
            employee_id = str(item['employee_id'])
            if employee_id in sum_rows:
                sum_rows[employee_id] += item['worked_hours']
            else:
                hours = item['worked_hours'] if item['worked_hours'] else 0
                sum_rows[employee_id] = hours
        
        bg_small_hour = {'bg_color': 'ffd966'}
        for record in attendances:
            employee_id = str(record['employee_id'])
            row_active = employee_writeds.get(employee_id)
            if not row_active:
                employee_writeds[employee_id] = row
                row_active = row
                sheet.write(row_active, 0, str(index + 1), self.format(workbook, cell_default))
                sheet.write(row_active, 3, '', self.format(workbook, cell_default, **{**border_default, **fmLRBorder, 'align': 'left'}))
                index += 1
                row += 1
                
            for key, vals in record.items():
                if key == 'name':
                    sheet.write(row_active, 1, vals, self.format(workbook, cell_default, **wd_format, **fmLeft))
                elif key == 'job_title':
                    sheet.write(row_active, 2, vals, self.format(workbook, cell_default, **fmLeft))
                elif key == 'day_working':
                    hours = record['worked_hours'] if record['worked_hours'] else 0
                    
                    # off all month
                    if not vals:
                        self.handle_user_off_all_month(sheet, row_active, [boxColFirst, boxColLast], workbook, cell_default)
                    else:
                        fm_hour = {
                            'num_format': '0.00', 
                            **wd_format
                        }
                        if hours < HOUR_SMALL:
                            fm_hour = {
                                **fm_hour,
                                **bg_small_hour 
                            }
                            
                        sheet.write_number(row_active, 3 + day_indexs.get(vals), hours, self.format(workbook, cell_default, **fm_hour))
                        sum_columns[str(day_indexs.get(vals))] += hours
                else:
                    continue
                
            workingday = round(sum_rows[employee_id]/8, 2)
            start_cell = xl_rowcol_to_cell(row_active, boxColFirst)
            end_cell = xl_rowcol_to_cell(row_active, boxColLast)
            formula = f'=IF(COUNTIF({start_cell}:{end_cell}, "{PN}")=0, "-", COUNTIF({start_cell}:{end_cell}, "{PN}"))'
            sheet.write_number(row_active, boxColLast + 1, sum_rows[employee_id], self.format(workbook, cell_default, **{**fmLRBorder, 'italic': True}))
            sheet.write_number(row_active, boxColLast + 2, workingday, self.format(workbook, cell_default, **{'font_color':'ff0000', 'italic': True, **fmlastCol}))
            sheet.write_formula(row_active, boxColLast + 3, formula, self.format(workbook, cell_default, **{**fmlastCol, 'italic': True}))
            
            # calculate sum of last column
        total_hours = sum([sum_rows[key] for key in sum_rows])
        sum_columns[str(data['end_month'] + 1)] += total_hours
        sum_columns[str(data['end_month'] + 2)] += round(total_hours/8, 2)
        

        self.merge_range(sheet, boxRowLast + 1, boxRowLast + 1, 0, 2, 'Tổng cộng', self.format(workbook, header_footer, **{**fm_bottom, 'valign': 'vcenter'}))
        sheet.write(boxRowLast + 1, 3, '', self.format(workbook, header_footer, **{**fm_bottom, 'left': 2, 'right': 2}))
        column_avg = data['end_month'] + 4
        for col in range(1, column_avg):
            val_sum = sum_columns.get(str(col)) if sum_columns.get(str(col)) else 0
            bd = {}
            if col > column_avg - 4:
                fm_bottom['align'] = 'right'
                if col == column_avg - 3:
                    bd = border_b
            
            sheet.write_number(boxRowLast + 1, col + 3, val_sum, self.format(workbook, header_footer, **{**fm_bottom, **bd}))

        # add formula to final cell
        start_cell = xl_rowcol_to_cell(boxRowFirst, boxColLast + 3)
        end_cell = xl_rowcol_to_cell(boxRowLast, boxColLast + 3)
        formula = f"=SUM({start_cell}:{end_cell})"
        sheet.write_formula(boxRowLast + 1, boxColLast + 3, formula, self.format(workbook, header_footer, **{**fm_bottom, **bd}))
        
        sheet.set_row(boxRowLast + 1, 25)
        sheet.set_row(boxRowLast + 3, 25)
        sheet.set_row(boxRowLast + 4, 25)
        sheet.write(boxRowLast + 3, 1, OFF, self.format(workbook, format, **{'bg_color': '#BFBFBF'}))
        sheet.write(boxRowLast + 3, 2, 'Nghỉ ca', self.format(workbook, format, **{'bold': True}))
        sheet.write(boxRowLast + 4, 1, PN, self.format(workbook, format, **{'bg_color': '548235'}))
        sheet.write(boxRowLast + 4, 2, 'Phép năm', self.format(workbook, format, **{'bold': True}))
        sheet.write(boxRowLast + 5, 1, CONFIRM, self.format(workbook, format, **{'bg_color': 'ffd966'}))
        sheet.write(boxRowLast + 5, 2, f'Thiếu giờ làm (<{HOUR_SMALL}h)', self.format(workbook, format, **{'bold': True}))
        
        
        
    def handle_user_off_all_month(self, sheet, row_active, col, workbook, cell_default):
        for col in range(col[0], col[1] + 1):
            sheet.write_string(row_active, col, '', self.format(workbook, cell_default))
        
    def merge_range(self, sheet, firstRow, lastRow, firstCol, lastCol, content, format):
        return sheet.merge_range(firstRow, firstCol, lastRow, lastCol, content, format)
        
    def set_column(self, sheet, fromIndexColumn, toIndexColumn, width):
        """Set width of column"""
        return sheet.set_column(fromIndexColumn, toIndexColumn, width)
    
    def format(self, workbook, format, **kwargs):
        """Add format to workbook"""
        return workbook.add_format({**format, **kwargs})
    
    def working_days(self, start_date, end_date):
        working_days = pd.date_range(start=start_date, end=end_date, freq='B')    # 'B' stands for business day
        return len(working_days)

    def attendance_query(self, company_ids, table_mode, start_date, end_date):
        query = f"""
                WITH attendances AS (
                    SELECT
                        employee_id,
                        location_date,
                        check_in AT TIME ZONE 'UTC' AT TIME ZONE '{self.env.user.tz}' AS check_in,
                        check_out AT TIME ZONE 'UTC' AT TIME ZONE '{self.env.user.tz}' AS check_out,
                        worked_hours
                    FROM {table_mode}
                    WHERE location_date BETWEEN '{start_date}' AND '{end_date}'
                    ORDER BY check_in DESC
                ),
                departure_dates AS (
                    SELECT 
                        employee_id,
                        MAX(departure_date) AS departure_date
                    FROM hr_departure_wizard
                    GROUP BY employee_id
                )
                SELECT
                    e.id AS employee_id,
                    e.name,
                    a.location_date,
                    a.check_in,
                    a.check_out,
                    a.worked_hours,
                    e.job_title
                FROM hr_employee e
                LEFT JOIN attendances a
                    ON a.employee_id = e.id
                LEFT JOIN departure_dates d
	                ON d.employee_id = e.id
                WHERE (e.active = True
                    OR (e.active = False 
                        AND (d.departure_date BETWEEN '{start_date}' AND '{end_date}'
                            OR (d.departure_date >= '{start_date}' and d.departure_date >= '{end_date}')
                        )
                    ))
                    AND e.company_id IN {tuple(company_ids + [0])}
                ORDER BY e.name, a.check_in desc;
        """
        
        self._cr.execute(query)
        attendances = self._cr.fetchall()
        return attendances


    def compute_attendance_view_mode(self, allowed_companies):
        companies = self.env['res.company'].search([('id', 'in', allowed_companies)])
        single_mode = []
        multi_mode = []
        
        for item in companies:
            if item.attendance_view_type:
                multi_mode.append(item.id)
            else:
                single_mode.append(item.id)
        
        return single_mode, multi_mode
            

    def action_get_data(self, start_date, end_date, allowed_companies):
        single_mode, multi_mode = self.compute_attendance_view_mode(allowed_companies)
        attendances = []
        if single_mode:
            single_mode = self.attendance_query(single_mode, "hr_attendance", start_date, end_date)
        if multi_mode:
            multi_mode = self.attendance_query(multi_mode, "hr_attendance_pesudo", start_date, end_date)
        
        attendances.extend(single_mode)
        attendances.extend(multi_mode)
        
        return self.handle_data_export(attendances)
        