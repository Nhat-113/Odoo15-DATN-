from werkzeug.wrappers import Response
from odoo.tools import date_utils
from pytz import timezone
from datetime import datetime
from odoo.tools import config 
from odoo.http import request

import json
import logging


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

def convert_current_tz(tizone, datime):
    input_timezone = timezone(tizone)
    input_timestamp = datetime.strptime(
                    str(datime), "%Y-%m-%d %H:%M:%S"
                ).astimezone(input_timezone)
    return input_timestamp

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

def image_url_getter(model, id, field = 'image_1920'):
    try:
        is_exist_image = request.env[model].browse(id)[field]
        image_url = ""
        if (is_exist_image):
            image_url = f"{request.httprequest.host_url}web/image?model={model}&id={str(id)}&field={field}"
        return image_url
    except:
        return ""
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