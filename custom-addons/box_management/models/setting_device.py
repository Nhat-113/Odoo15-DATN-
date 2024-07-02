from odoo import models, fields, api, exceptions, _
from datetime import datetime
from pytz import timezone
from helper.setting_device_common import create_update_setting, get_day_of_week_value, convert_string_to_time


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

class SettingDevice(models.Model):
    _name = "setting.device"
    _description = "Setting Device"
    _order = "create_date DESC" 
    _inherit = ["mail.thread", "mail.activity.mixin"]
    
    
    name = fields.Char(string="Name", required=True)
    device_ids = fields.Many2many(
        comodel_name="box.management",
        string="Devices",
        relation="device_setting_device_rel",
        column1="type_id",
        column2="device_id",
    )
    start_time = fields.Selection(
        generate_time_selection(),
        string="Start Time",
        store=True,
        required=True
    )
    end_time = fields.Selection(
        generate_time_selection(),
        string="End Time",
        store=True,
        required=True
    )
    time_duration = fields.Char(string="Opening Time", compute='_get_time_duration',)
    
    active = fields.Boolean(required=True, default=True)

    mon = fields.Boolean(string="Mon", readonly=False, default=True)
    tue = fields.Boolean(string="Tue", readonly=False, default=True)
    wed = fields.Boolean(string="Wed", readonly=False, default=True)
    thu = fields.Boolean(string="Thu", readonly=False, default=True)
    fri = fields.Boolean(string="Fri", readonly=False, default=True)
    sat = fields.Boolean(string="Sat", readonly=False, default=False)
    sun = fields.Boolean(string="Sun", readonly=False, default=False)
    number_of = fields.Integer(string="NO", default=1)

            
    def get_local_tz(self, offset=False):
        user_tz = self.env.user.tz or "UTC"
        if offset:
            tz_offset = timezone(user_tz).utcoffset(datetime.now()).total_seconds() // 3600
            return tz_offset
        return timezone(user_tz)

    def check_time_correct(self, start, end):
        return start < end

    @api.depends('start_time', 'end_time')
    def _get_time_duration(self):
        for rec in self:
            rec.time_duration = rec.start_time + " - " + rec.end_time

    @api.model
    def create(self, vals):
        device_ids = vals['device_ids'][0][2]
        week_day = get_day_of_week_value(vals)
        start_time = convert_string_to_time(vals['start_time'])
        end_time = convert_string_to_time(vals['end_time']) 
        
        if not self.check_time_correct(start=start_time, end=end_time):
            raise exceptions.ValidationError(
                ("Start Time cannot be greater than End Time.")
            )

        if not week_day.__contains__(True):
            raise exceptions.ValidationError(_("Please select at least one day of the week"))

        if device_ids:
            get_settings = self.env['setting.device'].search([("device_ids", 'in', device_ids)])
            if get_settings:
                for id in device_ids:    
                    get_setting = get_settings.filtered(lambda x: id in x.device_ids.ids)
                    create_update_setting(device_id=id, settings=get_setting, start_time=start_time, 
                        end_time=end_time, week_day=week_day)
        self._update_sequence_up()
        return super(SettingDevice, self).create(vals)

    def write(self, vals):
        edit = super(SettingDevice, self).write(vals)
        ids = self.device_ids.ids
        week_day = get_day_of_week_value(self)
        start_time = convert_string_to_time(self.start_time)
        end_time = convert_string_to_time(self.end_time) 

        if not self.check_time_correct(start=start_time, end=end_time):
            raise exceptions.ValidationError(
                ("Start Time cannot be greater than End Time.")
            )

        if not week_day.__contains__(True):
            raise exceptions.ValidationError(_("Please select at least one day of the week"))

        if ids:
            get_settings = self.env['setting.device'].search(['&', ("device_ids", 'in', ids), ('id', '!=', self.id)])
            if get_settings:
                for id in ids:
                    get_setting = get_settings.filtered(lambda x: id in x.device_ids.ids)
                    create_update_setting(device_id=id, settings=get_setting, start_time=start_time,
                        end_time=end_time, week_day=week_day)
        return edit

    @api.constrains("end_time", "start_time")
    def _check_time(self):
        for record in self:
            start_object = convert_string_to_time(record.start_time)
            end_object = convert_string_to_time(record.end_time)
            if start_object > end_object:
                raise exceptions.ValidationError(
                    ("Start Time cannot be greater than End Time.")
                )

    def unlink(self):
        update_settings = super(SettingDevice, self).write({"active": False})
        self._update_sequence_down()
        return update_settings

    def _update_sequence_down(self):
        records = self.search([], order='number_of')
        for index, record in enumerate(records):
            record.number_of = index + 1 

    def _update_sequence_up(self):
        records = self.search([], order='number_of')
        for record in records:
            record.number_of += 1