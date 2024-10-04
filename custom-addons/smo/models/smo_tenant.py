from odoo import models, fields, api
from helper.smo_helper import make_request
from odoo.exceptions import UserError
import requests
import json
import logging

_logger = logging.getLogger('smo.logger')

class SmoTenant(models.Model):
    _name = "smo.tenant"
    _description = "SmartOffice Tenants"

    smo_user_id = fields.Many2one('smo.user', string='SmartOffice User ID', required=True, ondelete='cascade')
    customer_id = fields.Char(string="Customer ID", required=True)
    smo_asset_ids = fields.One2many('smo.asset', 'smo_tenant_id', string='Assets Records')


    @api.model
    def fetch_customer_id(self, smo_uid):
        tokens_record = self.env['smo.token'].get_tokens_of_id(smo_uid)
        if not tokens_record:
            raise UserError('Token record not found')
        
        params = {'pageSize': 1, 'page': 0}

        try:
            _logger.info(f'Call API to fetch tenants')
            response = make_request(self, '/api/users', method='GET',
                            params=params,
                            access_token=tokens_record.access_token)
            response.raise_for_status()
        except requests.HTTPError as http_err:
            _logger.error(f'API Server Response: {response.status_code} - Call API to fetch tenants failed: {json.loads(response.text)["message"]}')
            if response.status_code == 401:
                self.env['smo.token'].refresh_access_token(smo_uid)
                return self.fetch_customer_id(smo_uid)
            else:
                raise UserError(f'Failed to fetch tenant: {response.text}')
        except Exception as err:
            _logger.error(f'Odoo Server Error: Call API to fetch tenants failed: {err}')
            raise UserError(f'Something went wrong! Please check your API URL and try again!')

        try:
            _logger.info(f'API Server Response: {response.status_code} - Call API to fetch tenants successfully')
            _logger.info(f'Parse response data of customerId')
            res_data = response.json()
        except Exception as err:
            _logger.error(f'Odoo Server Error: Failed to parse response data of customerId: {err}')
            raise UserError('Failed to parse response data of tenants')

        res_data = res_data['data'][0]
        res_customer_id = res_data['customerId']['id']

        existed_record = self.search([('smo_user_id', '=', smo_uid)])
        if existed_record:
            _logger.info('Update DB: Update customerId')
            existed_record.write({'customer_id': res_customer_id})
        else:
            _logger.info('Update DB: Create new tenant record to store customerId')
            self.create({
                'smo_user_id': smo_uid,
                'customer_id': res_customer_id
            })
        self.env.cr.commit()

        return res_customer_id

