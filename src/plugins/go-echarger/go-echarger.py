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
        self.settings = { # defaults
            "plugin_path": "/go-echarger",
            "device_ip": "10.0.0.47"
        }
        self.wallbox = goEapi(self.settings['device_ip'])

    def add_webserver(self, webserver):
        self.webserver = webserver

    def apply_settings(self, settings):
        if(type(self).__name__ in settings):
            log.info("Found custom config. Applying...")
            self.settings = settings[type(self).__name__]
            log.debug(f"Settings: {self.settings}")

    def endpoint(self, req, resp):
        # Path: plugin_path + /
        template_vars = {
            "pluginPackage": self.pluginPackage
        }
        template_vars['name'] = type(self).__name__
        if (self.__get_output_format(req) == "json"):
            resp.media = self.wallbox.get_status()
            return
        change_value = self.__get_change_value(req)
        if (change_value):
            res = self.wallbox.change_value(change_value)
            resp.media = res
            return
        resp.html = self.webserver.render_template("go-echarger/index.html", template_vars)

    def __get_change_value(self, req):
        try:
            return req.params['set']
        except KeyError:
            return

    def __send_change(self, change):
        return requests.get(f"http://{self.settings['device_ip']}{self.settings['device_api_write_path']}{change}").json()

    def __get_output_format(self, req):
        try:
            output_format = req.params['format']
        except KeyError:
            output_format = "html"
        return output_format

class goEapi():

    def __init__(self, device_ip):
        self.device_ip = device_ip
        self.read_api  = f"http://{device_ip}/status"
        self.write_api = f"http://{device_ip}/mqtt?payload="
        self.data = {}

    def __send_change(self, key, val):
        try:
            res = requests.get(f"{self.write_api}{key}={val}", timeout=1.5).json()
        except requests.Timeout:
            return {"error": "Timeout while accessing wallbox."}
        except requests.ConnectionError:
            return {"error": "Connection error while accessing wallbox."}
        self.updateData(res)
        return {"msg": "success!"}

    def change_value(self, param):
        key, val = param.split('=')
        if(key == "allow_charging"):
            return self.__send_change("alw", val)
        if(key == "max_ampere"):
            if(int(val) not in range(6,32+1)):
                return {"error": "max_ampere must be in range 6-32"}
            else:
                return self.__send_change("amp", val)

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
        self.data = {
            "device_serial" : status['sse'],
            "fw_version"    : status['fwv'],
            "charging"      : {
                "allow_charging" : int(status['alw']), # 0/1
                "status"        : charging_status_cases.get(status['car'], "Invalid charge status"),
                "max_ampere"    : int(status['amp']), # 6-32
                "current_power" : int(status['nrg'][11]),
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
            }
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