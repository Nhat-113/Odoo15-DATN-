from odoo.http import request
import requests
import json
from odoo.exceptions import UserError

def make_request(endpoint, method='GET', access_token=None, params=None, payload=None):
  api_base_url = request.env['ir.config_parameter'].get_param('smo.base_api_url')
  if not api_base_url:
    raise UserError('Thingsboard API URL not found. Please setup API URL!')
    
  api_url = api_base_url + endpoint
  headers = {
    'Content-Type': 'application/json',
  }
  if access_token:
    headers.update({'X-Authorization': f'Bearer {access_token}'})

  if method == 'GET':
    return requests.get(api_url, headers=headers, data=json.dumps(payload), params=params)
  elif method == 'POST':
    return requests.post(api_url, headers=headers, data=json.dumps(payload), params=params)
  else:
    return {'Error': 'HTTP method is not supported'}

