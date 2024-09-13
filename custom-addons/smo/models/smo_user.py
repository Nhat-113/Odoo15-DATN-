from odoo import models, fields, api
from odoo.http import request
import requests
from helper.smo_helper import make_request
from odoo.exceptions import ValidationError, UserError
import json
import logging

_logger = logging.getLogger('smo.logger')

class SmoUser(models.Model):
    _name = "smo.user"
    _description = "SmartOffice User"

    user_name = fields.Char(string="Username", required=True)
    passwords = fields.Char(string="Password", required=True)

    _sql_constraints = [
        ('unique_username', 'unique (user_name)', 'Username must be unique.')
    ]

    @api.model
    def login(self):
        ir_config = self.env['ir.config_parameter'].sudo()
        username = ir_config.get_param('smo.shared_account_username')
        pwd = ir_config.get_param('smo.shared_account_password')
        payload = {
            "username": username,
            "password": pwd
        }
        
        try:
            _logger.info(f'Call API to login to get new tokens with username: {username}')
            response = make_request(self, '/api/auth/login', method='POST', payload=payload)
            response.raise_for_status()
        except requests.HTTPError as http_err:
            _logger.error(f'API Server Response: {response.status_code} - Call API to login to get new tokens failed: {json.loads(response.text)["message"]}')
            raise ValidationError(f'Failed to authenticate: {json.loads(response.text)["message"]}')
        except Exception as err:
            _logger.error(f'Odoo Server Error: Call API to login to get new tokens failed: {err}')
            raise UserError(f'Something went wrong! Please check your API URL or API account and try again!')
        
        try:
            _logger.info(f'API Server Response: {response.status_code} - Call API to login to get new tokens successfully')
            _logger.info(f'Parse new tokens data from login')
            tokens = response.json()
        except Exception as err:
            _logger.error(f'Odoo Server Error: Failed to parse new tokens data from login: {err}')
            raise UserError('Failed to parse response data of user')

        uid = -1
        existed_user_record = self.search([], limit=1)
        if not existed_user_record:
            _logger.info(f'Update DB: Create new user record to store login info of username: {username}')
            new_record = self.create({
                'user_name': username,
                'passwords': pwd
            })
            uid = new_record.id
        else:
            _logger.info(f'Update DB: Update user record with username: {username}')
            existed_user_record.write({'passwords': pwd})
            uid = existed_user_record.id

        self.env.cr.commit()

        self.env['smo.token'].set_tokens_for_id(uid, tokens)
        
        return uid
