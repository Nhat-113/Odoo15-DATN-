import requests
import json
from odoo.exceptions import UserError

def make_request(self, endpoint, method='GET', access_token=None, params=None, payload=None):
    api_base_url = self.env['ir.config_parameter'].sudo().get_param('smo.base_api_url')
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

def generate_time_selection():
    time_selection = []
    start_hour = 0
    end_hour = 23
    end_minute = 30
    interval_minutes = 15

    for hour in range(start_hour, end_hour + 1):
        for minute in range(0, 60, interval_minutes):
            if hour == end_hour and minute > end_minute:
                break
            formatted_hour = str(hour).zfill(2)
            formatted_minute = str(minute).zfill(2)
            if hour >= 12:
                time_label = f"{formatted_hour}:{formatted_minute}"
            else:
                time_label = f"{formatted_hour}:{formatted_minute}"
            time_selection.append(
                (f"{formatted_hour}:{formatted_minute}", time_label)
            )

    return time_selection
