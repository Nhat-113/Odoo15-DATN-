from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime
from pytz import timezone


MAX_FILE_SIZE = 50 * 1000 * 1000
ALLOWED_ATTACHMENT = ["txt","doc","docx","xlsx","csv","ppt","pptx","pdf","png","jpg","jpeg"]
TIME_STRING_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d/%m/%Y"

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

class MeetingSchedule(models.Model):
    _name = "meeting.schedule"
    _description = "Meeting schedule"
    _order = "start_date DESC"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", compute="_compute_meeting_name", required=True)
    meeting_subject = fields.Char(string="Meeting subject")
    description = fields.Text(string="Description")
    meeting_type = fields.Selection(
        string="Meeting type",
        default="normal",
        required=True,
        selection=[
            ("normal", "Normal Meeting"),
            ("daily", "Daily Meeting"),
            ("weekly", "Weekly Meeting"),
        ],
    )
    start_date = fields.Datetime(string="Start Date Time", tracking=True, required=True)
    end_date = fields.Datetime(string="End Date Time", tracking=True, required=True)
    s_date = fields.Date(string="Start Date", required=True)
    e_date = fields.Date(string="End Date", required=True)

    start_minutes = fields.Selection(
        generate_time_selection(),
        string="Start",
        compute = '_compute_default_start_minutes',
        store=False,
        required=True
    )
    end_minutes = fields.Selection(
        generate_time_selection(),
        string="End",
        compute = '_compute_default_end_minutes',
        store=False,
        required=True
    )
    duration = fields.Float(
        string="Duration(hour)",
        compute="_compute_duration",
        store=True,
    )
    room_id = fields.Many2one("meeting.room", string="Room", tracking=True, required=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company name",
        required=True,
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Created by",
        required=True,
        default=lambda self: self.env.user,
    )
    day = fields.Char("Day", compute="_compute_kanban_date_start", store=True,)
    month = fields.Char("Month and Year", compute="_compute_kanban_date_start", store=True,)
    time = fields.Char("Time", compute="_compute_kanban_date_start", store=True,)

    repeat_weekly = fields.Integer(string="Repeat Weekly", default=0)
    weekday = fields.Char(string="Day of week")
    parent_id = fields.Integer()

    monday = fields.Boolean(string="Monday", default=True, readonly=False)
    tuesday = fields.Boolean(string="Tuesday", default=True, readonly=False)
    wednesday = fields.Boolean(string="Wednesday", default=True, readonly=False)
    thursday = fields.Boolean(string="Thursday", default=True, readonly=False)
    friday = fields.Boolean(string="Friday", default=True, readonly=False)
    saturday = fields.Boolean(string="Saturday", default=False, readonly=False)
    sunday = fields.Boolean(string="Sunday", default=False, readonly=False)
    

    is_edit = fields.Boolean(default=False)
    check_access_team_id = fields.Boolean("Check Access", compute="_check_user_id")
    access_link = fields.Char(compute='_compute_access_link')
    attachment_ids = fields.One2many('ir.attachment','res_id', string="Attachments") 
    file_attachment_ids = fields.Many2many('ir.attachment', string="Attach File", inverse='_inverse_file_attachment_ids')
    
    partner_ids = fields.Many2many(comodel_name="hr.employee", string="Attendees", tracking=True)
    for_attachment = fields.Boolean(default=True, compute="_check_for_attachment")
    customize = fields.Boolean(string="Customize", default=False)

    edit_room = fields.Char()
    edit_time = fields.Char()
    edit_date_start = fields.Char()
    edit_date_end = fields.Char()
    reason_delete = fields.Char()
    count = fields.Integer(default = 0)
    edit_emp = fields.Many2many(comodel_name="hr.employee", string="Attendees", tracking=True,relation="meeting_schedule_edit_emp_rel" )
    end_daily = fields.Char()
    delete_type = fields.Char(default="")
    email_sent = fields.Boolean(string='Email Sent', default=False)

    def _compute_default_start_minutes(self):
        time_start_date =  self.start_date.astimezone(self.get_local_tz()) 
        start_hour = time_start_date.hour
        start_minute = time_start_date.minute
        self.start_minutes = f"{start_hour:02d}:{start_minute:02d}"

    def _compute_default_end_minutes(self):
        time_end_date =  self.end_date.astimezone(self.get_local_tz())
        end_hour = time_end_date.hour
        end_minute = time_end_date.minute
        self.end_minutes = f"{end_hour:02d}:{end_minute:02d}"

    def _inverse_file_attachment_ids(self):
        self.attachment_ids = self.file_attachment_ids
    
    def _compute_access_link(self):
        for record in self:
            record.access_link = record._notify_get_action_link('view')

    # Depends
    @api.depends("user_id")
    def _check_user_id(self):
        for rec in self:
            rec.check_access_team_id = bool(rec.check_is_hr() or rec.user_id.id == self.env.uid)

    def get_attendees(self):
        if self.id:
            query = """
                SELECT hr_employee_id
                FROM hr_employee_meeting_schedule_rel
                WHERE meeting_schedule_id = %s
            """
            self.env.cr.execute(query, [self.id])
            result = self.env.cr.fetchall()
            partner_ids = [row[0] for row in result]
            return partner_ids
        return []

    def check_is_attendee(self):
        partner_ids = self.get_attendees()
        employee_id = self.env.user.employee_id.id
        return employee_id in partner_ids

    @api.depends("partner_ids")
    def _check_for_attachment(self):
        res_user_id = self.env.user.id
        is_attendee = self.check_is_attendee()

        for rec in self:
            is_hr = rec.check_is_hr()
            rec.for_attachment = bool(
                is_hr or
                res_user_id == rec.create_uid.id or
                is_attendee
            )
            
    @api.depends("room_id", "user_id")
    def _compute_meeting_name(self):
        for record in self:
            if record.room_id and record.user_id:
                record.name = f"{record.room_id.name} - {record.user_id.name}"

    @api.depends("start_date")
    def _compute_kanban_date_start(self):
        for record in self:
            if record.start_date:
                date_obj = record.start_date.astimezone(self.get_local_tz())
                record.day = date_obj.strftime("%d")
                record.month = date_obj.strftime("%b %Y")
                record.time = date_obj.strftime("%H:%M")
                record.weekday = date_obj.strftime("%A")
                record.s_date = date_obj.date()
                if record.is_edit:
                    record.e_date = date_obj.date()

    @api.depends("start_date", "end_date")
    def _compute_duration(self):
        for record in self:
            if record.start_date and record.end_date:

                start_time = record.start_date.astimezone(self.get_local_tz()).time()
                end_time = record.end_date.astimezone(self.get_local_tz()).time()

                if self.start_date >= self.end_date:
                    self.duration = 0
                else:
                    start_seconds = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
                    end_seconds = end_time.hour * 3600 + end_time.minute * 60 + end_time.second
                        
                    duration_seconds = end_seconds - start_seconds
                    duration_hours = duration_seconds / 3600
                    self.duration = duration_hours

    # Constraints
    @api.constrains("file_attachment_ids")
    def _validate_attachment(self):
        if self.file_attachment_ids:
            for file in self.file_attachment_ids:
                file_type = file.name.rsplit(".", 1)[1].lower()
                if "." not in file.name \
                or file_type not in ALLOWED_ATTACHMENT:
                    raise ValidationError(
                        f"Invalid attachment file type. " 
                        f"File {file.name}'s file type is '.{file_type}' which is not allowed"
                    )
                
                if file.file_size > MAX_FILE_SIZE:
                    size_in_mb = file.file_size /1000 /1000
                    raise ValidationError(
                        f"The size of file: {file.name} is {round(size_in_mb,2)} MB "
                        f"which exceeds the maximum file size allowed of {MAX_FILE_SIZE / 1000 / 1000} MB"
                    )

    @api.constrains("duration")
    def _check_duration(self):
        for schedule in self:
            if schedule.duration < 0.25:
                raise ValidationError("A meeting must be at least 15 minutes")

    @api.constrains("repeat_weekly")
    def _check_max_value(self):
        for record in self:
            if record.repeat_weekly > 52:
                raise ValidationError("Cannot repeat for more than a year")

    @api.constrains("start_date", "duration", "room_id")
    def _check_room_availability(self):
        for record in self:
            if record.start_date and record.duration and record.room_id:
                start_datetime = record.start_date
                end_datetime = start_datetime + timedelta(hours=record.duration)

                conflicting_bookings = self.search(
                    [
                        ("room_id", "=", record.room_id.id),
                        ("id", "!=", record.id),
                        ("start_date", "<", end_datetime),
                        ("end_date", ">", start_datetime),
                    ]
                )
                if conflicting_bookings:
                    raise ValidationError("The room is already booked for this time period.")
        
    # Onchanges
    @api.onchange("start_date", "end_date")
    def _onchange_start_end_date(self):
        if self.start_date and self.end_date:
            local_tz = self.get_local_tz()
            self.access_link = self._notify_get_action_link('view')
            start_date = self.start_date.astimezone(local_tz) 
            end_date = self.end_date.astimezone(local_tz) 
            
            if self.start_date >= self.end_date:
                self.duration = 0
            else:
                start_seconds = start_date.hour * 3600 + start_date.minute * 60 + start_date.second
                end_seconds = end_date.hour * 3600 + end_date.minute * 60 + end_date.second
                    
                duration_seconds = end_seconds - start_seconds
                duration_hours = duration_seconds / 3600
                self.duration = duration_hours

            self.start_minutes = str(start_date.hour).zfill(2) + ":" + str(start_date.minute).zfill(2)
            self.end_minutes = str(end_date.hour).zfill(2) + ":" + str(end_date.minute).zfill(2)        
        
            if self.duration != 0 and end_date.date() != start_date.date() and self.meeting_type != "daily" :
                self.meeting_type = "daily"

    @api.onchange("start_date")
    def _onchange_start_date(self):
        if self.start_date:
            local_offset = self.get_local_tz(True)
            adjusted_start_date = self.start_date + timedelta(hours=local_offset)
            self.weekday = adjusted_start_date.strftime("%A")
            self.s_date = fields.Date.to_string(adjusted_start_date.date())

    @api.onchange("end_date")
    def _onchange_end_date(self):
        if self.end_date:
            local_offset = self.get_local_tz(True)
            adjusted_end_date = self.end_date + timedelta(hours=local_offset)
            self.e_date = fields.Date.to_string(adjusted_end_date.date())

    @api.onchange("s_date", "start_minutes")
    def onchange_s_date(self):
        if self.s_date and self.start_minutes:
            local_offset = self.get_local_tz(True)
            time_obj = datetime.strptime(self.start_minutes, "%H:%M").time()
            combined_datetime = datetime.combine(self.s_date, time_obj)
            self.start_date = combined_datetime - timedelta(hours=local_offset)

    @api.onchange("e_date", "end_minutes")
    def onchange_e_date(self):
        if self.e_date and self.end_minutes:
            local_offset = self.get_local_tz(True)
            time_obj = datetime.strptime(self.end_minutes, "%H:%M").time()
            combined_datetime = datetime.combine(self.e_date, time_obj)
            self.end_date = combined_datetime - timedelta(hours=local_offset)

    @api.onchange("s_date")
    def _onchange_s_date(self):
        if self.s_date and self.end_date and self.is_edit:
            self.e_date = self.s_date
            self.end_date = datetime.combine(self.s_date, self.end_date.time())

    @api.onchange("meeting_type")
    def onchange_meeting_type(self):
        if self.meeting_type != "daily" and self.s_date != self.e_date:
            self.end_date = self.end_date.replace(day=self.start_date.day
            ,month = self.start_date.month
            ,year=self.start_date.year)

    @api.onchange("start_date", "meeting_type")
    def onchange_start_time(self):
        if self.start_date and self.meeting_type:
            if self.meeting_type == "daily":
                self.monday = self.tuesday = self.wednesday = self.thursday = self.friday = True
                self.saturday = self.sunday = False
            elif self.meeting_type == "weekly":
                self.monday = self.tuesday = self.wednesday = self.thursday = self.friday = self.saturday = self.sunday = False
                local_start = self.start_date.astimezone(self.get_local_tz())
                day_of_week = local_start.weekday()
                days = {0: 'monday', 1: 'tuesday', 2: 'wednesday', 3: 'thursday', 4: 'friday', 5: 'saturday', 6: 'sunday'}
                setattr(self, days[day_of_week], True)

    # Business Logic Methods
    def create_daily(self):
        start_datetime = self.start_date
        end_datetime = self.end_date
        end_date = datetime.combine(start_datetime.date(), end_datetime.time())

        hours = self.get_local_tz(offset=True)

        local_start_date = (start_datetime + timedelta(hours=hours)).date()
        local_end_date = (end_datetime + timedelta(hours=hours)).date()

        new_end_date = ""
        
        if local_start_date == start_datetime.date():
            new_end_date = end_date
        elif local_start_date > start_datetime.date():
            if local_end_date > end_datetime.date():
                new_end_date = end_date
            elif local_end_date == end_datetime.date():
                new_end_date = end_date + timedelta(days=1)

        local_new_end_date = (new_end_date + timedelta(hours=hours)).date()

        self.write({"end_date": new_end_date, "e_date": local_new_end_date, "count": 1})

        weekday_attributes = [
            self.monday,
            self.tuesday,
            self.wednesday,
            self.thursday,
            self.friday,
            self.saturday,
            self.sunday,
        ]
        weekday_mapping = dict(zip(range(len(weekday_attributes)), weekday_attributes))

        booking_dates = [
            start_datetime + timedelta(days=day)
            for day in range(1, (end_datetime - start_datetime).days + 1)
        ]
        self.end_daily = "to " + str((self.end_date + timedelta(days=len(booking_dates))).strftime('%d/%m/%Y'))
        booking_to_create = []
        
        for booking in booking_dates:
            if weekday_mapping.get(booking.weekday(), False):
                date = booking.date()
                s_hour = (booking + timedelta(hours=hours)).hour
                e_hour = (booking + timedelta(hours=(hours + self.duration))).hour
                if s_hour < hours and e_hour >= hours:
                    date += timedelta(days=1)
                booking_to_create.append({
                    "name": self.name,
                    "meeting_subject": self.meeting_subject,
                    "description": self.description,
                    "meeting_type": self.meeting_type,
                    "start_date": booking,
                    "end_date": datetime.combine(date, end_datetime.time()),
                    "duration": self.duration,
                    "file_attachment_ids": self.file_attachment_ids,
                    "room_id": self.room_id.id,
                    "company_id": self.company_id.id,
                    "user_id": self.user_id.id,
                    "is_edit": True,
                    "partner_ids": self.partner_ids,
                    'parent_id': self.id,
                    's_date': date,
                    'e_date': date,
                })

        self.create(booking_to_create)

    def create_weekly(self):
        booking_to_create = []
        start_date = self.start_date

        for i in range(self.repeat_weekly + 1):
            new_bookings = []
            current_date = start_date + timedelta(weeks=i)
            if current_date != start_date:
                new_bookings.append(
                    {
                        "name": self.room_id.name,
                        "meeting_subject": self.meeting_subject,
                        "description": self.description,
                        "start_date": current_date,
                        "end_date": current_date + timedelta(hours=self.duration),
                        "meeting_type": self.meeting_type,
                        "room_id": self.room_id.id,
                        "company_id": self.company_id.id,
                        "duration": self.duration,
                        "file_attachment_ids": self.file_attachment_ids,
                        "user_id": self.user_id.id,
                        "repeat_weekly": self.repeat_weekly,
                        "is_edit": True,
                        "partner_ids": self.partner_ids,
                        'parent_id': self.id,
                        's_date': current_date.date(),
                        'e_date': current_date.date()
                    }
                )
            booking_to_create.extend(new_bookings)

        self.create(booking_to_create)

    @api.model
    def check_is_hr(self):
        return self.env.user.has_group("booking_room.group_booking_room_hr")

    @api.model
    def get_current_user(self):
        return {"employee_id": self.env.user.employee_id.id, "is_hr": self.check_is_hr()}

    @api.model
    def get_booking_detail(self, id):
        booking = self.search([('id', '=', id)])
        if booking:
            result = {
                "user_id": booking.user_id.id,
                "start_date": booking.start_date + timedelta(hours=self.get_local_tz(offset=True)),
                "end_date": booking.end_date + timedelta(hours=self.get_local_tz(offset=True)),
                "is_hr": self.check_is_hr(),
                "room_id": booking.room_id.id,
            }
        return result

    def _check_is_past_date(self, start_date):
        if start_date is None:
            return False
        if not isinstance(start_date, datetime):
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        return start_date < fields.Datetime.now()

    def _validate_start_date(self):
        user_tz = self.env.user.tz or "UTC"
        local_tz = timezone(user_tz)
        start_datetime = self.start_date.astimezone(local_tz)

        weekday_mapping = {
            0: ("Monday", self.monday),
            1: ("Tuesday", self.tuesday),
            2: ("Wednesday", self.wednesday),
            3: ("Thursday", self.thursday),
            4: ("Friday", self.friday),
            5: ("Saturday", self.saturday),
            6: ("Sunday", self.sunday),
        }
        weekday_name, allowed = weekday_mapping.get(start_datetime.weekday())
        if not allowed and self.meeting_type == "daily" and not self.parent_id:
            raise ValidationError(f"Start date cannot be scheduled on {weekday_name}.")

    def send_meeting_email(self, template):
        template_id = self.env.ref(template, raise_if_not_found=False)
        if template_id:
            for record in self:
                template_id.send_mail(record.id, force_send=True)

    def send_meeting_email_edit(self, vals, edit_type = 'single'):
        if len(self.partner_ids.ids) == 0 and 'partner_ids' not in vals:
            return
        template_id_edit = self.env.ref('booking_room.template_sendmail_edit_event', raise_if_not_found=False)
        template_id_add_attendens = self.env.ref('booking_room.template_sendmail_add_attendens', raise_if_not_found=False)
        template_id_delete_attendens = self.env.ref('booking_room.template_sendmail_delete_attendens', raise_if_not_found=False)

        current_rec = self.search([('id', "=", vals['id'])]) if edit_type != 'single' else None
        source_rec = current_rec if current_rec else self
        local_tz = self.get_local_tz()

        room_name = self.env['meeting.room'].search([('id', '=', vals['room_id'])]).name if 'room_id' in vals else source_rec.room_id.name
        start_date = vals.get('start_date')
        smallest_start_date = vals.get('smallest_start_date')
        largest_start_date = vals.get('largest_start_date')
        end_date = vals.get('end_date')
        partner_ids = vals.get('partner_ids')

        if start_date:
            local_start_date = datetime.strptime(str(start_date), TIME_STRING_FORMAT).astimezone(local_tz)
        else:
            local_start_date = source_rec.start_date.astimezone(local_tz)

        if end_date:
            local_end_date = datetime.strptime(str(end_date), TIME_STRING_FORMAT).astimezone(local_tz)
        else:
            local_end_date = source_rec.end_date.astimezone(local_tz)

        if smallest_start_date and largest_start_date:
            local_smallest_start_date = smallest_start_date.astimezone(local_tz)
            local_largest_start_date = largest_start_date.astimezone(local_tz)

        source_rec.edit_room = room_name
        source_rec.s_date = local_start_date.date()
        source_rec.e_date = local_end_date.date()
        source_rec.edit_time = local_start_date.strftime("%H:%M") +" to " + local_end_date.strftime("%H:%M")
        source_rec.delete_type = 'none'
        if not current_rec:
            source_rec.edit_date_start = local_start_date.strftime(DATE_FORMAT)
            source_rec.edit_date_end = local_end_date.strftime(DATE_FORMAT)
        else:
            source_rec.edit_date_start = local_smallest_start_date.strftime(DATE_FORMAT)
            source_rec.edit_date_end = local_largest_start_date.strftime(DATE_FORMAT)

        removed_emps = {}
        # Run if there are changes in partners
        if partner_ids or partner_ids == []:
            curent_emp = []
            for edit_emp in source_rec.partner_ids:
                curent_emp.append(edit_emp.id)
            curent_emp = set(curent_emp)
            edit_emp = set(partner_ids[0][2]) if not current_rec else set(partner_ids)

            removed_emps = curent_emp - edit_emp
            added_emps = edit_emp - curent_emp

            if len(removed_emps) > 0:
                source_rec.edit_emp = self.env['hr.employee'].search([("id", "in", list(removed_emps))])
                template_id_delete_attendens.send_mail(source_rec.id, force_send=True)

            if len(added_emps) > 0:
                source_rec.edit_emp = self.env['hr.employee'].search([("id", "in", list(added_emps))])
                template_id_add_attendens.send_mail(source_rec.id, force_send=True)

        # Removed employees won't receive an email of changes
        source_rec.edit_emp = source_rec.partner_ids.filtered(lambda p: p.id not in removed_emps) if removed_emps else source_rec.partner_ids

        # Send email of changes only when these fields below change
        if start_date or end_date:
            if start_date != source_rec.start_date or end_date != source_rec.end_date or 'room_id' in vals:
                template_id_edit.send_mail(source_rec.id, force_send=True)

    def get_local_tz(self, offset=False):
        user_tz = self.env.user.tz or "UTC"
        if offset:
            tz_offset = timezone(user_tz).utcoffset(datetime.now()).total_seconds() // 3600
            return tz_offset
        return timezone(user_tz)

    # CRUD Methods
    @api.model
    def create(self, vals):
        start_date = vals.get("start_date")
        if not self.check_is_hr() and self._check_is_past_date(start_date):
            raise ValidationError("Start date cannot be in the past")
        vals["is_edit"] = True
        meeting_schedule = super(MeetingSchedule, self).create(vals)

        meeting_schedule._validate_start_date()

        meeting_type = vals.get("meeting_type")

        if meeting_type == "daily" and not vals["parent_id"]:
            meeting_schedule.create_daily()
        elif meeting_type == "weekly" and not vals["parent_id"]:
            meeting_schedule.create_weekly()
        if not vals["parent_id"] \
        and "partner_ids" in vals \
        and len(vals["partner_ids"][0][2]) > 0:
            meeting_schedule.send_meeting_email('booking_room.template_sendmail')
        return meeting_schedule

    def write(self, vals):
        if vals.get("count") !=1:
            for record in self:
                start_date = vals.get("start_date")
                end_date = vals.get("end_date")
                room_id =  vals.get("room_id")
                partner_ids = vals.get('partner_ids')

                if start_date and end_date:
                    local_tz = self.get_local_tz()
                    local_start_date = start_date if isinstance(start_date, datetime) else datetime.strptime(start_date, TIME_STRING_FORMAT).astimezone(local_tz)
                    local_end_date = end_date if isinstance(end_date, datetime) else datetime.strptime(end_date, TIME_STRING_FORMAT).astimezone(local_tz)
                    if local_start_date.date() != local_end_date.date():
                        raise ValidationError("A meeting must end on the same day")

                if not record.check_is_hr() and 'email_sent' not in vals:
                    if self.env.uid != record.user_id.id:
                        raise ValidationError("Cannot modify someone else's meeting")
                    if self._check_is_past_date(record.start_date):
                        raise ValidationError("Cannot edit ongoing or finished meetings")
                    if self._check_is_past_date(start_date):
                        raise ValidationError("Start date cannot be in the past")
                if record.meeting_type == 'normal':
                    if start_date or end_date or room_id or partner_ids:
                        self.send_meeting_email_edit(vals)
        return super(MeetingSchedule, self).write(vals)

    def unlink(self):
        for record in self:
            if not record.check_is_hr(): 
                if self.env.uid != record.user_id.id:
                    raise ValidationError("Cannot delete someone else's meeting")
                if record._check_is_past_date(start_date=record.start_date):
                    raise ValidationError("Cannot delete ongoing or finished meetings.")
        return super(MeetingSchedule, self).unlink()

    @api.model
    def delete_meeting(self, selected_value,reason_delete, id, type_view):
        find_meeting = self.search([("id", "=", id)])
        s=find_meeting.partner_ids
        if self.check_is_hr() == True:
            if selected_value == "self_only":
                find_meeting.reason_delete = reason_delete
                find_meeting.send_meeting_email('booking_room.template_send_mail_delete')
                if type_view!="form_view":
                    return super(MeetingSchedule, find_meeting).unlink()
            elif selected_value == "future_events":
                delete_type = "future_events"
                record_to_detele = self.search([("start_date", ">=", find_meeting.start_date)], order="id")
                record_to_detele.send_mail_delete_attends(reason_delete, record_to_detele, delete_type)
                find_meeting.unlink()
                return super(MeetingSchedule, record_to_detele).unlink()
            else:
                delete_type = "future_events"
                record_to_detele = self.search([], order="id")
                record_to_detele.send_mail_delete_attends(reason_delete, record_to_detele, delete_type)
                return super(MeetingSchedule, record_to_detele).unlink()
        else:
            if find_meeting.user_id.id == self.env.uid:
                if selected_value == "self_only":
                    if self._check_is_past_date(find_meeting.start_date):
                        raise Exception("Cannot delete ongoing or finished meetings.")
                    if type_view!="form_view":
                        find_meeting.delete_type = 'normal'
                        find_meeting.send_meeting_email('booking_room.template_send_mail_delete')
                        return super(MeetingSchedule, find_meeting).unlink()
                elif selected_value == "future_events":
                    record_to_detele = self.search(
                        [
                            ("start_date", ">=", find_meeting.start_date),
                            ("create_uid", "=", self.env.uid),
                        ],
                        order="id"
                    )
                    delete_type = "future_events"
                    record_to_detele.send_mail_delete_attends(reason_delete,record_to_detele,delete_type)
                    return super(MeetingSchedule, record_to_detele).unlink()
                else:
                    record_to_detele = self.search(
                        [
                            ("start_date", ">=", fields.Datetime.now()),
                            ("create_uid", "=", self.env.uid),
                        ],
                        order="id"
                    )
                    delete_type = "future_events"
                    record_to_detele.send_mail_delete_attends(reason_delete,record_to_detele,delete_type)
                    return super(MeetingSchedule, record_to_detele).unlink()
                    
    def send_mail_delete_attends(self, reason_delete, records_to_delete, delete_type):
        name_meeting = ""
        name_room = ""
        attends = set()
        for record in records_to_delete:
            if name_meeting != record.meeting_subject or name_room != record.room_id.name:
                record.reason_delete = reason_delete
                record.delete_type = delete_type
                template_id = self.env.ref('booking_room.template_send_mail_delete', raise_if_not_found=False)
                if template_id:
                    template_id.send_mail(record.id, force_send=True)
                name_meeting = record.meeting_subject
                name_room = record.room_id.name
                attends.update(record.partner_ids.ids)

            new_attendees = set(record.partner_ids.ids) - attends

            if new_attendees:
                attends.update(new_attendees)
                record.reason_delete = reason_delete
                record.delete_type = delete_type
                record.edit_emp = record.partner_ids.filtered(lambda emp: emp.id in new_attendees)
                template_id = self.env.ref('booking_room.template_sendmail_delete_attendens', raise_if_not_found=False)
                if template_id:
                    template_id.send_mail(record.id, force_send=True)

    @api.model
    def write_many(self, data, start_date_str, selected_value, action_type = "form"):
        id = data["id"]
        duration = data["duration"]
        parent_id = data["parent_id"]

        if action_type == "form":
            old_start_date = datetime.strptime(start_date_str, TIME_STRING_FORMAT)
            start_date = datetime.strptime(data["start_date"], TIME_STRING_FORMAT)
            room_id = data["room_id"]["data"]["id"]
            file_attachment_ids = data["file_attachment_ids"]["res_ids"]
            partner_ids = data["partner_ids"]["res_ids"]
        else:
            old_start_date = datetime.strptime(data["start_date"], TIME_STRING_FORMAT)
            start_date = datetime.strptime(start_date_str, TIME_STRING_FORMAT)
            room_id = data["room_id"][0]
            file_attachment_ids = data["file_attachment_ids"]
            partner_ids = data["partner_ids"]

        rec = self.search([('id', '=', id)])

        filter = []
        
        if selected_value == 'this':
            filter = [('id', "=", id)]
        if selected_value == 'future':
            if parent_id == 0: 
                filter = [
                    '|', 
                    ('id', "=", id), 
                    ('parent_id', "=", id),
                    ('start_date','>=', old_start_date),
                ]
            else:
                filter = [
                    '|', 
                    ('id', "=", parent_id), 
                    ('parent_id', "=", parent_id),
                    ('start_date','>=', old_start_date),
                ]
        elif selected_value == 'all':
            if parent_id == 0: filter = ['|', ('id', "=", id), ('parent_id', "=", id)]
            else:
                filter = [
                    '|',
                    ('id', "=", parent_id),
                    ('parent_id', "=", parent_id),
                ]

        if not self.check_is_hr(): filter.append(('start_date','>=', fields.Datetime.now()))

        child_records = self.search(filter, order="start_date ASC" if start_date < old_start_date else "start_date DESC")
        gap = start_date - old_start_date
        recs_to_edit = []

        for rec in child_records:
            new_start_date = datetime.combine((rec.start_date + gap).date(), start_date.time())
            new_end_date = new_start_date + timedelta(hours=duration)
            new_date = new_start_date.astimezone(self.get_local_tz()).date()

            if action_type == 'form':
                vals = {
                    "room_id": room_id,
                    "start_date": new_start_date,
                    "end_date": new_end_date,
                    "meeting_subject": data["meeting_subject"],
                    "description": data["description"],
                    "duration": data["duration"],
                    "repeat_weekly": data["repeat_weekly"],
                    "s_date": new_date,
                    "e_date": new_date,
                    "file_attachment_ids": file_attachment_ids if len(file_attachment_ids) > 0 else None,
                    "partner_ids": partner_ids if len(partner_ids) > 0 else None,
                }
            else:
                vals = {
                    "start_date": new_start_date,
                    "end_date": new_end_date,
                    "duration": data["duration"],
                    "s_date": new_date,
                    "e_date": new_date,
                }
            recs_to_edit.append(vals)

        smallest_start_date = min(d["start_date"] for d in recs_to_edit)
        largest_start_date = max(d["start_date"] for d in recs_to_edit)
            
        mail_data = {
            "id": data["id"],
            "smallest_start_date": smallest_start_date,
            "largest_start_date": largest_start_date,
            "start_date": start_date,
            "end_date": start_date + timedelta(hours=duration),
            "partner_ids": partner_ids if len(partner_ids) > 0 else [],
        }
        if room_id != rec.room_id.id: mail_data["room_id"] = room_id
        self.send_meeting_email_edit(mail_data, edit_type='multi')
        for i, rec in enumerate(child_records): rec.write(recs_to_edit[i])

    @api.model
    def notify_booking(self):
        NOTIFY_MAIL_MINUTES = 10

        current_time = fields.Datetime.now()
        local_tz = self.get_local_tz()
        local_current_time = current_time.astimezone(local_tz)
        records_to_send = self.search([
            ('start_date', '<=', current_time + timedelta(minutes=NOTIFY_MAIL_MINUTES)),
            ('email_sent', '=', False),
            ('s_date', '=', local_current_time.date()),
        ])
        for record in records_to_send:
            # if user create booking when current time is less than 10 minutes from the start of that booking, it wont send notify mail
            if (record.create_date + timedelta(minutes=NOTIFY_MAIL_MINUTES) > record.start_date and self.parent_id == 0):
                record.email_sent = True
            else:
                template_id = self.env.ref('booking_room.template_notify_attendees')
                template_id.send_mail(record.id, force_send=True)
                record.email_sent = True
