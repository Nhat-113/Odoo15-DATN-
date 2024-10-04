from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
from helper.smo_helper import make_request
import json
import logging

_logger = logging.getLogger('smo.logger')

class SmoToken(models.Model):
    _name = "smo.token"
    _description = "SmartOffice Tokens"

    smo_user_id = fields.Many2one('smo.user', string="SmartOffice User ID", required=True)
    access_token = fields.Char(string="Access Token", required=True)
    refresh_token = fields.Char(string="Refresh Token", required=True)

    _sql_constraints = [
        ('unique_rf_token', 'unique (refresh_token)', 'Refresh Token must be unique.')
    ]

    @api.model
    def get_tokens_of_id(self, smo_uid=None):
        if not smo_uid:
            smo_user_record = self.env['smo.user'].search([], limit=1)
            smo_uid = smo_user_record.id or self.env['smo.user'].login()

        return self.search([('smo_user_id', '=', smo_uid)], limit=1)

    @api.model
    def set_tokens_for_id(self, smo_uid, tokens):
        values = {
            'access_token': tokens['token'],
            'refresh_token': tokens['refreshToken']
        }

        user_tokens_record = self.search([('smo_user_id', '=', smo_uid)], limit=1)
        if user_tokens_record:
            _logger.info('Update DB: Update tokens')
            user_tokens_record.write(values)
        else:
            values['smo_user_id'] = smo_uid
            _logger.info('Update DB: Create new token record to store new tokens')
            self.create(values)
        self.env.cr.commit()

    @api.model
    def get_new_tokens(self):
        smo_uid = self.env['smo.user'].login()
        if not smo_uid:
            raise UserError('Failed to obtain new tokens')

        token_record = self.search([('smo_user_id', '=', smo_uid)], limit=1)
        if token_record:
            raise UserError('Failed to get tokens record')
        
        return token_record
    
    @api.model
    def refresh_access_token(self, smo_uid=None):        
        if not smo_uid:
            smo_user_record = self.env['smo.user'].search([], limit=1)
            smo_uid = smo_user_record.id if smo_user_record else self.env['smo.user'].login()
            
        user_token_record = self.search([('smo_user_id', '=', smo_uid)])
        if not user_token_record:
            raise UserError('Token record not found')
        
        payload = {'refreshToken': user_token_record.refresh_token}
        
        try:
            _logger.info(f'Call API to refresh tokens')
            response = make_request(self, '/api/auth/token', method='POST', payload=payload)
            response.raise_for_status()
        except requests.HTTPError as http_err:
            _logger.error(f'API Server Response: {response.status_code} - Call API to refresh tokens failed: {json.loads(response.text)["message"]}')
            if response.status_code == 401:
                return self.get_new_tokens()
            else:
                raise UserError(f'Failed to refresh access token: {response.text}')
        except Exception as err:
            _logger.error(f'Odoo Server Error: Call API to refresh tokens failed: {err}')
            raise UserError(f'Something went wrong! Failed to refresh access token')

        try:
            _logger.info(f'API Server Response: {response.status_code} - Call API to refresh tokens successfully')
            _logger.info(f'Parse new tokens data from refreshing tokens')
            res_data = response.json()
        except Exception as err:
            _logger.error(f'Odoo Server Error: Failed to parse new tokens data from refreshing tokens: {err}')
            raise UserError('Failed to parse response data of tokens')

        _logger.info('Update DB: Update new tokens')
        user_token_record.write({
            'access_token': res_data['token'],
            'refresh_token': res_data['refreshToken'],
        })
        self.env.cr.commit()
        return user_token_record
