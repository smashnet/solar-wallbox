"""
Read and write data of go-eCharger wallbox.
"""
import os
import logging
import requests

import plugin_collection

log = logging.getLogger("GoEcharger")

class GoEcharger(plugin_collection.Plugin):
    
    def __init__(self):
        super().__init__()
        self.title = "go-eCharger"
        self.description = "Read and write data of go-eCharger wallbox."
        self.pluginPackage = type(self).__module__.split('.')[1]
        self.type = "consumer"
        self.has_runtime = False
        self.devices = [] # Will be read from src/config/settings.json
        self.settings = {} # Will be read from src/config/settings.json

    def add_webserver(self, webserver):
        self.webserver = webserver

    def apply_settings(self, settings):
        if(type(self).__name__ in settings):
            log.info("Found custom config. Applying...")
            self.settings = settings[type(self).__name__]
            log.debug(f"Settings: {self.settings}")
            self.devices = [goeDevice(device['name'], device['ip']) for device in self.settings['devices']]

    def has_runtime(self):
        return self.has_runtime

    def endpoint(self, req, resp):
        viewmodel = self.__create_view_model(req)

        if (self.__get_output_format(req) == "json"):
            resp.media = self.devices[viewmodel['selected_device']].get_status()
            return
        change_value = self.__get_change_value(req)
        if (change_value):
            res = self.devices[viewmodel['selected_device']].change_value(change_value)
            resp.media = res
            return
        resp.html = self.webserver.render_template("go-echarger/index.html", viewmodel)

    def __create_view_model(self, req):
        # Path: plugin_path + /
        return {
            "pluginPackage": self.pluginPackage,
            "name": type(self).__name__,
            "structure": self.__get_web_dict(),
            "selected_device": self.__get_selected_device(req),
            "devices": [self.__add_to_dict(device, "no", i) for i, device in enumerate(self.settings['devices'])]
        }

    def __add_to_dict(self, d, k, v):
        d[k] = v
        return d

    def __get_change_value(self, req):
        try:
            return req.params['set']
        except KeyError:
            return

    def __get_output_format(self, req):
        try:
            output_format = req.params['format']
        except KeyError:
            output_format = "html"
        return output_format

    def __get_selected_device(self, req):
        try:
            device = int(req.params['device'])
        except KeyError:
            device = 0
        return device

    def __get_web_dict(self):
        '''
        {
            "title": "Test Chart",
            "type": "chartcard",
            "current_val_id": "testChartCard",
            "chart_id": "testChart",
            "icons": [
                {"name": "house", "size": 48, "fill": "currentColor"}
            ]
        },
        '''
        return {
            "groups": [
                {
                    "title": "Main Controls",
                    "blocks": [
                        {
                            "id": "allowChargingToggle",
                            "title": "Allow Charging",
                            "type": "square_switch",
                            "icons": [
                                {"name": "power", "size": 40, "fill": "currentColor"}
                            ]
                        },
                        {
                            "id": "maxAmpereSelect",
                            "title": "Max Ampere",
                            "type": "square_dropdown",
                            "options": [
                                {"value": 6, "text": "6 A"},
                                {"value": 8, "text": "8 A"},
                                {"value": 10, "text": "10 A"},
                                {"value": 12, "text": "12 A"},
                                {"value": 16, "text": "16 A"}
                            ],
                            "icons": []
                        }
                    ]
                },
                {
                    "title": "Charging",
                    "blocks": [
                        {
                            "id": "chargingStatus",
                            "title": "Status",
                            "type": "square",
                            "icons": []
                        },
                        {
                            "id": "chargingPower",
                            "title": "Power",
                            "type": "square",
                            "icons": []
                        },
                        {
                            "id": "usedPhases",
                            "title": "Used Phases",
                            "type": "square",
                            "icons": []
                        },
                        {
                            "id": "energyCharged",
                            "title": "Charged",
                            "type": "square",
                            "icons": []
                        },
                        {
                            "id": "totalEnergyCharged",
                            "title": "Charged Total",
                            "type": "square",
                            "icons": []
                        }
                    ]
                },
                {
                    "title": "Access Controls",
                    "blocks": [
                        {
                            "id": "unlockMethodSelect",
                            "title": "Unlock Method",
                            "type": "square_dropdown",
                            "options": [
                                {"value": 0, "text": "open"},
                                {"value": 1, "text": "RFID"},
                                {"value": 2, "text": "automatic"}
                            ],
                            "icons": [
                                {"name": "unlock", "size": 40, "fill": "currentColor"}
                            ]
                        },
                        {
                            "id": "unlockedByUser",
                            "title": "Current User",
                            "type": "square",
                            "icons": [
                                {"name": "person", "size": 40, "fill": "currentColor"}
                            ]
                        },
                        {
                            "id": "userEnergy",
                            "title": "Charged by User",
                            "type": "square",
                            "icons": [
                                {"name": "plug", "size": 40, "fill": "currentColor"}
                            ]
                        }
                    ]
                },
                {
                    "title": "General",
                    "blocks": [
                        {
                            "type": "infocard",
                            "title": "",
                            "icons": [
                                {"name": "plug", "size": 48, "fill": "currentColor"}
                            ],
                            "contents": [
                                {"name": "Serial Number", "id": "serialNumber"},
                                {"name": "Firmware", "id": "firmwareVersion"},
                                {"name": "IP Address", "id": "ipAddress"}
                            ]
                        }
                    ]
                }
            ]
        }

class goeDevice():

    def __init__(self, name, ip):
        self.name = name
        self.ip = ip
        self.read_api  = f"http://{self.ip}/status"
        self.write_api = f"http://{self.ip}/mqtt?payload="
        self.data = {}
        self.value_map = {
            "allow_charging": "alw",
            "max_ampere"    : "amp",
            "access_control": "ast",
            "button_level_1": "al1",
            "button_level_2": "al2",
            "button_level_3": "al3",
            "button_level_4": "al4",
            "button_level_5": "al5",
            "rfid_name_1"   : "rna",
            "rfid_name_2"   : "rnm",
            "rfid_name_3"   : "rne",
            "rfid_name_4"   : "rn4",
            "rfid_name_4"   : "rn5",
            "rfid_name_4"   : "rn6",
            "rfid_name_4"   : "rn7",
            "rfid_name_4"   : "rn8",
            "rfid_name_4"   : "rn9",
            "rfid_name_4"   : "rn1"
        }

    def __send_change(self, key, val):
        try:
            res = requests.get(f"{self.write_api}{key}={val}", timeout=1.5).json()
        except requests.Timeout:
            return {"error": "Timeout while accessing wallbox."}
        except requests.ConnectionError:
            return {"error": "Connection error while accessing wallbox."}
        self.updateData(res)
        return {
            "msg": "success!",
            key  : val
            }

    def change_value(self, param):
        key, val = param.split('=')
        try:
            key_name = self.value_map[key]
        except KeyError:
            log.warning(f"Key {key} not yet supported. Not changing anything!")
            return
        return self.__send_change(key_name, val)

    def get_status(self):
        try:
            res = requests.get(self.read_api, timeout=1.5).json()
        except requests.Timeout:
            return {"error": "Timeout while accessing wallbox."}
        except requests.ConnectionError:
            return {"error": "Connection error while accessing wallbox."}
        self.updateData(res)
        return self.data
    
    def updateData(self, status):
        # This is not the full set of available data available from the wallbox
        # For a complete documentation see https://github.com/goecharger/go-eCharger-API-v1
        charging_status_cases = {
            "1": "Charging station ready, no vehicle",
            "2": "Vehicle charging",
            "3": "Waiting for vehicle",
            "4": "Charge finished, vehicle still connected"
        }
        error_states = {
            "0": "No error",
            "1": "Residual Current Device",
            "3": "Phase disturbance",
            "8": "Earthing detection",
            "10": "Other"
        }
        self.data = {
            "device_serial" : status['sse'],
            "fw_version"    : status['fwv'],
            "device_ip"     : self.ip,
            "access_control": {
                "access_method"  : int(status['ast']),
                "allow_charging" : int(status['alw']), # 0/1
                "unlocked_by"    : int(status['uby']),
                "rfid_cards"     : {
                    1 : {
                        "id"     : status['rca'],
                        "name"   : status['rna'],
                        "energy" : int(status['eca']) # in 0.1 kWh
                    },
                    2 : {
                        "id"     : status['rcr'],
                        "name"   : status['rnm'],
                        "energy" : int(status['ecr']) # in 0.1 kWh
                    }
                }
            },
            "charging"      : {
                "status"        : charging_status_cases.get(status['car'], "Invalid charge status"),
                "max_ampere"    : int(status['amp']), # 6-32
                "current_power" : round(int(status['nrg'][11]) / 100.0, 3),
                "pha_available"  : self.__get_number_of_available_phases(int(status['pha'])),
                "pha_used"       : self.__get_number_of_used_phases(status['nrg']),
                "energy"        : self.__dws_to_kWh(int(status['dws']))
            },
            "energy_total"   : int(status['eto']), # in 0.1 kWh
            "button_levels"  : {
                    "level1": int(status['al1']),
                    "level2": int(status['al2']),
                    "level3": int(status['al3']),
                    "level4": int(status['al4']),
                    "level5": int(status['al5'])
            },
            "energy_values"  : {
                "L1_voltage": status['nrg'][0], # in Volts
                "L2_voltage": status['nrg'][1],
                "L3_voltage": status['nrg'][2],
                "N_voltage" : status['nrg'][3],
                "L1_ampere" : status['nrg'][4], # in 0.1 A
                "L2_ampere" : status['nrg'][5],
                "L3_ampere" : status['nrg'][6],
                "L1_power"  : status['nrg'][7], # in 0.1 kW
                "L2_power"  : status['nrg'][8],
                "L3_power"  : status['nrg'][9],
                "N_power"   : status['nrg'][10],
                "sum_power" : status['nrg'][11],
                "L1_powfac" : status['nrg'][12], # in %
                "L2_powfac" : status['nrg'][13],
                "L3_powfac" : status['nrg'][14],
                "N_powfac"  : status['nrg'][15]
            },
            "error_state"   : error_states.get(status['err'], "Invalid error state")
        }

    ''' Phases
        0b00ABCDEF
        A ... phase 3, in front of the contactor
        B ... phase 2 in front of the contactor
        C ... phase 1 in front of the contactor
        D ... phase 3 after the contactor
        E ... phase 2 after the contactor
        F ... phase 1 after the contactor
        
        pha | 0b00001000: Phase 1 is available
        pha | 0b00111000: Phase1-3 is available
        '''
    def __get_number_of_available_phases(self, pha):
        res = 0
        if pha & 0b00001000:
            res += 1
        if pha & 0b00010000:
            res += 1
        if pha & 0b00100000:
            res += 1
        return res
    
    def __get_number_of_used_phases(self, nrg):
        res = 0
        if nrg[7] > 5: # If power (in 0.1 kW) on L1 > 5
            res += 1
        if nrg[8] > 5: # If power (in 0.1 kW) on L2 > 5
            res += 1
        if nrg[9] > 5: # If power (in 0.1 kW) on L3 > 5
            res += 1
        return res

    def __dws_to_kWh(self, dws):
        return round((dws * 10.0 / 60.0 / 60.0 / 1000.0), 3)


'''
The following parameters can only be read:
version rbc rbt car err cbl pha tmp dws adi uby eto wst nrg fwv sse eca ecr
ecd ec4 ec5 ec6 ec7 ec8 ec9 ec1 rca rcr rcd rc4 rc5 rc6 rc7 rc8 rc9 rc1

The following parameters can be set:
amp ast alw stp dwo wss wke wen tof tds lbr aho afi ama al1 al2 al3 al4 al5
cid cch cfi lse ust wak r1x dto nmo rna rnm rne rn4 rn5 rn6 rn7 rn8 rn9 rn1
'''