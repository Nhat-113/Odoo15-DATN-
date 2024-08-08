from odoo import api, fields, models
from odoo.exceptions import ValidationError
import json
from geopy.geocoders import Nominatim
import geocoder


class CompanyLocation(models.Model):
    _name = 'company.location'
    _rec_name = 'company_id'
    _description = "Company Location"

    lng = fields.Float("Longitude", required=True, digits=(10, 7), default=lambda self: self._default_lng_lat().get('lng'))
    lat = fields.Float("Latitude", required=True, digits=(9, 7), default=lambda self: self._default_lng_lat().get('lat'))
    company_id = fields.Many2one("res.company", required=True)
    employee_ids = fields.Many2many("hr.employee", "location_employee_rel", "location_id", "employee_id", "Employee Access")
    wifi_ids = fields.One2many("location.wifi", "parent_id", string="SSID")
    gmap = fields.Char("Location")
    acceptance_distance = fields.Float("Acceptance Distance(meters)", required=True)
    wifi_access = fields.Boolean('Wifi Access', default = False)
    @api.model
    def _default_lng_lat(self):
        try:
            g = geocoder.ip('me')
            if g.ok:
                return {'lng': g.lng, 'lat': g.lat}
            else:
                return {'lng': 0.0, 'lat': 0.0}
        except Exception as e:
            return {'lng': 0.0, 'lat': 0.0} 

    @api.constrains('lng', 'lat')
    def _check_coordinates(self):
        for record in self:
            if not (-180.0 <= record.lng <= 180.0):
                raise ValidationError("Longitude must be between -180 and 180.")
            if not (-90.0 <= record.lat <= 90.0):
                raise ValidationError("Latitude must be between -90 and 90.")
            
    @api.onchange("lng","lat")
    def onchange_map(self):
        lat = self.lat
        lng = self.lng
        if isinstance(lat, float) or isinstance(lng, float):
            if not (-180.0 <= lng <= 180.0):
                raise ValidationError("The Longitude value is invalid.")
            if not (-90.0 <= lat <= 90.0):
                raise ValidationError("The Latitude value is invalid.")
            self.gmap = json.dumps({
                'position': {'lat': lat, 'lng': lng},
                'zoom': 14
            })
        else:
            raise ValidationError("The Latitude and Longitude are invalid.")

    @api.onchange("acceptance_distance", "company_id")
    def check_vale_acceptance_distance(self):
        company_acceptance_distance = self.company_id.acceptance_distance
        if self.acceptance_distance and company_acceptance_distance:
            if company_acceptance_distance > 0:
                if not (0 <= self.acceptance_distance <= float(company_acceptance_distance)):
                    raise ValidationError("The allowable range for Acceptance Distance (in meters) is from 0 to ", company_acceptance_distance )
            else:
                raise ValidationError("The limit for Acceptance Distance (in meters) has been set to 0.")

    @api.onchange('gmap')
    def onchange_gmap(self):
        if self.gmap:
            gmap_value = json.loads(self.gmap)
            self.lat = gmap_value['position']['lat']
            self.lng = gmap_value['position']['lng']
