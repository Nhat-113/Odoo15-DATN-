from odoo.http import request, Response
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import pytz


def extract_hour_minute(time_string):
    try:
        hour, minute = time_string.split(":")
        return int(hour), int(minute)
    except ValueError:
        raise ValueError("Invalid time format. Expected 'HH:MM'.")

def create_attendance_device_details(datas, pseudo):
    if "location_id" in datas:
        datas["pseudo_attendance_id_app"] = pseudo.id
        pseudo.update({
        "attendance_device_details_app": [(0,0, datas)]
    })
    else:
        datas["pseudo_attendance_id"] = pseudo.id
        pseudo.update({
            "attendance_device_details": [(0,0, datas)]
        })


def validate_end_time(start, end):
    if start > end:
        raise ValidationError("Check out can't be less than check in")

    
def attendance_multi_record_mode(datas, attendance, pseudo_attendance, is_multiple_mode):
    message = ""
    data_details = {
        "device_id": datas['device_id'],
        "position": datas['position']
    }
    if datas['device_type'] == 'box_in':
        data_news = {
            "employee_id": datas['employee_id'].id,
            "check_in": datas['timeutc'],
            "is_multiple": is_multiple_mode
        }
        request.env['hr.attendance'].create(data_news)
        pseudo = request.env['hr.attendance.pesudo'].create(data_news)
        create_attendance_device_details(data_details, pseudo)
        message += "Check in"
    else:
        data_updates = {
            "employee_id": datas['employee_id'].id,
            "check_out": datas['timeutc'],
            "check_in": False,
            "is_multiple": is_multiple_mode
        }
        
        if attendance and not attendance.check_out:
            validate_end_time(attendance.check_in, datas['timeutc'])
            attendance.write({"check_out": datas['timeutc']})
        else:
            request.env['hr.attendance'].create(data_updates)

        if pseudo_attendance and not pseudo_attendance.check_out:
            pseudo_attendance.write({"check_out": datas['timeutc']})
            create_attendance_device_details(data_details, pseudo_attendance)
        else:
            pseudo = request.env['hr.attendance.pesudo'].create(data_updates)
            create_attendance_device_details(data_details, pseudo)
        
        message += "Check out"
    return message
    
def attendance_single_record_mode(datas, attendance, pseudo_attendance, is_multiple_mode):
    message = ""
    data_details = {
        "device_id": datas['device_id'],
        "position": datas['position']
    }
    if datas['device_type'] == 'box_in':
        data_news = {
            "employee_id": datas['employee_id'].id,
            "check_in": datas['timeutc'],
            "is_multiple": is_multiple_mode
        }
        if not attendance:
            request.env['hr.attendance'].create(data_news)
        pseudo = request.env['hr.attendance.pesudo'].create(data_news)
        create_attendance_device_details(data_details, pseudo)
        message += "Check in"
    else:
        data_updates = {
            "employee_id": datas['employee_id'].id,
            "check_out": datas['timeutc'],
            "is_multiple": is_multiple_mode
        }
        
        if attendance:
            validate_end_time(attendance.check_in, datas['timeutc'])
            attendance.write({"check_out": datas['timeutc']})
        
        if pseudo_attendance and not pseudo_attendance.check_out:
            validate_end_time(pseudo_attendance.check_in, datas['timeutc'])
            pseudo_attendance.write({"check_out": datas['timeutc']})
            create_attendance_device_details(data_details, pseudo_attendance)
        else:
            pseudo = request.env['hr.attendance.pesudo'].create(data_updates)
            create_attendance_device_details(data_details, pseudo)

        message += "Check out"
    return message

def handle_facelog_process_box_io(datas, attendance, pseudo_attendance, is_multiple_mode):
    message = ""
    if 'location_id' in datas:
        data_details = {
            "location_id": datas['location_id'],
        }
    else:
        data_details = {
            "device_id": datas['device_id'],
            "position": datas['position']
        }
    if attendance and attendance.check_in:
        if not attendance.check_out:
            data_updates = {
                "check_out": datas['timeutc']
            }
            validate_end_time(attendance.check_in, datas['timeutc'])
            attendance.write(data_updates)
            if pseudo_attendance:
                pseudo_attendance.write(data_updates)
                create_attendance_device_details(data_details, pseudo_attendance)
            message += "Check out"
        else:
            create_attendance_device_details(data_details, create_attendance(datas, is_multiple_mode))
            message += "Check in"
    else:
        create_attendance_device_details(data_details, create_attendance(datas, is_multiple_mode))
        message += "Check in"
    return message

def create_attendance(datas, is_multiple_mode):
    data_news = {
        "employee_id": datas['employee_id'].id,
        "check_in": datas['timeutc'],
        "is_multiple": is_multiple_mode
    }
    request.env['hr.attendance'].create(data_news)
    pseudo = request.env['hr.attendance.pesudo'].create(data_news)
    return pseudo
    
def handle_attendance_view_mode(datas):
    """
        Handle the logic of the api check in/out to resolve view mode single or multiple.
        datas = {
            "employee_id": employee,
            "device_type": device_type,
            "device_id": device_id,
            "timezone": timezone,
            "timestamp": timestamp,
            "timeutc": formatted_time
        }

        Handle the logic of the api check in/out for mobile.
        datas = {
            "employee_id": employee,
            "device_type": device_type,
            "location_id": location_id,
            "timezone": timezone,
            "timestamp": timestamp,
            "timeutc": formatted_time
        }
    """
    datetz = datetime.strptime(datas['timestamp'], "%Y-%m-%d %H:%M:%S")
    if datas['timezone'] != request.env.user.tz:
        # Switch back to the original timezone
        datetz = datetz.replace(tzinfo=pytz.timezone(datas['timezone']))
        # Convert to the timezone of the current user
        datetz = datetz.astimezone(pytz.timezone(request.env.user.tz))
    companies = datas['employee_id'].company_id
    if companies.attendance_view_type == True and companies.enable_split_shift == True:
        hour_start, hour_end = extract_hour_minute(datas['employee_id'].company_id.hour_work_start)
        if datetz.hour > hour_start and datetz.minute > hour_end:
            start_date = datetz.date()
        else:
            start_date = (datetz - timedelta(days=1)).date()
        
        attendance = request.env['hr.attendance'].search([
            ('employee_id', '=', datas['employee_id'].id),
            ('location_date_multi', '=', start_date),
            ('check_in', '!=', None)
        ], order="check_in desc, check_out desc", limit=1)

        pseudo_attendance = request.env['hr.attendance.pesudo'].search([('employee_id', '=', datas['employee_id'].id), 
                                                                        ('location_date_multi', '=', start_date)],
                                                                        order="check_in desc, check_out desc", limit=1)
    else:
        attendance = request.env['hr.attendance'].search([('employee_id', '=', datas['employee_id'].id),
                                                      ('location_date', '=', datetz.date()),
                                                      ('check_in', '!=', None)],
                                                     order="check_in desc, check_out desc", limit=1)
        pseudo_attendance = request.env['hr.attendance.pesudo'].search([('employee_id', '=', datas['employee_id'].id), 
                                                                        ('location_date', '=', datetz.date())],
                                                                    order="check_in desc, check_out desc", limit=1)
                                    
    is_multiple_mode = datas['employee_id'].company_id.attendance_view_type
    if datas['device_type'] == 'box_io':
        return handle_facelog_process_box_io(datas, attendance, pseudo_attendance, is_multiple_mode)
    else:
        #HR_attendance multiple records view mode
        if is_multiple_mode:
            return attendance_multi_record_mode(datas, attendance, pseudo_attendance, is_multiple_mode)
                
        else:
            # HR_attendance single record view mode
            return attendance_single_record_mode(datas, attendance, pseudo_attendance, is_multiple_mode)