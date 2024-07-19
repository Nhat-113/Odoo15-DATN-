from werkzeug.wrappers import Response
from odoo.tools import date_utils
from pytz import timezone
from datetime import datetime
from odoo.tools import config 
from odoo.http import request

import json
import logging
from itertools import chain


###############################
# common function handle box and hr attendance api
###############################
def check_field_missing_api(kw, listkey):
    key_missing = []
    for key in listkey:
        if key not in kw:
            key_missing.append(key)
    return key_missing

def message_error_missing(listkey):
    field_missing = ', '.join(listkey)
    if len(listkey) > 1:
        return "Missing parameters. The following fields are required: %s" %(field_missing)
    else:
        return "Missing parameter. The %s field is required." %(field_missing)

def alternative_json_response(self, result=None, error=None):
    if error is not None:
        response = error
    if result is not None:
        response = result
    status_code = response.get("status", 200)
    mime = "application/json"
    body = json.dumps(response, default=date_utils.json_default)
    return Response(
        body,
        status=error and error.pop("http_status", 200) or status_code,
        headers=[("Content-Type", mime), ("Content-Length", len(body))],
    )
def alternative_json_response_for_mobile(self, result=None, error=None):
    if error is not None:
        response = error
    if result is not None:
        response = result
    response_data = json.loads(response.data)
    mime = "application/json"
    body = json.dumps(response_data, default=date_utils.json_default)
    return Response(
        body,
        status=error and error.pop("http_status", 200) or result.status_code,
        headers=[("Content-Type", mime), ("Content-Length", str(len(body)))],
    )
    
def convert_current_tz(tizone, datime):
    try:
        input_timezone = timezone(tizone)
        input_timestamp = datetime.strptime(
                        str(datime), "%Y-%m-%d %H:%M:%S"
                    ).astimezone(input_timezone)
        return input_timestamp
    except ValueError:
        return None

def logger (): 
    _logfile = "odoo.log" if "logpath" not in config.options else config.options["logpath"]
    _logger = logging.getLogger(__name__)

    _handler = logging.FileHandler(_logfile)
    _formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    _handler.setFormatter(_formatter)
    _logger.addHandler(_handler)
    return _logger

def jsonResponse (msg, status):
  return Response(json.dumps(msg, default=date_utils.json_default), content_type="application/json", status=status)

def check_authorize(model, user_id):
    return request.env[model].browse(user_id).check_access_rights('read', raise_exception=False)

def handle_pagination(offset, limit, total_records):
    last_pages = -(-total_records // limit)  
    return {
        "current_page": offset,
        "last_page": last_pages if last_pages > 0 else 1,
        "per_page": limit,
        "total": total_records,
    }

def validate_pagination(offset, limit):
    try:
        page = int(offset)
        per_page = int(limit)
        return {
            "offset": page if page > 0 else 1,
            "limit": per_page if per_page > 0 else 10
        }
    except:
        return False

def image_url_getter(model, record_id, field='image_1920'):
    record = request.env[model].browse(record_id)
    check_field_img = hasattr(record, 'image_1920')
    image_url = ""

    if check_field_img:
        is_exist_image = record[field]
        if is_exist_image:
            Params = request.env['ir.config_parameter'].sudo()
            base_url = Params.get_param('web.base.url')
            image_url = f"{base_url}/web/image?model={model}&id={record_id}&field={field}"
    return image_url
        
def valid_timezone(timez, timest):
    try:
        input_timezone = timezone(timez)
        input_timestamp = input_timezone.localize(
            datetime.strptime(timest, "%Y-%m-%d %H:%M:%S")
            
        ).astimezone(timezone("UTC"))
        formatted_time = datetime.strptime(input_timestamp.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
        return formatted_time
    except:
        return {"status": 400, "message": 'Invalid timestamp or timezone value'}

def is_valid_month(month_str, format="%Y-%m"):
    try:
        return datetime.strptime(month_str, format)
    except ValueError:
        return False

def is_valid_integer(value):
    try:
        return int(value)
    except (ValueError, TypeError): 
        return None

def check_and_handle_missing_fields(kwargs, required_fields, message="Invalid", status=40001):
    missing_fields = check_field_missing_api(kwargs, required_fields)
    if missing_fields:
        return jsonResponse({
            "status": status,
            "message": message,
            "keyerror": message_error_missing(missing_fields)
        }, 400)
    return None

def valid_timezone_for_mobile(timez, timest):
    try:
        input_timezone = timezone(timez)
        input_timestamp = input_timezone.localize(
            datetime.strptime(timest, "%Y-%m-%d %H:%M:%S")
            
        ).astimezone(timezone("UTC"))
        formatted_time = datetime.strptime(input_timestamp.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
        return formatted_time
    except:
        return {"status": 40001, "message": 'Invalid timestamp or timezone value'}
