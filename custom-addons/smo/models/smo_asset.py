from odoo import models, fields, api
from helper.smo_helper import make_request
from odoo.exceptions import UserError
import requests
import json
import logging

_logger = logging.getLogger('smo.logger')

class SmoAsset(models.Model):
    _name = "smo.asset"
    _description = "SmartOffice Assets"
    _rec_name = "asset_name"

    smo_tenant_id = fields.Many2one('smo.tenant', string="SmartOffice Tenant ID", required=True, ondelete='cascade')
    customer_id = fields.Char(string='Customer ID')
    asset_id = fields.Char(string="Asset ID", required=True)
    asset_name = fields.Char(string="Asset Name", required=True)
    smo_device_ids = fields.One2many('smo.device', 'smo_asset_id', string='SmartOffice Device Records')
    
    @api.model
    def fetch_assets(self, smo_uid):
        customer_id = self.env['smo.tenant'].fetch_customer_id(smo_uid)
        if not customer_id:
            raise UserError('An error occurred while fetching tenants.')
        
        tokens_record = self.env['smo.token'].get_tokens_of_id(smo_uid)
        if not tokens_record:
            raise UserError('Token record not found.')

        params = {
            'fromId': customer_id,
            'fromType': 'CUSTOMER'
        }
        
        try:
            _logger.info(f'Call API to fetch assets')
            response = make_request(self, '/api/relations/info', method='GET',
                            params=params,
                            access_token=tokens_record.access_token)
            response.raise_for_status()
        except requests.HTTPError as http_err:
            _logger.error(f'API Server Response: {response.status_code} - Call API to fetch assets failed: {json.loads(response.text)["message"]}')
            if response.status_code == 401:
                self.env['smo.token'].refresh_access_token(smo_uid)
                self.fetch_assets(smo_uid)
            else:
                raise UserError(f'Failed to fetch assets: {response.text}')
        except Exception as err:
            _logger.error(f'Odoo Server Error: Call API to fetch assets failed: {err}')
            raise UserError(f'Something went wrong! Please check your API URL and try again!')

        try:
            _logger.info(f'API Server Response: {response.status_code} - Call API to fetch assets successfully')
            _logger.info(f'Parse response data of assets')
            data = response.json()
        except Exception as err:
            _logger.error(f'Odoo Server Error: Failed to parse response data of assets: {err}')
            raise UserError('Failed to parse response data of assets')

        existing_assets = {asset.asset_id: asset for asset in self.search([('smo_tenant_id', '=', customer_id)])}

        tenant_record = self.env['smo.tenant'].search([('customer_id', '=', customer_id)], limit=1)
        if not tenant_record:
            raise UserError('Tenant record not found')

        fetched_asset_ids = []
        for asset in data:
            customer_id = asset['from']['id']
            asset_id = asset['to']['id']
            asset_name = asset['toName']

            fetched_asset_ids.append(asset_id)

            if asset_id in existing_assets:
                _logger.info(f'Update DB: Update asset [{asset_name}]: [asset_name: {existing_assets[asset_id].asset_name} ➜ {asset_name}]')
                existing_assets[asset_id].write({'asset_name': asset_name})
            else:
                _logger.info(f'Update DB: Create new asset record to store asset data [{asset_name}]')
                self.create({
                    'smo_tenant_id': tenant_record.id,
                    'customer_id': tenant_record.customer_id,
                    'asset_id': asset_id,
                    'asset_name': asset_name
                })

        assets_to_delete = [asset for asset_id, asset in existing_assets.items() if asset_id not in fetched_asset_ids]
        for asset in assets_to_delete:
            _logger.info(f'Update DB: Delete asset record [{asset.asset_name}]')
            asset.unlink()

        self.env.cr.commit()
        return fetched_asset_ids

