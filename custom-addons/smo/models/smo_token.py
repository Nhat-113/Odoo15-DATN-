from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
from helper.smo_helper import make_request

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
  def get_tokens_of_id(self, smo_uid):
    if not smo_uid:
      smo_uid = self.env['smo.user'].login()

    return self.search([('smo_user_id', '=', smo_uid)], limit=1)

  @api.model
  def set_tokens_for_id(self, smo_uid, tokens):
    values = {
      'access_token': tokens['token'],
      'refresh_token': tokens['refreshToken']
    }

    user_tokens_record = self.search([('smo_user_id', '=', smo_uid)], limit=1)
    if user_tokens_record:
      user_tokens_record.write(values)
    else:
      values['smo_user_id'] = smo_uid
      self.create(values)
    self.env.cr.commit()

  @api.model
  def get_new_tokens(self, smo_uid):
    user_record = self.env['smo.user'].search([('id', '=', smo_uid)], limit=1)
    if not user_record:
      raise UserError('User record not found')
    
    tokens_response = self.env['smo.user'].login()
    if not tokens_response:
      raise UserError('Failed to obtain new tokens')

    values = {
      'access_token': tokens_response['token'],
      'refresh_token': tokens_response['refreshToken']
    }

    token_record = self.search([('smo_user_id', '=', smo_uid)], limit=1)
    if token_record:
      token_record.write(values)
    else:
      values['smo_user_id'] = smo_uid
      self.create(values)
    self.env.cr.commit()
  
  @api.model
  def refresh_access_token(self, smo_uid):
    user_token_record = self.search([('smo_user_id', '=', smo_uid)])
    if not user_token_record:
      raise UserError('Token record not found')
    
    payload = {
      "refreshToken": user_token_record.refresh_token
    }
    try: 
      response = make_request('/api/auth/token', method='POST', payload=payload)
      response.raise_for_status()
      
      res_data = response.json()
      user_token_record.write({
          'access_token': res_data['token'],
          'refresh_token': res_data['refreshToken'],
      })
      self.env.cr.commit()
    except requests.HTTPError as http_err:
      if response.status_code == 401:
        self.get_new_tokens(smo_uid)
      else:
        raise UserError(f'Failed to refresh access token: {response.text}')
    except Exception as err:
        raise UserError(f'An error occurred: {str(err)}')
      