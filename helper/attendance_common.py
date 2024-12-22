from odoo.http import request, Response
from datetime import datetime, timedelta, time
from odoo.exceptions import ValidationError
import pytz


def extract_hour_minute(time_string):
    try:
        hour, minute = time_string.split(":")
        return int(hour), int(minute)
    except ValueError:
        raise ValueError("Invalid time format. Expected 'HH:MM'.")

# def create_attendance_device_details(datas, pseudo):
#     # Kiểm tra xem có "location_id" trong dữ liệu không, sau đó gắn pseudo_attendance_id tương ứng
#     if "location_id" in datas:
#         datas["pseudo_attendance_id_app"] = pseudo.id
#         pseudo.sudo().update({
#             "attendance_device_details_app": [(0, 0, datas)]
#         })
#     else:
#         # Không sử dụng trường employee_id nếu không cần thiết
#         datas["pseudo_attendance_id"] = pseudo.id
#         pseudo.sudo().update({
#             "attendance_device_details": [(0, 0, datas)]
#         })


def validate_end_time(start, end):
    if start > end:
        raise ValidationError("Check out can't be less than check in")


def attendance_multi_record_mode(datas, attendance, pseudo_attendance, is_multiple_mode):
    message = ""
    
    if datas['type'] == 'check-in':
        # Handle check-in for multiple records
        data_news = {
            "employee_id": datas['employee_id'].id,
            "check_in": datas['timeutc'],
            "is_multiple": is_multiple_mode,
            "from_api": True
        }
        # Create a new attendance record
        request.env['hr.attendance'].sudo().create(data_news)
        pseudo = request.env['hr.attendance.pesudo'].sudo().create(data_news)
        # create_attendance_device_details(datas, pseudo)
        message += "Check in"
    else:
        # Handle check-out for multiple records
        data_updates = {
            "employee_id": datas['employee_id'].id,
            "check_out": datas['timeutc'],
            "check_in": False,
            "is_multiple": is_multiple_mode,
            "from_api": True
        }
        
        if attendance and not attendance.check_out:
            # Validate and update the attendance check-out time
            validate_end_time(attendance.check_in, datas['timeutc'])
            attendance.write({"check_out": datas['timeutc'], "from_api": True})
        else:
            # Create a new attendance record if no existing check-out
            request.env['hr.attendance'].sudo().create(data_updates)

        if pseudo_attendance and not pseudo_attendance.check_out:
            # If there is pseudo-attendance, update check-out time
            pseudo_attendance.sudo().write({"check_out": datas['timeutc']})
            # create_attendance_device_details(datas, pseudo_attendance)
        else:
            # Create a new pseudo-attendance record if no check-out
            pseudo = request.env['hr.attendance.pesudo'].sudo().create(data_updates)
            # create_attendance_device_details(datas, pseudo)
        
        message += "Check out"
    
    return message


def attendance_single_record_mode(datas, attendance, pseudo_attendance, is_multiple_mode):
    message = ""
    
    if datas['type'] == 'check-in':
        # Handle check-in for single record mode
        data_news = {
            "employee_id": datas['employee_id'].id,
            "check_in": datas['timeutc'],
            "is_multiple": is_multiple_mode,
            "from_api": True
        }
        # Only create a new attendance if none exists
        if not attendance:
            request.env['hr.attendance'].sudo().create(data_news)
        data_news.pop("from_api", None)
        pseudo = request.env['hr.attendance.pesudo'].sudo().create(data_news)
        # create_attendance_device_details(datas, pseudo)
        message += "Check in"
    else:
        # Handle check-out for single record mode
        data_updates = {
            "employee_id": datas['employee_id'].id,
            "check_out": datas['timeutc'],
            "is_multiple": is_multiple_mode,
        }
        
        if attendance:
            # Validate and update the attendance check-out time
            validate_end_time(attendance.check_in, datas['timeutc'])
            attendance.write({"check_out": datas['timeutc'], "from_api": True})
        
        if pseudo_attendance and not pseudo_attendance.check_out:
            # If there is pseudo-attendance, update check-out time
            validate_end_time(pseudo_attendance.check_in, datas['timeutc'])
            pseudo_attendance.sudo().write({"check_out": datas['timeutc']})
            # create_attendance_device_details(datas, pseudo_attendance)
        else:
            # Create a new pseudo-attendance record if no check-out
            pseudo = request.env['hr.attendance.pesudo'].sudo().create(data_updates)
            # create_attendance_device_details(datas, pseudo)

        message += "Check out"
    
    return message


# def handle_facelog_process_box_io(datas, attendance, pseudo_attendance, is_multiple_mode):
#     message = ""
#     if 'location_id' in datas:
#         data_details = {
#             "location_id": datas['location_id'],
#         }
#     else:
#         data_details = {
#             "device_id": datas['device_id'],
#             "position": datas['position']
#         }
#     if attendance and attendance.check_in:
#         if not attendance.check_out:
#             validate_end_time(attendance.check_in, datas['timeutc'])
#             attendance.write({"check_out": datas['timeutc'], "from_api": True})
#             if pseudo_attendance:
#                 pseudo_attendance.sudo().write({"check_out": datas['timeutc']})
#                 create_attendance_device_details(data_details, pseudo_attendance)
#             message += "Check out"
#         else:
#             if is_multiple_mode:
#                 create_attendance_device_details(data_details, create_attendance(datas, is_multiple_mode))
#                 message += "Check in"
#             else:
#                 validate_end_time(attendance.check_in, datas['timeutc'])
#                 attendance.write({"check_out": datas['timeutc'], "from_api": True})
                
#                 if pseudo_attendance and not pseudo_attendance.check_out:
#                     validate_end_time(pseudo_attendance.check_in, datas['timeutc'])
#                     pseudo_attendance.sudo().write({"check_out": datas['timeutc']})
#                     create_attendance_device_details(data_details, pseudo_attendance)
#                 else:
#                     data_updates = {
#                         "employee_id": datas['employee_id'].id,
#                         "check_in": datas['timeutc'],
#                         "is_multiple": is_multiple_mode
#                     }
#                     pseudo = request.env['hr.attendance.pesudo'].sudo().create(data_updates)
#                     create_attendance_device_details(data_details, pseudo)
#                 message += "Check out"
#     else:
#         create_attendance_device_details(data_details, create_attendance(datas, is_multiple_mode))
#         message += "Check in"
#     return message

def create_attendance(datas, is_multiple_mode):
    data_news = {
        "employee_id": datas['employee_id'].id,
        "check_in": datas['timeutc'],
        "is_multiple": is_multiple_mode,
        "from_api": True
    }
    request.env['hr.attendance'].sudo().create(data_news)
    pseudo = request.env['hr.attendance.pesudo'].sudo().create(data_news)
    return pseudo
    
def handle_attendance_view_mode(datas):
    """
    Handle the logic of the API check in/out to resolve view mode single or multiple.
    """
    try:
        # Convert timestamp to datetime object
        datetz = datetime.strptime(datas['timestamp'], "%Y-%m-%d %H:%M:%S")
        original_tz = pytz.timezone(datas['timezone']).localize(datetz).tzinfo
        datetz = datetz.replace(tzinfo=original_tz)

        # Convert to user's timezone if it's different
        if datas['timezone'] != request.env.user.tz:
            datetz = datetz.astimezone(pytz.timezone(request.env.user.tz))

        # Get company data
        companies = datas['employee_id'].company_id

        # Handling for split shift if enabled
        if companies.attendance_view_type and companies.enable_split_shift:
            hour_start, minute_start = extract_hour_minute(companies.hour_work_start)
            specific_time_start = time(hour_start, minute_start, 0)

            # Determine the date for attendance based on time
            if datetz.time() > specific_time_start:
                start_date = datetz.date()
            else:
                start_date = (datetz - timedelta(days=1)).date()

            # Search for attendance and pseudo-attendance for split shift mode
            attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', datas['employee_id'].id),
                ('location_date_multi', '=', start_date),
                ('check_in', '!=', None)
            ], order="check_in desc, check_out desc", limit=1)

            pseudo_attendance = request.env['hr.attendance.pesudo'].sudo().search([
                ('employee_id', '=', datas['employee_id'].id), 
                ('location_date_multi', '=', start_date)
            ], order="check_in desc, check_out desc", limit=1)
        
        else:
            # Search for attendance and pseudo-attendance for normal mode
            attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', datas['employee_id'].id),
                ('location_date', '=', datetz.date()),
                ('check_in', '!=', None)
            ], order="check_in desc, check_out desc", limit=1)

            pseudo_attendance = request.env['hr.attendance.pesudo'].sudo().search([
                ('employee_id', '=', datas['employee_id'].id), 
                ('location_date', '=', datetz.date())
            ]) 

            if pseudo_attendance:
                # If there are multiple pseudo attendances, sort by check_in
                list_attendances = [
                    {
                        "id": item.id,
                        "check_in": item.check_in if item.check_in else item.check_out,
                        "check_out": item.check_out if item.check_out else None
                    }
                    for item in pseudo_attendance
                ]
                lastest_records = sorted(list_attendances, key=lambda x: x['check_in'], reverse=True)[0]
                pseudo_attendance = pseudo_attendance.filtered(lambda x: x.id == lastest_records['id'])

        # Determine if we need to return multiple or single attendance records
        is_multiple_mode = companies.attendance_view_type

        # HR_attendance multiple records view mode
        if is_multiple_mode:
            return attendance_multi_record_mode(datas, attendance, pseudo_attendance, is_multiple_mode)
        else:
            # HR_attendance single record view mode
            return attendance_single_record_mode(datas, attendance, pseudo_attendance, is_multiple_mode)

    except KeyError as e:
        return {"status": 400, "message": f"Missing required parameter: {str(e)}"}
    except Exception as e:
        return {"status": 400, "message": f"Unexpected error: {str(e)}"}