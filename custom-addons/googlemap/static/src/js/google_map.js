odoo.define('googlemap.FieldGoogleMap', function(require) {
    "use strict";
    var field_registry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');

    var FieldGoogleMap = AbstractField.extend({
        template: 'FieldGoogleMap',

        start: function() {
            var self = this;
            self.init_map();
            return this._super();
        },

        init_map: function () {
            var self = this;
            var $searchBoxElement = $(this.el).find('#company_location_google_map_search')[0];
            var $mapElement = $(this.el).find('#company_location_googlemap')[0];

            var searchBox = new google.maps.places.SearchBox($searchBoxElement);
            var markers = [];

            searchBox.addListener('places_changed', function() {
                var places = searchBox.getPlaces();
                if (places.length == 0) {
                    return;
                }

                markers.forEach(function(marker) {
                    marker.setMap(null);
                });
                markers = [];

                var bounds = new google.maps.LatLngBounds();
                places.forEach(function(place) {
                    if (!place.geometry) {
                        return;
                    }
                    var icon = {
                        url: place.icon,
                        size: new google.maps.Size(71, 71),
                        origin: new google.maps.Point(0, 0),
                        anchor: new google.maps.Point(17, 34),
                        scaledSize: new google.maps.Size(25, 25)
                    };

                    markers.push(new google.maps.Marker({
                        map: self.map,
                        icon: icon,
                        title: place.name,
                        position: place.geometry.location
                    }));

                    if (place.geometry.viewport) {
                        bounds.union(place.geometry.viewport);
                    } else {
                        bounds.extend(place.geometry.location);
                    }
                });
                self.map.fitBounds(bounds);
            });

            this.map = new google.maps.Map($mapElement, {
                center: {lat: 0, lng: 0},
                zoom: 14,
                disableDefaultUI: true,
            });

            this.marker = new google.maps.Marker({
                position: {lat: 0, lng: 0},
                draggable: true,
                map: null
            });

            if (this.value) {
                this.marker.setPosition(JSON.parse(this.value).position);
                this.map.setCenter(JSON.parse(this.value).position);
                this.map.setZoom(JSON.parse(this.value).zoom);
                this.marker.setMap(this.map);
            }

            this.map.addListener('click', function(e) {
                if (self.mode === 'edit') {
                    self.marker.setMap(null);
                    self.marker.setPosition(e.latLng);
                    self.marker.setMap(self.map);
                    self._setValue(JSON.stringify({
                        position: self.marker.getPosition(),
                        zoom: self.map.getZoom()
                    }));
                }
            });

            this.map.addListener('zoom_changed', function() {
                if (self.mode === 'edit' && self.marker.getMap()) {
                    self._setValue(JSON.stringify({
                        position: self.marker.getPosition(),
                        zoom: self.map.getZoom()
                    }));
                }
            });

            this.marker.addListener('click', function() {
                if (self.mode === 'edit') {
                    self.marker.setMap(null);
                    self._setValue(false);
                }
            });

            this.marker.addListener('dragend', function() {
                self._setValue(JSON.stringify({
                    position: self.marker.getPosition(),
                    zoom: self.map.getZoom()
                }));
            });
        },

        update_map: function(value) {
            if (value && value.position) {
                var position = value.position;
                this.marker.setPosition(position);
                this.map.setCenter(position);
                this.map.setZoom(value.zoom || 14);
                this.marker.setMap(this.map);
            }
        },

        _render: function() {
            if (this.value ) {
                var value = JSON.parse(this.value);
                this.update_map(value);
            }
        }
    });

    field_registry.add('googlemap', FieldGoogleMap);

    return {
        FieldGoogleMap: FieldGoogleMap,
    };
});
