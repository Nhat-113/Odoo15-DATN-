from odoo import models, fields, api

class ExportWizard(models.TransientModel):
    _inherit = 'export.wizard'
    
    def get_time_off_type_ids_for_companies(self, company_ids):
        time_off_type_ids = [0]
        companies = self.env['res.company'].browse(company_ids)
        
        for company in companies:
            if company.time_off_type_id:
                time_off_type_ids.append(company.time_off_type_id.id)
                
        return time_off_type_ids
