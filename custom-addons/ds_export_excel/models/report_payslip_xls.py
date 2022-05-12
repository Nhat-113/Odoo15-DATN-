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
            "Phụ cấp không chịu thuế",
            "Phụ cấp chịu thuế",
            "Lương",
            "Ngày công trong tháng",
            "Bình quân ngày công",
            "Ngày nghỉ không lương",
            "Ngày công tính lương",
            "Lương trong tháng",
            "Thời Gian OT 100% Lương",
            "Thời Gian OT 150% Lương",
            "Thời Gian OT 200% Lương",
            "Thời Gian OT 300% Lương",
            "Lương OT",
            "Khấu trừ",
            "Khoản bổ sung/Tạm ứng",
            "Tiền công đoàn",
            "Lương OT chịu thuế",
            "Tổng thu nhâp trong tháng",
            "BHYT, BHXH, BHTN",
            "Giảm trừ gia cảnh và tiêu dùng cá nhân",
            "Lương tháng 13/Bonus",
            "Thu nhập chịu thế theo lương",
            "Thuế TNCN theo lương",
            "Thuế TNCN theo lương tháng 13/bonus",
            "Lương thực lĩnh",
        ]

        # Set Column Ranges
        sheet.set_column(col, col + 28, 20)
        sheet.set_column(3, 3, 23)
        sheet.set_column(8, 8, 21)
        sheet.set_column(11, 14, 25)
        sheet.set_column(17, 17, 25)
        sheet.set_column(20, 20, 25)
        sheet.set_column(22, 22, 35)
        sheet.set_column(24, 24, 30)
        sheet.set_column(25, 25, 23)
        sheet.set_column(26, 26, 35)

        for i, name in enumerate(col_names):
            sheet.write(row, col + i, name, bold_center)

        for obj in payslips:
            row += 1
            pcd = list(
                filter(lambda line: line['code'] == 'PCD', obj.line_ids))
            bh = list(filter(lambda line: line['code'] == 'BH', obj.line_ids))
            ot = list(filter(lambda line: line['code'] == 'OT', obj.line_ids))
            pck = list(filter(lambda line: line['code'] == 'PCK', obj.line_ids))
            pc = list(filter(lambda line: line['code'] == 'PC', obj.line_ids))
            basic = list(filter(lambda line: line['code'] == 'Basic', obj.line_ids))
            nctt = list(filter(lambda line: line['code'] == 'NCTT', obj.line_ids))
            bqnc = list(filter(lambda line: line['code'] == 'BQNC', obj.line_ids))
            nnkl = list(filter(lambda line: line['code'] == 'NNKL', obj.line_ids))
            nctte = list(filter(lambda line: line['code'] == 'NCTTE', obj.line_ids))
            tl = list(filter(lambda line: line['code'] == 'TL', obj.line_ids))
            tot1 = list(filter(lambda line: line['code'] == 'TOT1', obj.line_ids))
            tot2 = list(filter(lambda line: line['code'] == 'TOT2', obj.line_ids))
            tot3 = list(filter(lambda line: line['code'] == 'TOT3', obj.line_ids))
            tot4 = list(filter(lambda line: line['code'] == 'TOT4', obj.line_ids))
            ltu = list(filter(lambda line: line['code'] == 'LTU', obj.line_ids))
            kbs = list(filter(lambda line: line['code'] == 'KBS', obj.line_ids))
            otct = list(filter(lambda line: line['code'] == 'OTCT', obj.line_ids))
            ttntt = list(filter(lambda line: line['code'] == 'TTNTT', obj.line_ids))
            gtgc = list(filter(lambda line: line['code'] == 'GTGC', obj.line_ids))
            lbn = list(filter(lambda line: line['code'] == 'LBN', obj.line_ids))
            tnc = list(filter(lambda line: line['code'] == 'TNC', obj.line_ids))
            ttncnbn = list(filter(lambda line: line['code'] == 'TTNCNBN', obj.line_ids))

            if obj.struct_id.id == 1:
                net = list(
                    filter(lambda line: line['code'] == 'NET', obj.line_ids))
                ttncn = [x for x in obj.line_ids if x.code == 'TTNCN']
            elif obj.struct_id.id == 2:
                net = list(
                    filter(lambda line: line['code'] == 'NET1', obj.line_ids))
                ttncn = [x for x in obj.line_ids if x.code == 'TTNCN1']

            col_values = [
                obj.employee_id.name,
                obj.employee_id.bank_account_id.acc_number or '',
                obj.employee_id.bank_account_id.bank_name or '',
                0 if len(pck) == 0 else pck[0].amount,
                0 if len(pc) == 0 else pc[0].amount,
                0 if len(basic) == 0 else basic[0].amount,
                0 if len(nctt) == 0 else nctt[0].amount,
                0 if len(bqnc) == 0 else bqnc[0].amount,
                0 if len(nnkl) == 0 else nnkl[0].amount,
                0 if len(nctte) == 0 else nctte[0].amount,
                0 if len(tl) == 0 else tl[0].amount,
                0 if len(tot1) == 0 else tot1[0].amount,
                0 if len(tot2) == 0 else tot2[0].amount,
                0 if len(tot3) == 0 else tot3[0].amount,
                0 if len(tot4) == 0 else tot4[0].amount,
                0 if len(ot) == 0 else ot[0].amount,
                0 if len(ltu) == 0 else ltu[0].amount,
                0 if len(kbs) == 0 else kbs[0].amount,
                0 if len(pcd) == 0 else pcd[0].amount,
                0 if len(otct) == 0 else otct[0].amount,
                0 if len(ttntt) == 0 else ttntt[0].amount,
                0 if len(bh) == 0 else bh[0].amount,
                0 if len(gtgc) == 0 else gtgc[0].amount,
                0 if len(lbn) == 0 else lbn[0].amount,
                0 if len(tnc) == 0 else tnc[0].amount,
                0 if len(ttncn) == 0 else ttncn[0].amount,
                0 if len(ttncnbn) == 0 else ttncnbn[0].amount,
                0 if len(net) == 0 else net[0].amount,
            ]

            for i, value in enumerate(col_values):
                if i in range(3, 28):
                    sheet.write(row, col + i, value, currency_format)
                else:
                    sheet.write(row, col + i, value, border)
