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
    time_duration = fields.Char(string=_("Opening Time"), compute='_get_time_duration',)
    
    active = fields.Boolean(required=True, default=True, string="Active")

    mon = fields.Boolean(string=_("Mon"), readonly=False, default=True)
    tue = fields.Boolean(string=_("Tue"), readonly=False, default=True)
    wed = fields.Boolean(string=_("Wed"), readonly=False, default=True)
    thu = fields.Boolean(string=_("Thu"), readonly=False, default=True)
    fri = fields.Boolean(string=_("Fri"), readonly=False, default=True)
    sat = fields.Boolean(string=_("Sat"), readonly=False, default=False)
    sun = fields.Boolean(string=_("Sun"), readonly=False, default=False)
    # number_of = fields.Integer(string="NO", default=1)
    list_days = fields.Text(string="Opening Day", readonly=True, compute='_get_field_day')
    status = fields.Selection(
        string=_("Status"),
        default="active",
        required=True, 
        selection=[
            ("active", _("Active")),
            ("inactive", _("Inactive")),
    ])


    
    def _get_field_day(self):
        days = [_('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'), _('Friday'), _('Saturday'), _('Sunday')]
        for rec in self:
            days_array = [x for x,y in zip(days, get_day_of_week_value(rec)) if y]
            rec.list_days = ", ".join(f"{day}" for day in days_array)

    def get_local_tz(self, offset=False):
        user_tz = self.env.user.tz or "UTC"
        if offset:
            tz_offset = timezone(user_tz).utcoffset(datetime.now()).total_seconds() // 3600
            return tz_offset
        return timezone(user_tz)

    @api.depends('start_time', 'end_time')
    def _get_time_duration(self):
        for rec in self:
            rec.time_duration = rec.start_time + " - " + rec.end_time

    @api.model
    def create(self, vals):
        device_ids = vals['device_ids'][0][2]
        start_time = convert_string_to_time(vals['start_time'])
        end_time = convert_string_to_time(vals['end_time'])
        week_day = get_day_of_week_value(vals)
        
        if start_time >= end_time:
            raise exceptions.ValidationError("Start Time cannot be greater than End Time.")

        if not any(week_day):
            raise exceptions.ValidationError(_("Please select at least one day of the week"))

        new_record = super(SettingDevice, self).create(vals)
        if device_ids:
            get_settings = self.env['setting.device'].search([("device_ids", 'in', device_ids)])
            devices = self.env['box.management'].browse(device_ids)

            for device in devices:
                get_setting = get_settings.filtered(lambda x: device.id in x.device_ids.ids)
                create_update_setting(
                    device_id=device.device_id,
                    settings=get_setting,
                    start_time=start_time,
                    end_time=end_time,
                    week_day=week_day,
                    active=True,
                    status=vals['status']
                )
                self.env['schedule.device.rel'].create({
                        'schedule_id': new_record.id,
                        'device_id': device.device_id,
                        'active': True, 
                    })
        
        return new_record

    def write(self, vals):
        start_time = convert_string_to_time(self.start_time)
        end_time = convert_string_to_time(self.end_time) 
        if start_time >= end_time:
            raise exceptions.ValidationError("Start Time cannot be greater than End Time.")

        week_day = get_day_of_week_value(self)
        if not any(week_day):
            raise exceptions.ValidationError(_("Please select at least one day of the week"))

        if "device_ids" in vals:
            vals_divices = vals["device_ids"][0][2]
            if len(vals_divices) < len(self.device_ids):
                devices_removed = list(set(self.device_ids.ids) - set(vals_divices))
                devices = self.env['box.management'].search([('id', 'in', devices_removed)])
                device_id = []
                for device in devices:
                    device_id.append(device.device_id)

                schedule_rel = self.env['schedule.device.rel'].search([('schedule_id', '=', self.id), ('device_id', 'in', device_id)])
                data_update = {
                    "active": False,
                }
                schedule_rel.update(data_update)
            else:
                devices = self.env['box.management'].search([('id', 'in', vals_divices)])
                schedule_rel = self.env['schedule.device.rel'].search([('schedule_id', '=', self.id)])
                if schedule_rel:
                    for item in devices:
                        data_update = {
                            'device_id': item.device_id,
                            'active': True, 
                        }
                        schedule_rel.update(data_update)
                else:
                    for item in devices:
                        data_update = {
                            'schedule_id': self.id,
                            'device_id': item.device_id,
                            'active': True, 
                        }
                        schedule_rel.create(data_update)

        edit = super(SettingDevice, self).write(vals)
        device_ids = self.device_ids.ids

        schedule_rel = self.env['schedule.device.rel'].sudo().with_context(active_test=False).search([('schedule_id', '=', self.id)])
        if "status" in vals and vals['status'] == "active":
            schedule_rel.update({"active": True})
            self.update({"active": True})
        elif "status" in vals and vals['status'] == "inactive":
            schedule_rel.update({"active": False})

        if device_ids:
            get_settings = self.env['setting.device'].search([("device_ids", 'in', device_ids), ('id', '!=', self.id)])
            devices = self.env['box.management'].browse(device_ids)

            for device in devices:
                get_setting = get_settings.filtered(lambda x: device.id in x.device_ids.ids)
                create_update_setting(
                    device_id=device.device_id,
                    settings=get_setting,
                    start_time=start_time,
                    end_time=end_time,
                    week_day=week_day,
                    status=self.status,
                    active=self.active
                )

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
        schedule_rel = self.env['schedule.device.rel'].search([('schedule_id', 'in', self.ids)])
        schedule_rel.update({"active": False})
        return super(SettingDevice, self).write({"active": False, "status": "inactive"})

    def action_archive(self):   
        schedule_rel = self.env['schedule.device.rel'].search([('schedule_id', 'in', self.ids)])
        schedule_rel.update({"active": False})
        return super(SettingDevice, self).write({"active": False, "status": "inactive"})

    def action_unarchive(self):
        return super(SettingDevice, self).write({"active": True, "status": "active"})


    # def _update_sequence_down(self):
    #     records = self.search([], order='number_of')
    #     for index, record in enumerate(records):
    #         record.number_of = index + 1 

    # def _update_sequence_up(self):
    #     records = self.search([], order='number_of')
    #     for record in records:
    #         record.number_of += 1