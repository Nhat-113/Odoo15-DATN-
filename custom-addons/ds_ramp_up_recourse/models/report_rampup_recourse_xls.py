from odoo import models, _


class RampUpRecourse(models.Model):
    _inherit = ['hr.employee']


class RampUpXlsx(models.AbstractModel):
    _name = 'report.ds_export_excel.rampup_xlsx'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, employee):

        sheet = workbook.add_worksheet('Ramp Up Recourse Report'[:31])
        bold_center = workbook.add_format(
            {'bold': True, 'align': 'center', 'border': 1})
        currency_format = workbook.add_format(
            {'num_format': '#,##0', 'border': 1})
        border = workbook.add_format({'border': 1})
        row, col = 0, 0
        col_names = [
            "Name",
            "Position",
            "Department",
        ]

        projects = self.env['project.project'].search(
            ['&', ('company_id', '=', self.env.company.id), ('active', '=', True)])
        for project in projects:
            col_names.append(project.name + ' (%)')

        # Set Column Ranges
        sheet.set_column(col, col + 28, 35)
        sheet.set_column(1, 1, 40)


        for i, name in enumerate(col_names):
            sheet.write(row, col + i, name, bold_center)

        for obj in employee:
            row += 1

            col_values = [
                obj.name,
                obj.job_title or '',
                obj.department_id.name or '',
            ]

            for project in projects:
                project_id = [
                    x for x in obj.planning_calendar_resources if x.project_id.id == project.id]
                col_values.append(
                    project_id[0].effort_rate) if project_id else col_values.append('')

            for i, value in enumerate(col_values):
                if i in range(3, 28):
                    sheet.write(row, col + i, value, currency_format)
                else:
                    sheet.write(row, col + i, value, border)
