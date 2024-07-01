from odoo import models, fields, api
from odoo.http import request
from helper.smo_helper import make_request
from odoo.exceptions import ValidationError
import json

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
    ir_config = self.env['ir.config_parameter']
    username = ir_config.get_param('smo.shared_account_username')
    pwd = ir_config.get_param('smo.shared_account_password')
    payload = {
      "username": username,
      "password": pwd
    }
    
    try:
      response = make_request('/api/auth/login', method='POST', payload=payload)
      response.raise_for_status()
    except:
      raise ValidationError(f'Failed to authenticate: {json.loads(response.text)["message"]}')
    
    uid = -1
    existed_user_record = self.search([], limit=1)
    if not existed_user_record:
      new_record = self.create({
        'user_name': username,
        'passwords': pwd
      })
      uid = new_record.id
    else:
      existed_user_record.write({'passwords': pwd})
      uid = existed_user_record.id

    self.env.cr.commit()
    
    tokens = response.json()
    self.env['smo.token'].set_tokens_for_id(uid, tokens)
    
    return uid
      

  