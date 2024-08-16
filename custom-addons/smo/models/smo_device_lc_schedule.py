from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import datetime
from pytz import timezone, UTC
from helper.smo_helper import generate_time_selection
import pytz
from odoo import tools
import logging

_logger = logging.getLogger(__name__)

START_TIME_MISSING_ANNOUNCE = 'Invalid Input: Start Time must be provided'
START_TIME_IN_PAST_ANNOUNCE = 'Invalid Input: Start Time must not be in the past'
END_TIME_MISSING_ANNOUNCE = 'Invalid Input: End Time must be provided in Time Frame mode'
START_TIME_AFTER_END_TIME_ANNOUNCE = 'Invalid Input: End Time must be after Start Time'
END_TIME_IN_PAST_ANNOUNCE = 'Invalid Input: End Time must be in the future'
NO_DAY_IN_WEEK_ANNOUNCE = 'Invalid Input: You must choose at least one day in week'

class SmoDeviceLcSchedule(models.Model):
    _name = "smo.device.lc.schedule"
    _description = "SmartOffice LC Devices Schedules"
    _rec_name = "schedule_name"

    schedule_name = fields.Char(string="Schedule Name", required=True)

    target_type = fields.Selection([
        ('custom', 'Custom'),
        ('device', 'Device'),
        ('asset', 'Asset'),
    ], string="Selection Type", required=True, default='custom')

    schedule_mode = fields.Selection([
        ('once', 'One-time'),
        ('frame', 'Time Frame'),
    ], string="Schedule Mode", required=True, default='once')

    repeat_daily = fields.Boolean(string="Repeat Daily", default=False)
    custom_day =fields.Boolean(string="Customize", default=False)

    monday = fields.Boolean(string="Monday", default=True)
    tuesday = fields.Boolean(string="Tuesday", default=True)
    wednesday = fields.Boolean(string="Wednesday", default=True)
    thursday = fields.Boolean(string="Thursday", default=True)
    friday = fields.Boolean(string="Friday", default=True)
    saturday = fields.Boolean(string="Saturday", default=False)
    sunday = fields.Boolean(string="Sunday", default=False)

    smo_device_lc_ids = fields.Many2many('smo.device.lc', string="Scheduled Bulbs", required=True)
    smo_asset_id = fields.Many2one('smo.asset', string='Asset')
    devices_selections = fields.Selection(selection="_get_devices_for_lc_schedule", string="Device")

    start_time = fields.Datetime(string="Start Time", default=lambda self: fields.Datetime.now(),)
    end_time = fields.Datetime(string="End Time")

    start_time_daily = fields.Selection(generate_time_selection(), string="Start Time Daily", store=True,)
    end_time_daily = fields.Selection(generate_time_selection(), string="End Time Daily", store=True,)
    
    start_time_daily_utc = fields.Char(string="Start Time Daily UTC", compute='_compute_start_daily_utc', store=True)
    end_time_daily_utc = fields.Char(string="End Time Daily UTC", compute='_compute_end_daily_utc', store=True)

    state = fields.Boolean(string="Turn Lights On/Off", required=True, default=True)

    cron_start_ids = fields.One2many('ir.cron', 'smo_device_lc_schedule_id_start', string="Cron Starts")
    cron_end_ids = fields.One2many('ir.cron', 'smo_device_lc_schedule_id_end', string="Cron Ends")
    
    state_display = fields.Char(string="Turn On/Off", compute='_compute_state_display')
    
    @api.model
    def _get_devices_for_lc_schedule(self):
        device_ids = self.env['smo.device'].search([('device_type', '=', 'LC')])
        devices = [(device.device_id, device.device_name) for device in device_ids]
        return list(set(devices))
    
    @api.depends('state')
    def _compute_state_display(self):
        for record in self:
            record.state_display = "Turn ON" if record.state else "Turn OFF"
            
    def _convert_time_string_local_to_utc(self, time_string):
        hour, minute = map(int, time_string.split(':'))
        today_datetime = fields.Datetime.now()
        today_datetime_local = self._convert_to_local_time(today_datetime)
        today_datetime_local = today_datetime_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        utc_datetime = today_datetime_local.astimezone(UTC).replace(tzinfo=None)
        utc_time = utc_datetime.time()
        
        return utc_time

    @api.depends('start_time_daily')
    def _compute_start_daily_utc(self):
        for record in self:
            if record.start_time_daily:
                record.start_time_daily_utc = self._convert_time_string_local_to_utc(record.start_time_daily)

    @api.depends('end_time_daily')
    def _compute_end_daily_utc(self):
        for record in self:
            if record.end_time_daily:
                record.end_time_daily_utc = self._convert_time_string_local_to_utc(record.end_time_daily)
    
    def _validate_time_for_repeating_schedule(self):
        for record in self:
            if record.repeat_daily == True:
                if not record.start_time_daily:
                    raise ValidationError(START_TIME_MISSING_ANNOUNCE)
                
                if record.custom_day and not any([record.monday, record.tuesday, record.wednesday, record.thursday, record.friday, record.saturday, record.sunday]):
                    raise ValidationError(NO_DAY_IN_WEEK_ANNOUNCE)

                if record.schedule_mode == 'frame':
                    if not record.end_time_daily:
                        raise ValidationError(END_TIME_MISSING_ANNOUNCE)

                    if record.start_time_daily >= record.end_time_daily:
                        raise ValidationError(START_TIME_AFTER_END_TIME_ANNOUNCE)

    def _validate_time_for_schedule(self):
        now = fields.Datetime.now()
        for record in self:
            if record.repeat_daily == False:
                if not record.start_time:
                    raise ValidationError(START_TIME_MISSING_ANNOUNCE)
                
                if record.start_time < now and record.schedule_mode != "frame":
                    raise ValidationError(START_TIME_IN_PAST_ANNOUNCE)

                if record.schedule_mode == "frame":
                    if record.start_time >= record.end_time:
                        raise ValidationError(START_TIME_AFTER_END_TIME_ANNOUNCE)

                    if record.id and record.end_time < now:
                        raise ValidationError(END_TIME_IN_PAST_ANNOUNCE)

    @api.constrains('start_time', 'end_time', 'start_time_daily', 'end_time_daily', 'repeat_daily', 'schedule_mode', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'smo_device_lc_ids')
    def _check_schedule_overlap(self):
        for record in self:
            if record.repeat_daily:
                record._validate_time_for_repeating_schedule()
                record._check_overlap_for_repeating_schedule()
            else:
                record._validate_time_for_schedule()
                record._check_overlap_for_schedule()

    def _check_overlap_for_repeating_schedule(self):
        for record in self:
            schedules = self._get_overlapped_devices_schedules(record)
            if not schedules:
                return

            start_time = self._parse_time(record.start_time_daily)
            end_time = self._parse_time(record.end_time_daily) if record.schedule_mode == 'frame' else None

            for schedule in schedules:
                overlapped_days = record._get_overlapped_days(schedule)
                if overlapped_days:
                    if schedule.repeat_daily:
                        schedule_start_time = self._parse_time(schedule.start_time_daily)
                        schedule_end_time = self._parse_time(schedule.end_time_daily) if schedule.schedule_mode == 'frame' else None
                    else:
                        schedule_start_time = self._convert_to_local_time(schedule.start_time).time()
                        schedule_end_time = self._convert_to_local_time(schedule.end_time).time() if schedule.schedule_mode == 'frame' else None
                    
                    if record.state != schedule.state:
                        check_overlap = self._is_time_point_overlap
                    else:
                        check_overlap = self._is_time_overlap

                    if check_overlap(start_time, end_time, schedule_start_time, schedule_end_time):
                        raise ValidationError(record._get_overlapped_validation_err_messages(schedule))

    def _check_overlap_for_schedule(self):
        for record in self:
            schedules = self._get_overlapped_devices_schedules(record)
            if not schedules:
                continue

            for schedule in schedules:
                if record.state != schedule.state:
                    check_overlap = self._is_time_point_overlap
                else:
                    check_overlap = self._is_time_overlap

                if schedule.repeat_daily:
                    overlapped_days = record._get_overlapped_days(schedule)
                    if overlapped_days:
                        record_start_time = self._convert_to_local_time(record.start_time).time()
                        record_end_time = self._convert_to_local_time(record.end_time).time() if record.schedule_mode == 'frame' else None

                        schedule_start_time = self._parse_time(schedule.start_time_daily)
                        schedule_end_time = self._parse_time(schedule.end_time_daily) if schedule.schedule_mode == 'frame' else None

                        if check_overlap(record_start_time, record_end_time, schedule_start_time, schedule_end_time):
                            raise ValidationError(record._get_overlapped_validation_err_messages(schedule))
                else:
                    if check_overlap(record.start_time, record.end_time, schedule.start_time, schedule.end_time):
                        raise ValidationError(record._get_overlapped_validation_err_messages(schedule))
    
    def _get_overlapped_validation_err_messages(self, conflicting_schedule):
        start_part = f'Your schedule overlaps with the following schedule: {conflicting_schedule.schedule_name}\n'
        devices_part = self._format_devices_part(conflicting_schedule)
        time_part = self._format_time_part(conflicting_schedule)
        suggest_part = '\n\tPlease pick another time to schedule your bulbs!'
        return start_part + devices_part + time_part + suggest_part

    def _format_devices_part(self, conflicting_schedule):
        overlapped_devices = set(self.smo_device_lc_ids) & set(conflicting_schedule.smo_device_lc_ids)
        overlapped_devices_names = sorted(device.param_name for device in overlapped_devices)
        devices_string = ', '.join(overlapped_devices_names)
        return f'Detail:\n\tThese bulbs: {devices_string} were already set on schedule '

    def _format_time_part(self, conflicting_schedule):
        if conflicting_schedule.repeat_daily:
            return self._format_repeat_daily_time_part(conflicting_schedule)
        return self._format_one_time_time_part(conflicting_schedule)

    def _format_repeat_daily_time_part(self, conflicting_schedule):
        if conflicting_schedule.schedule_mode == 'frame':
            time_part = f'from {conflicting_schedule.start_time_daily} to {conflicting_schedule.end_time_daily} '
        else:
            time_part = f'at {conflicting_schedule.start_time_daily} '
        days_string = ', '.join(day.capitalize() for day in conflicting_schedule._get_selected_days())
        return time_part + f'on {days_string}'

    def _format_one_time_time_part(self, conflicting_schedule):
        local_start_time = self._convert_to_local_time(conflicting_schedule.start_time).strftime('%H:%M:%S on %d/%m/%Y')
        if conflicting_schedule.schedule_mode == 'frame':
            local_end_time = self._convert_to_local_time(conflicting_schedule.end_time).strftime('%H:%M:%S on %d/%m/%Y')
            return f'from {local_start_time} to {local_end_time}'
        return f'at {local_start_time}'

    def _is_time_overlap(self, start1, end1, start2, end2):
        end1 = end1 or start1
        end2 = end2 or start2

        return (start1 <= start2 <= end1) or (start2 <= start1 <= end2)
    
    def _is_time_point_overlap(self, start1, end1, start2, end2):
        end1 = end1 or start1
        end2 = end2 or start2

        return start1 in {start2, end2} or end1 in {start2, end2}

    def _convert_to_local_time(self, utc_time):
        return fields.Datetime.context_timestamp(self, utc_time)

    def _parse_time(self, time_str, second=False):
        format = '%H:%M:%S' if second else '%H:%M'
        return datetime.datetime.strptime(time_str, format).time()

    def _get_overlapped_devices_schedules(self, record):
        return self.search([
            ('id', '!=', record.id),
            ('smo_device_lc_ids', 'in', record.smo_device_lc_ids.ids)
        ])

    def _get_selected_days(self):
        self.ensure_one()
        days_in_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        if self.repeat_daily:
            days = [day for day in days_in_week if getattr(self, day)]
        else:
            start_date = self._convert_to_local_time(self.start_time).date()
            end_date = self._convert_to_local_time(self.end_time).date() if self.schedule_mode == 'frame' else None
            days = [days_in_week[start_date.weekday()]]
            if end_date:
                days.append(days_in_week[end_date.weekday()])

        return sorted(set(days), key=lambda x: days_in_week.index(x))

    def _get_overlapped_days(self, compared_schedule):
        self.ensure_one()
        self_days = self._get_selected_days()
        compared_schedule_days = compared_schedule._get_selected_days()
        return set(self_days) & set(compared_schedule_days)

    @api.onchange('target_type', 'smo_asset_id', 'devices_selections')
    def _onchange_target_type(self):
        for record in self:
            record.smo_device_lc_ids = [(5, 0, 0)]
            select_type = self.target_type
            if select_type == 'custom':
                self.smo_asset_id = None
                self.devices_selections = None
            elif select_type == 'asset':
                self.devices_selections = None
            elif select_type == 'device':
                self.smo_asset_id = None
            record._set_lc_ids_by_asset_or_device()

    @api.onchange('custom_day')
    def _onchange_custom_day(self):
        for record in self:
            if not record.custom_day:
                record.monday = record.tuesday = record.wednesday = record.thursday = record.friday = True
                record.saturday = record.sunday = False

    @api.model
    def _get_asset_lc_ids(self):
        self.ensure_one()
        if self.smo_asset_id:
            return self.env['smo.device.lc'].search([('asset_control_id', '=', self.smo_asset_id.asset_id)])
        return self.env['smo.device.lc']
    
    @api.model
    def _get_device_lc_ids(self):
        self.ensure_one()
        if self.devices_selections:
            return self.env['smo.device.lc'].search([('device_id', '=', self.devices_selections)])
        return self.env['smo.device.lc']
    
    @api.model
    def create(self, vals):
        record = super(SmoDeviceLcSchedule, self).create(vals)
        record._set_lc_ids_by_asset_or_device()
        record._create_and_update_cronjob_for_schedule()
        return record
    
    @api.onchange('schedule_mode')
    def _onchange_schedule_mode(self):
        if self.schedule_mode == 'frame' and self.repeat_daily == False:
            self.end_time = fields.Datetime.now()

    def create_cron(self, name, time, schedule_id_start=False, schedule_id_end=False):
        return self.env['ir.cron'].create({
            'name': name,
            'model_id': self.env.ref('smo.model_smo_device_lc_schedule').id,
            'state': 'code',
            'code': f"model.execute_scheduled_action({self.id})",
            'user_id': 1,
            'interval_number': 1,
            'interval_type': 'weeks' if self.repeat_daily == True else 'minutes',
            'numbercall': -1 if self.repeat_daily == True else 1,
            'nextcall': time,
            'priority': 1,
            'smo_device_lc_schedule_id_start': schedule_id_start,
            'smo_device_lc_schedule_id_end': schedule_id_end,
        })

    def _create_and_update_crons_for_onetime_schedules(self):
        now = fields.Datetime.now()
        for record in self:
            local_start_time = record._convert_to_local_time(record.start_time).strftime('%H:%M:%S on %d/%m/%Y')
            start_cron_name = f'[{record.schedule_name}] Turn lights {"on" if record.state == True else "off"} at {local_start_time}'
            
            if record.start_time > now:
                if record.cron_start_ids:
                    record.cron_start_ids.write({'nextcall': record.start_time, 'name': start_cron_name})
                else:
                    start_cron = record.create_cron(start_cron_name, record.start_time, schedule_id_start=record.id)
                    record.cron_start_ids = [(4, start_cron.id)]

            if record.schedule_mode == 'frame':
                local_end_time = record._convert_to_local_time(record.end_time).strftime('%H:%M:%S on %d/%m/%Y')
                end_cron_name = f'[{record.schedule_name}] Turn lights {"off" if record.state == True else "on"} at {local_end_time}'
                
                if record.cron_end_ids:
                    record.cron_end_ids.write({'nextcall': record.end_time, 'name': end_cron_name})
                else:
                    end_cron = record.create_cron(end_cron_name, record.end_time, schedule_id_end=record.id)
                    record.cron_end_ids = [(4, end_cron.id)]
            elif record.schedule_mode == 'once' and record.cron_end_ids:
                record.cron_end_ids.unlink()

    def _create_and_update_crons_for_repeating_schedules(self):
        for record in self:
            days_mapping = {
                'monday': '0',
                'tuesday': '1',
                'wednesday': '2',
                'thursday': '3',
                'friday': '4',
                'saturday': '5',
                'sunday': '6'
            }
            days_to_create_crons = record._get_selected_days()

            existing_start_crons = {cron.name.split()[-1].lower(): cron for cron in record.cron_start_ids}
            existing_end_crons = {cron.name.split()[-1].lower(): cron for cron in record.cron_end_ids}

            self._unlink_not_selected_days_crons(existing_start_crons, days_to_create_crons)
            self._unlink_not_selected_days_crons(existing_end_crons, days_to_create_crons)

            for day, code in days_mapping.items():
                if day in days_to_create_crons:
                    start_time = record._get_next_call_datetime(record.start_time_daily, code)
                    start_cron_name = f'[{record.schedule_name}] Turn {"on" if record.state == True else "off"} lights on {day.capitalize()}'
                    
                    if day in existing_start_crons:
                        existing_start_crons[day].write({'nextcall': start_time, 'name': start_cron_name})
                    else:
                        start_cron = record.create_cron(start_cron_name, start_time, schedule_id_start=record.id)
                        record.cron_start_ids = [(4, start_cron.id)]

                    if record.schedule_mode == 'frame':
                        end_time = record._get_next_call_datetime(record.end_time_daily, code)
                        end_cron_name = f'[{record.schedule_name}] Turn {"off" if record.state == True else "on"} lights on {day.capitalize()}'
                        
                        if day in existing_end_crons:
                            existing_end_crons[day].write({'nextcall': end_time, 'name': end_cron_name})
                        else:
                            end_cron = record.create_cron(end_cron_name, end_time, schedule_id_end=record.id)
                            record.cron_end_ids = [(4, end_cron.id)]
                    elif day in existing_end_crons:
                        existing_end_crons[day].unlink()

    def _create_and_update_cronjob_for_schedule(self):
        if self.repeat_daily:
            self._create_and_update_crons_for_repeating_schedules()
        else:
            self._create_and_update_crons_for_onetime_schedules()

    def _unlink_not_selected_days_crons(self, existing_crons, crr_selected_days):
        for day, cron in existing_crons.items():
            if day not in crr_selected_days:
                cron.unlink()

    def _get_next_call_datetime(self, time_str, day_of_week_code):
        hour, minute = map(int, time_str.split(':'))

        today_local = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        today_day_of_week_local = today_local.weekday()

        days_ahead = int(day_of_week_code) - today_day_of_week_local
        if days_ahead < 0 or (days_ahead == 0 and (hour, minute) <= (today_local.hour, today_local.minute)):
            days_ahead += 7

        next_call_date_local = today_local + datetime.timedelta(days=days_ahead)
        next_call_local = next_call_date_local.replace(hour=hour, minute=minute, second=0, microsecond=0)

        next_call_utc = next_call_local.astimezone(UTC).replace(tzinfo=None)

        return next_call_utc

    def _unlink_all_crons(self):
        for record in self:
            if record.cron_start_ids:
                record.cron_start_ids.unlink()
            if record.cron_end_ids:
                record.cron_end_ids.unlink()

    def _set_lc_ids_by_asset_or_device(self):
        if self.target_type == 'asset' and self.smo_asset_id:
            self.smo_device_lc_ids = [(6, 0, self._get_asset_lc_ids().ids)]
        elif self.target_type == 'device':
            self.smo_device_lc_ids = [(6, 0, self._get_device_lc_ids().ids)]

    def write(self, vals):
        res = super(SmoDeviceLcSchedule, self).write(vals)
        for record in self:
            if any(field in vals for field in {'target_type', 'smo_asset_id', 'devices_selections'}):
                self._set_lc_ids_by_asset_or_device()

            if 'repeat_daily' in vals:
                record._unlink_all_crons()

            trigger_fields = {
                'repeat_daily', 'schedule_mode', 'state',
                'start_time', 'end_time', 'start_time_daily', 'end_time_daily',
                'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
            }

            if any(field in vals for field in trigger_fields):
                record._create_and_update_cronjob_for_schedule()

        return res

    @api.model
    def execute_scheduled_action(self, schedule_record_id):
        schedule_record = self.search([('id', '=', schedule_record_id)], limit=1)
        if not schedule_record:
            raise UserError('Lighting Schedule record not found.')

        mode = schedule_record.schedule_mode
        now = fields.Datetime.now()
        
        if schedule_record.repeat_daily:
            now = now.time()
            end = self._parse_time(schedule_record.end_time_daily_utc, second=True) if mode == 'frame' else None
        else:
            end = schedule_record.end_time if mode == 'frame' else None

        state = schedule_record.state

        if mode == 'frame' and end and now >= end:
            state = not state
        if schedule_record.smo_device_lc_ids:
            schedule_record.smo_device_lc_ids.write({'current_state': state})
        


