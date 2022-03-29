from odoo import models, _

class HrPayslip(models.Model):
    _inherit = ['hr.payslip']


class PayslipXlsx(models.AbstractModel):
    _name = 'report.ds_export_excel.payslips_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, payslips):
        sheet = workbook.add_worksheet('Salary Slips Report'[:31])
        bold_center = workbook.add_format(
            {'bold': True, 'align': 'center', 'border': 1})
        currency_format = workbook.add_format({'num_format': '#,##0', 'border': 1})
        border = workbook.add_format({'border': 1})
        row, col = 0, 0
        col_names = [
            "Tên Nhân Viên",
            "Số tài khoản ngân hàng",
            "Tên CN ngân hàng",
            "Tiền công đoàn",
            "BHYT, BHXH, BHTN",
            "Thuế TNCN",
            "Lương OT",
            "Lương thực lĩnh",
        ]

        # Set Column Ranges
        sheet.set_column(col, col + 7, 20)

        for i, name in enumerate(col_names):
            sheet.write(row, col + i, name, bold_center)

        for obj in payslips:
            row += 1
            pcd = list(
                filter(lambda line: line['code'] == 'PCD', obj.line_ids))
            bh = list(filter(lambda line: line['code'] == 'BH', obj.line_ids))
            ttncn = [x for x in obj.line_ids if x.code == 'TTNCN']
            ot = list(filter(lambda line: line['code'] == 'OT', obj.line_ids))
            net = list(
                filter(lambda line: line['code'] == 'NET', obj.line_ids))

            col_values = [
                obj.employee_id.name,
                obj.employee_id.bank_account_id.acc_number or '',
                obj.employee_id.bank_account_id.bank_name or '',
                0 if len(pcd) == 0 else pcd[0].amount,
                0 if len(bh) == 0 else bh[0].amount,
                0 if len(ttncn) == 0 else ttncn[0].amount,
                0 if len(ot) == 0 else ot[0].amount,
                0 if len(net) == 0 else net[0].amount,
            ]

            for i, value in enumerate(col_values):
                if i in [3, 4, 5, 6, 7]:
                    sheet.write(row, col + i, value, currency_format)
                else:
                    sheet.write(row, col + i, value, border)
