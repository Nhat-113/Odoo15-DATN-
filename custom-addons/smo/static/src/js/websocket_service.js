odoo.define('smo.websocket', function (require) {
    "use strict";

    const AbstractService = require('web.AbstractService')
    const core = require('web.core')
    const rpc = require('web.rpc')

    const WebSocketService = AbstractService.extend({
        dependencies: [],

        start: function () {
            this._super.apply(this, arguments)
            this._initializeService()
        },

        _initializeWebSocket: function (wss_url, devices, token) {
            const self = this
            const ws = new WebSocket(wss_url)

            ws.onopen = function () {
                console.log('Smo WebSocket connection opened')
                devices.forEach(device => {
                    const object = {
                        authCmd: {token: token},
                        cmds: [
                            {
                                entityType: "DEVICE",
                                entityId: device.device_id,
                                scope: "LATEST_TELEMETRY",
                                cmdId: device.id,
                                type: "TIMESERIES",
                            }
                        ]
                    }
                    
                    const data = JSON.stringify(object)
                    ws.send(data)
                })
            }

            ws.onmessage = function (message) {
                self._handleWebSocketMessage(message.data)
            }

            ws.onclose = function (close) {
                console.log('WebSocket connection closed. Attempting to reconnect...')
                if (close.code == 1007 && close.reason == 'JWT Token expired') {
                    return rpc.query({
                        route: '/smo/token/refresh',
                        params: {}
                    }).then(function (response) {
                        setTimeout(function () {
                            self._initializeService()
                        }, 5000)
                    })
                }

                setTimeout(function () {
                    self._initializeService()
                }, 5000)
            }

            ws.onerror = function (error) {
                console.error('WebSocket encountered an error: ', error)
            }
        },

        _initializeService: function () {
            const self = this
            rpc.query({
                route: '/smo/socket/init',
                params: {}
            }).then(function (response) {
                const init_data = response.data
                if (init_data.socket_active == true) {
                    self._initializeWebSocket(
                        init_data.wss_url,
                        init_data.devices,
                        init_data.token
                    )
                }
            }).catch(function (error) {
                console.error('Error get initial data from server: ', error)
            })
        },

        _handleWebSocketMessage: function (message) {
            console.log('Got WebSocket message: ', message)
            rpc.query({
                route: '/smo/socket/device/lc',
                params: {
                    message: message
                }
            }).then(function (result) {

            }).catch(function (error) {
                console.error('Error sending data to server:', error);
            })
        },
    })

    core.serviceRegistry.add('smo_websocket_service', WebSocketService)
    return WebSocketService
})
