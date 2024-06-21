from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class SmoDeviceLcSchedule(models.Model):
  _name = "smo.device.lc.schedule"
  _description = "SmartOffice LC Devices Schedules"

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

  smo_device_lc_ids = fields.Many2many('smo.device.lc', string="Scheduled Bulbs", required=True)
  smo_asset_id = fields.Many2one('smo.asset', string='Asset')
  smo_device_id = fields.Many2one('smo.device', string='Device')
  
  start_time = fields.Datetime(string="Start Time", default=fields.Datetime.now(),required=True)
  end_time = fields.Datetime(string="End Time", default=fields.Datetime.now())

  state = fields.Boolean(string="Turn Lights On/Off", required=True, default=True)

  cron_start_id = fields.Many2one('ir.cron', string="Cron Start")
  cron_end_id = fields.Many2one('ir.cron', string="Cron End")

  _rec_name = "schedule_name"

  @api.constrains('start_time', 'end_time', 'schedule_mode')
  def _validate_time(self):
    for record in self:
      if record.start_time:
        now = fields.Datetime.now()
        if not record.id and record.start_time < now:
          raise ValidationError("The start time must be in the future for new schedules.")
      
        if record.schedule_mode == "frame" and record.start_time > record.end_time:
          raise ValidationError("The start time must be before the end time.")
        
        if record.schedule_mode == "frame" and record.id and record.end_time < now:
            raise ValidationError("The end time must be in the future.")
  
  @api.constrains('start_time', 'end_time', 'smo_device_lc_ids')
  def _check_time_overlap(self):
    for record in self:
      overlapping_records = self.env['smo.device.lc.schedule'].search([
        ('id', '!=', record.id),
        ('smo_device_lc_ids', 'in', record.smo_device_lc_ids.ids),
        '|',
        '&', ('start_time', '<=', record.start_time), ('end_time', '>=', record.start_time),
        '&', ('start_time', '<=', record.end_time), ('end_time', '>=', record.end_time)
      ])
      if overlapping_records:
        overlapping_info = {}
        for rec in overlapping_records:
          for lc in rec.smo_device_lc_ids:
            if lc.id in record.smo_device_lc_ids.ids:
              key = (lc.device_name, lc.asset_name)
              if key not in overlapping_info:
                overlapping_info[key] = {
                  'schedule_name': rec.schedule_name,
                  'start_time': rec.start_time,
                  'end_time': rec.end_time,
                  'lights': set()
                }
              overlapping_info[key]['lights'].add(lc.param_name)
        
        overlapping_info_str = "\n".join(
          f"Schedule: {info['schedule_name']} (Time: {info['start_time'].strftime('%H:%M:%S %d-%m-%Y')} - {info['end_time'].strftime('%H:%M:%S %d-%m-%Y')})\n"
          f"Device: {device_name} (Asset: {asset_name})\n"
          f"Lights: {', '.join(info['lights'])}\n"
          for (device_name, asset_name), info in overlapping_info.items()
        )

        raise ValidationError(
          f"This schedule overlaps with the following existing schedules:\n{overlapping_info_str}"
        )


  @api.onchange('target_type', 'smo_asset_id', 'smo_device_id')
  def _onchange_target_type(self):
    self.smo_device_lc_ids = [(5, 0, 0)]
    if self.target_type == 'custom':
      self.smo_asset_id = False
      self.smo_device_id = False
    elif self.target_type == 'asset' and self.smo_asset_id:
      self.smo_device_id = False
      self.smo_device_lc_ids = [(6, False, self.get_asset_lc_ids().ids)]
    elif self.target_type == 'device' and self.smo_device_id:
      self.smo_asset_id = False
      self.smo_device_lc_ids = [(6, False, self.smo_device_id.smo_device_lc_ids.ids)]

  @api.model
  def get_asset_lc_ids(self):
    self.ensure_one()
    if self.smo_asset_id:
      return self.env['smo.device.lc'].search([('asset_control_id', '=', self.smo_asset_id.asset_id)])
    return self.env['smo.device.lc']

  @api.model
  def create(self, vals):
    record = super(SmoDeviceLcSchedule, self).create(vals)
    if record.target_type == 'asset' and record.smo_asset_id:
      record.smo_device_lc_ids = [(6, 0, record.get_asset_lc_ids().ids)]
    elif record.target_type == 'device' and record.smo_device_id:
      record.smo_device_lc_ids = [(6, 0, record.smo_device_id.smo_device_lc_ids.ids)]
    record.create_cronjob_for_schedule()
    return record

  def create_cronjob_for_schedule(self):
    cron_start_vals = {
      'name': f'Turn {"on" if self.state == True else "off"} at {self.start_time}',
      'model_id': self.env.ref('smo.model_smo_device_lc_schedule').id,
      'state': 'code',
      'code': f"model.execute_scheduled_action({self.id})",
      'user_id': 1,
      'interval_number': 1,
      'interval_type': 'minutes',
      'numbercall': 1,
      'nextcall': self.start_time,
    }
    self.cron_start_id = self.env['ir.cron'].create(cron_start_vals)

    if self.schedule_mode == 'frame':
      cron_end_vals = {
        'name': f'Turn {"off" if self.state == True else "on"} at {self.end_time}',
        'model_id': self.env.ref('smo.model_smo_device_lc_schedule').id,
        'state': 'code',
        'code': f"model.execute_scheduled_action({self.id})",
        'user_id': 1,
        'interval_number': 1,
        'interval_type': 'minutes',
        'numbercall': 1,
        'nextcall': self.end_time,
      }
      self.cron_end_id = self.env['ir.cron'].create(cron_end_vals)

  def write(self, vals):
    res = super(SmoDeviceLcSchedule, self).write(vals)
    for record in self:
      if 'target_type' in vals or 'smo_asset_id' in vals or 'smo_device_id' in vals:
        if record.target_type == 'asset' and record.smo_asset_id:
          record.smo_device_lc_ids = [(6, 0, record.get_asset_lc_ids().ids)]
        elif record.target_type == 'device' and record.smo_device_id:
          record.smo_device_lc_ids = [(6, 0, record.smo_device_id.smo_device_lc_ids.ids)]

      if 'start_time' in vals or 'end_time' in vals or 'state' in vals:  
        name = f'Turn {"on" if record.state == True else "off"} at '
        if record.cron_start_id:
          record.cron_start_id.write({
            'nextcall': record.start_time,
            'name': name + f'{record.start_time}',
          })
        if record.cron_end_id:
          record.cron_end_id.write({
            'nextcall': record.end_time,
            'name': name + f'{record.end_time}',
          })

    return res

  @api.model
  def execute_scheduled_action(self, schedule_record_id):
    schedule_record = self.search([('id', '=', schedule_record_id)], limit=1)
    if not schedule_record:
      raise UserError('LC Schedule record not found.')

    now = fields.Datetime.now()
    start = schedule_record.start_time
    end = schedule_record.end_time
    
    state = True
    if now >= end:
      state = not schedule_record.state
    elif now >= start:
      state = schedule_record.state
    for lc_record in schedule_record.smo_device_lc_ids:
      self.env['smo.device.lc'].change_light_state(lc_record.device_id, lc_record.param_name, state, update_local=True)    

  def unlink(self):
    for record in self:
      if record.cron_start_id:
        record.cron_start_id.unlink()
      if record.cron_end_id:
        record.cron_end_id.unlink()
    return super(SmoDeviceLcSchedule, self).unlink()


