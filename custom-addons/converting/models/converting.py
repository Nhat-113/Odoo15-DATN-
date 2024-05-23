from odoo import models, fields, api
import base64
from io import BytesIO
from xlrd import open_workbook
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import xlsxwriter
import tempfile

datetime_pattern = "%d%m%Y%H%M%S"
space_datetime_pattern = "%d/%m/%Y %H:%M:%S"
date_pattern = "%d/%m/%Y"

cover_duration = 5 #Represent for 5 minutes difference

ct_bank_name = "VietinBank"
ck_bank_name = "VpBank"

max_file_size = 50 * 1024 * 1024

inv_bank_col_labels = [
    "Thời gian giao dịch",
    "So khớp mã giao dịch",
    "Thời gian giao dịch",
    "Mã giao dịch",
]

misa_col_labels = [
    "Ngày hạch toán (*)",
    "Ngày chứng từ (*)",
    "Số chứng từ (*)",
    "Mã đối tượng",
    "Tên đối tượng",
    "Nộp vào TK",
    "Mở tại ngân hàng",
    "Lý do thu",
    "Diễn giải lý do thu",
    "Loại tiền",
    "Tỷ giá",
    "Diễn giải (hạch toán)",
    "TK Nợ (*)",
    "TK Có (*)",
    "Số tiền",
    "Quy đổi",
    "Mã đối tượng (hạch toán)",
]

class InvoiceConverting(models.Model):
    _name = "accounting.converting"
    _description = "accounting.converting"
    _order = "create_date DESC"

    invoice_attachment = fields.Binary(string="Invoice", required=True)
    ct_transaction_attachment = fields.Binary(string=ct_bank_name)
    ck_transaction_attachment = fields.Binary(string=ck_bank_name)
    invoice_bank_attachment = fields.Binary(string="Invoice Bank", readonly=True)
    misa_attachment = fields.Binary(string="Misa", readonly=True)

    invoice_attachment_name = fields.Char(string="Invoice Attachment")
    ct_transaction_attachment_name = fields.Char(string=f"{ct_bank_name} Attachment")
    ck_transaction_attachment_name = fields.Char(string=f"{ck_bank_name} Attachment")
    invoice_bank_attachment_name = fields.Char(string="Invoice Bank Attachment")
    misa_attachment_name = fields.Char(string="Misa Attachment")

    is_creating = fields.Boolean(default=True)

    name = fields.Char(string="Title", required=True)

    @api.onchange("invoice_attachment")
    def _check_invoice_attachment(self):
        if self.invoice_attachment:
            self._validate_file(self.invoice_attachment)

    @api.onchange("ct_transaction_attachment")
    def _check_ct_transaction_attachment(self):
        if self.ct_transaction_attachment:
            self._validate_file(self.ct_transaction_attachment)

    @api.onchange("ck_transaction_attachment")
    def _check_ck_transaction_attachment(self):
        if self.ck_transaction_attachment:
            self._validate_file(self.ck_transaction_attachment)

    @api.constrains("ck_transaction_attachment", "ct_transaction_attachment")
    def _check_transaction_attachment(self):
        if not self.ck_transaction_attachment and not self.ct_transaction_attachment:
            raise ValidationError("There is no transaction to compare")

    def _validate_file(self, attachment):
        try:
            if len(attachment) > max_file_size:
                raise ValidationError("Attachment size exceeds the limit (50MB). Please upload a smaller file.")
            decoded_data = base64.b64decode(attachment)
            file_like_object = BytesIO(decoded_data)
            open_workbook(file_contents=file_like_object.read())
        except ValidationError as ve:
            raise ve
        except:
            raise ValidationError("File is not supported!")

    def combine_date_time(self, date_str, time_str):
        date = datetime.strptime(date_str, date_pattern)
        time = datetime.strptime(time_str, "%H:%M")
        combined_datetime = datetime(date.year, date.month, date.day, time.hour, time.minute)
        return combined_datetime

    def get_invoice(self, invoice_wb, start, end):
        try:
            start_invoice = False
            result = []
            for row in range(invoice_wb.nrows):
                invoice_data = {}
                if not start_invoice:
                    if invoice_wb.cell_value(row, 1) == start:
                        start_invoice = True
                else:
                    if invoice_wb.cell_value(row, 1) == end:
                        break
                    for col in range(invoice_wb.ncols):
                        invoice_data["invoice_date"] = invoice_wb.cell_value(row, 1)
                        invoice_data["accounting_number"] = invoice_wb.cell_value(row, 2)
                        invoice_data["money"] = invoice_wb.cell_value(row, 16)
                        invoice_data["time_in"] = invoice_wb.cell_value(row, 7)
                        invoice_data["time_out"] = invoice_wb.cell_value(row, 8)
                        invoice_data["row"] = row
                        invoice_data["col"] = col
                    result.append(invoice_data)
            if not start_invoice:
                raise ValidationError(f"Unsupported format for invoice file")
            return result
        except:
            raise ValidationError(f"Unsupported format for invoice file")

    def get_ct_transaction(self, transaction_wb):
        try:
            transactions = []
            start_row = False
            for row in range(transaction_wb.nrows):
                transaction_data = {}
                if not start_row:
                    if transaction_wb.cell_value(row, 1) == "Ngày giao dịch/ Transaction date":
                        start_row = True
                else:
                    for col in range(transaction_wb.ncols):
                        transaction_data["transaction_date"] = transaction_wb.cell_value(row, 1)
                        transaction_data["credit"] = transaction_wb.cell_value(row, 4)
                        transaction_data["transaction_number"] = transaction_wb.cell_value(row, 6)
                    transactions.append(transaction_data)
            if not start_row:
                raise ValidationError(f"Unsupported format for {ct_bank_name} file")
            return transactions
        except:
            raise ValidationError(f"Unsupported format for {ct_bank_name} file")

    def get_ck_transaction(self, transaction_wb):
        try:
            transactions = []
            start_row = False
            for row in range(transaction_wb.nrows):
                transaction_data = {}
                if not start_row:
                    if transaction_wb.cell_value(row, 0) == "Ngày giao dịch":
                        start_row = True
                else:
                    for col in range(transaction_wb.ncols):
                        transaction_data["transaction_date"] = transaction_wb.cell_value(row, 0)
                        transaction_data["money"] = transaction_wb.cell_value(row, 5)
                        transaction_data["transaction_number"] = transaction_wb.cell_value(row, 3)
                    transactions.append(transaction_data)
            if not start_row:
                raise ValidationError(f"Unsupported format for {ck_bank_name} file")
            return transactions
        except:
            raise ValidationError(f"Unsupported format for {ck_bank_name} file")

    def find_ct_transaction(self, ct_invoices, ct_transactions):
        try:
            result = []
            for ct_invoice in ct_invoices:
                invoice_date = self.combine_date_time(ct_invoice["invoice_date"], ct_invoice["time_out"])
                nearest_difference = timedelta.max
                match_transaction = {}

                for ct_transaction in ct_transactions:
                    transaction_date = datetime.strptime(ct_transaction["transaction_date"], "%d-%m-%Y %H:%M:%S")
                    difference = abs(transaction_date - invoice_date)

                    if ct_invoice["money"] == ct_transaction["credit"] \
                    and difference < nearest_difference:
                        nearest_difference = difference
                        match_transaction = ct_transaction
                    match_transaction["row"] = ct_invoice["row"]
                    match_transaction["accounting_number"] = ct_invoice["accounting_number"]
                    match_transaction["date"] = transaction_date.strftime(date_pattern)
                match_transaction["iv_datetime"] = (ct_invoice["invoice_date"] + " " + ct_invoice["time_out"])

                result.append(match_transaction)

            return result
        except:
            raise ValidationError(f"Unsupported format for {ct_bank_name} file")

    def find_ck_transaction(self, ck_invoices, ck_transactions):
        try:
            result = []
            checked_transaction = []

            for ck_invoice in ck_invoices:
                invoice_date = self.combine_date_time(ck_invoice["invoice_date"], ck_invoice["time_out"])
                nearest_difference = timedelta.max
                match_transaction = {}

                for ck_transaction in ck_transactions:
                    transaction_datetime = datetime.strptime(ck_transaction["transaction_date"], space_datetime_pattern)
                    difference = abs(transaction_datetime - invoice_date)

                    converted_money = 0
                    converted_money_str = "".join(filter(str.isdigit, ck_transaction["money"]))
                    
                    if converted_money_str.isdigit():
                        converted_money = int(converted_money_str)

                    if ck_invoice["money"] == converted_money \
                    and difference < nearest_difference \
                    and ck_transaction["transaction_number"] not in checked_transaction \
                    and (((transaction_datetime - invoice_date).total_seconds() / 60) <= cover_duration and ((transaction_datetime - invoice_date).total_seconds() / 60) >= -cover_duration):
                    
                        nearest_difference = difference
                        match_transaction = ck_transaction

                    match_transaction["row"] = ck_invoice["row"]
                    match_transaction["accounting_number"] = ck_invoice["accounting_number"]
                match_transaction["iv_datetime"] = ck_invoice["invoice_date"] + " " + ck_invoice["time_out"]

                if "transaction_number" in match_transaction:
                    checked_transaction.append(match_transaction["transaction_number"])

                result.append(match_transaction)

            return result
        except:
            raise ValidationError(f"Unsupported format for {ck_bank_name} file")


    def write_inv_bank(self, invoice_wb, checked_ct_invoices, checked_ck_invoices):
        with tempfile.NamedTemporaryFile(delete=True) as temp:
            invoice_bank = xlsxwriter.Workbook(temp.name)
            sheet = invoice_bank.add_worksheet(name="InvBank")

            for row in range(invoice_wb.nrows):
                for col in range(invoice_wb.row_len(row)):
                    sheet.write(row, col, invoice_wb.cell_value(row, col))

            for i, value in enumerate(inv_bank_col_labels):
                sheet.write(6, i + 19, value)

            max_lengths = [0] * 4

            if checked_ct_invoices:
                for i, invoice in enumerate(checked_ct_invoices):
                    row = invoice.get("row", 0)
                    row_data = [invoice.get("iv_datetime", "#N/A"), invoice.get("transaction_number", "#N/A"), "", ""]
                    self.get_column_max_width(max_lengths, row_data, inv_bank_col_labels)

                    for i, cell in enumerate(row_data):
                        sheet.write(row, i + 19, cell)

            if checked_ck_invoices:
                for i, invoice in enumerate(checked_ck_invoices):
                    iv_datetime = invoice.get("iv_datetime", "#N/A")
                    transaction_number = invoice.get("transaction_number", "#N/A")
                    transaction_date = invoice.get("transaction_date", "#N/A").replace("\n", " ")
                    row = invoice.get("row", 0)
                    row_data = [iv_datetime, transaction_number, transaction_date, transaction_number]
                    self.get_column_max_width(max_lengths, row_data, inv_bank_col_labels)

                    for i, cell in enumerate(row_data):
                        sheet.write(row, i + 19, cell)

            for i, value in enumerate(max_lengths):
                sheet.set_column(i + 19, i + 19, value + 2)

            invoice_bank.close()
            with open(temp.name, 'rb') as file:
                binary_data = file.read()
            encoded_data = base64.b64encode(binary_data)
            return encoded_data

    def write_misa_record(self, workbook, rows, sheet, checked_invoice, record_format, t_type = None):
        try:
            if t_type =='CK':
                index = workbook.cell_value(1, 0).find("Số tài khoản:")
                account_number = workbook.cell_value(1, 0)[index + len("Số tài khoản:") :].split("\n")[0].strip()
            else:
                account_number = workbook.cell_value(11, 2)
        except:
            raise ValidationError(f"Unsupported file format\nCannot get the account number of {ck_bank_name if t_type == 'CK' else ct_bank_name} file")

        max_lengths = [0] * 17

        for i, invoice in enumerate(checked_invoice):
            transaction_number = invoice.get("transaction_number", "#N/A")
            if transaction_number != "#N/A":
                row = rows["row"]
                row_data = self._handle_misa_data(invoice, t_type, account_number)
                self.get_column_max_width(max_lengths, row_data, misa_col_labels)
                for i, cell in enumerate(row_data):
                    sheet.write(row, i, cell, record_format)
                rows['row'] += 1
            else:
                self.get_column_max_width(max_lengths, [], misa_col_labels)
        for i, value in enumerate(max_lengths):
            sheet.set_column(i, i, value + 2)

    def _handle_misa_data(self, invoice, t_type, account_number):
        current_date = datetime.today().strftime(date_pattern)

        transaction_date = invoice.get("date", "#N/A") if t_type == 'CT' \
        else invoice.get("transaction_date", "#N/A").split("\n")[0]

        accounting_number = invoice.get("accounting_number", "#N/A")

        money = "{:,.0f}".format(invoice.get("credit", "#N/A")) if t_type == 'CT' \
        else invoice.get("money", "#N/A").replace("\nVND", "")

        row_data = [
            current_date,
            transaction_date,
            accounting_number,
            "KL",
            "Khách lẻ Chill",
            account_number,
            ct_bank_name if t_type == 'CT' else ck_bank_name,
            "Thu tiền khách hàng (không theo hóa đơn)",
            f"Thu tiền bán hàng theo số chứng từ {int(accounting_number)}",
            "VND",
            "1",
            "Doanh thu bán hàng",
            "1211",
            "131",
            money,
            money,
            "KL"
        ]

        return row_data

    def get_column_max_width(self, max_lengths, row_data, column_labels):
        if row_data:
            for i, (label, value) in enumerate(zip(column_labels, row_data)):
                max_lengths[i] = max(max_lengths[i], max(len(label), len(str(value))))
        else:
            for i, label in enumerate(column_labels):
                max_lengths[i] = max(max_lengths[i], len(label))

    def write_misa(self, ct_transaction_wb, ck_transaction_wb, checked_ct_invoices, checked_ck_invoices):
        with tempfile.NamedTemporaryFile(delete=True) as temp:
            misa = xlsxwriter.Workbook(temp.name)
            sheet = misa.add_worksheet(name="MISA - THU")
            
            header_format = misa.add_format({'bold': True, 'border': 1})
            record_format = misa.add_format({'border': 1})
            header_format.set_align('center')

            sheet.merge_range(6, 11, 6, 16, "Chi tiết hạch toán", header_format)

            for i, value in enumerate(misa_col_labels):
                sheet.write(7, i, value, header_format)

            rows = {"row": 8 }

            if ct_transaction_wb:
                self.write_misa_record(ct_transaction_wb, rows, sheet, checked_ct_invoices, record_format, t_type="CT")
            if ck_transaction_wb:
                self.write_misa_record(ck_transaction_wb, rows, sheet, checked_ck_invoices, record_format, t_type="CK")

            misa.close()
            with open(temp.name, 'rb') as file:
                binary_data = file.read()
            encoded_data = base64.b64encode(binary_data)
            return encoded_data

    def get_sheet(self, attachment):
        decoded_data = base64.b64decode(attachment)
        file_like_object = BytesIO(decoded_data)
        workbook = open_workbook(file_contents=file_like_object.read())
        sheet = workbook.sheet_by_index(0)
        return sheet

    def create_export_output(self):
        for record in self:
            invoice_wb = self.get_sheet(record.invoice_attachment)
            ct_invoices = self.get_invoice(invoice_wb, start="CT", end="")
            ck_invoices = self.get_invoice(invoice_wb, start="CK", end="CT")

            ct_transaction_wb = None
            ck_transaction_wb = None

            if record.ct_transaction_attachment:
                ct_transaction_wb = self.get_sheet(record.ct_transaction_attachment)
                ct_transactions = self.get_ct_transaction(ct_transaction_wb)
                checked_ct_invoices = self.find_ct_transaction(ct_invoices, ct_transactions)

            if record.ck_transaction_attachment:
                ck_transaction_wb = self.get_sheet(record.ck_transaction_attachment)
                ck_transactions = self.get_ck_transaction(ck_transaction_wb)
                checked_ck_invoices = self.find_ck_transaction(ck_invoices, ck_transactions)

            invoice_bank_attachment = self.write_inv_bank(invoice_wb, checked_ct_invoices if ct_transaction_wb else [], checked_ck_invoices if ck_transaction_wb else [])
            misa_attachment = self.write_misa(ct_transaction_wb, ck_transaction_wb, checked_ct_invoices if ct_transaction_wb else [], checked_ck_invoices if ck_transaction_wb else [])

            self.write(
                {
                    "invoice_bank_attachment": invoice_bank_attachment,
                    "invoice_bank_attachment_name": "INV_BANK_" + self.create_date.strftime(datetime_pattern),
                    "misa_attachment": misa_attachment,
                    "misa_attachment_name": "MISA_THU_" + self.create_date.strftime(datetime_pattern),
                }
            )

    @api.model
    def create(self, vals):
        vals["is_creating"] = False
        accounting_statistics = super(InvoiceConverting, self).create(vals)
        accounting_statistics.create_export_output()
        return accounting_statistics
