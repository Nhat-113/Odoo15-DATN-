# -*- coding: utf-8 -*-

from datetime import datetime, time, timedelta
from odoo import api, fields, models, exceptions, _
from pytz import timezone, utc

def _get_user_time(self, hour, minute, second):
  user_tz = self.env.user.tz
  tz = timezone(user_tz) or utc
  user_time = datetime.now().astimezone(tz).replace(hour=hour, minute=minute, second=second)
  final_utc_time = user_time.astimezone(timezone('UTC')).replace(tzinfo=None)
  return final_utc_time


class Passcode(models.Model):
    _name = "passcode.register"
    _description = "Passcode"
    _rec_name = "name"
    
    name = fields.Char(string=_("Name"), required=True)
    passcode = fields.Char(string=_("Passcode"), required=True, size=4)
    device_ids = fields.Many2many(
        comodel_name="box.management",
        string=_("Devices"),
        relation="device_passcode_rel",
        column1="passcode_id",
        column2="device_id",
    )
    active = fields.Boolean(required=True, default=True)
    
    def _get_current_time(self):
      user_time = _get_user_time(self, 0, 0, 0)
      return user_time
    def _get_time_max(self): 
      user_time = _get_user_time(self, 23, 59, 59)
      return user_time

    valid_from = fields.Datetime(string="Valid From Date", default=_get_current_time)
    expired_date = fields.Datetime(string="Expired Date", default=_get_time_max)

    @api.constrains("valid_from", "expired_date")
    def _check_dates(self):
        for record in self:
            if record.valid_from > record.expired_date:
                raise exceptions.ValidationError(
                    ("Valid From date cannot be greater than Expired Date.")
                )
    
    @api.constrains("passcode")
    def _check_passcode(self):
        for record in self:
            if len(record.passcode) != 4:
                raise exceptions.ValidationError(_("Passcode must be 4 digits."))
            if not record.passcode.isdigit():
                raise exceptions.ValidationError(_("Passcode must be numeric."))

    def unlink(self):
        update_passcode_remove = super(Passcode, self).write({"active": False})
        return update_passcode_remove
