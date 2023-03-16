from odoo import models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'
    
    # ------------------------------------------------------
    # FOLLOWERS API
    # ------------------------------------------------------
    
    # @Override
    # Disable the feature of automatically adding the manager department to followers when changing the department from the hr.contract model
    def _message_auto_subscribe(self, updated_values, followers_existing_policy='skip'):
        return True