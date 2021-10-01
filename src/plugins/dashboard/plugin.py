"""
Read and decode energy data from SENEC Home V3 Hybrid appliances.
"""
import os
import schedule
import time
import logging

import plugin_collection

log = logging.getLogger("Dashboard")

class Dashboard(plugin_collection.Plugin):
    
    def __init__(self):
        super().__init__()
        self.title = "Solar Dashboard"
        self.description = "Overview over SENEC and go-E"
        self.pluginPackage = type(self).__module__.split('.')[1]
        self.type = "sink"
        self.has_runtime = True
        self.current_data = {}
        self.settings = {}
        self.automaticChargingEnabled = False
        self.enoughPowerCounter = 0
        self.automaticChargingPowerAvailable = False

    def add_webserver(self, webserver):
        self.webserver = webserver

    def apply_settings(self, settings):
        if(type(self).__name__ in settings):
            log.info("Found custom config. Applying...")
            self.settings = settings[type(self).__name__]

    def runtime(self, other_plugins):
        # This is run permanently in the background
        while True:
            # Get data from (energy) producers and consumers
            senec = other_plugins.get_plugin("SenecHomeV3Hybrid")
            goe = other_plugins.get_plugin("GoEcharger")

            self.current_data = {
                "house": senec.get_data(),
                "wallbox1": goe.get_data(0),
                "wallbox2": goe.get_data(1),
                "automaticCharging": self.automaticChargingEnabled
            }

            # Calculate if charging should be allowed:
            # If spare energy is > 3500W for 30s then allow charging
            # Where spare energy is: PV production - house consumption + currently charging
            if(self.automaticChargingEnabled):
                self.__automaticChargingExcessPower(goe, 3500, 30)
            
            time.sleep(1)

    def __automaticChargingExcessPower(self, goe, watts, seconds):
        weHaveExcessPower = self.__weHaveExcessPowerFor(watts)
        if(weHaveExcessPower and self.enoughPowerCounter < seconds):
            self.enoughPowerCounter += 1
            if(self.enoughPowerCounter == seconds):
                log.info(f"We have enough power to charge for {seconds} seconds. Activating wallbox!")
                self.automaticChargingPowerAvailable = True
                goe.set_charging(device_no=1,on_off=1)
        elif(not weHaveExcessPower and self.enoughPowerCounter > 0):
            self.enoughPowerCounter -= 1
            if(self.enoughPowerCounter == 0):
                log.info(f"Not enough power to charge for {seconds} seconds. Deactivating wallbox!")
                self.automaticChargingPowerAvailable = False
                goe.set_charging(device_no=1,on_off=0)

    def __weHaveExcessPowerFor(self, watts):
        try:
            excessPower = self.current_data["house"]["live_data"]["pv_production"] \
                        - self.current_data["house"]["live_data"]["house_power"] \
                        + self.current_data["wallbox1"]["charging"]["current_power"] \
                        + self.current_data["wallbox2"]["charging"]["current_power"]
            log.info(f"Excess power: {round(excessPower, 2)} W")
            return excessPower >= watts
        except KeyError:
            return False


    def endpoint(self, req, resp):
        viewmodel = self.__create_view_model(req)
        if (self.__get_output_format(req) == "json"):
            res = self.current_data
            resp.media = res
            return
        if (self.__process_req_params(req)):
            resp.media = {"message": "Params set successfully."}
            return
        resp.html = self.webserver.render_template("dashboard/index.html", viewmodel)

    def __create_view_model(self, req):
        # Path: plugin_path + /
        return {
            "pluginPackage": self.pluginPackage,
            "name": type(self).__name__,
            "structure": self.__get_web_dict()
        }

    def __process_req_params(self, req):
        try:
            if(int(req.params['setAutomaticCharging']) == 1):
                log.info("Automatic charging enabled!")
                self.automaticChargingEnabled = True
            elif(int(req.params['setAutomaticCharging']) == 0):
                log.info("Automatic charging disabled!")
                self.automaticChargingEnabled = False
            return True
        except KeyError:
            return False

    def __get_output_format(self, req):
        try:
            output_format = req.params['format']
        except KeyError:
            output_format = "html"
        return output_format

    def __get_web_dict(self):
        return {
            "groups": [
                {
                    "title": "Production and Storage",
                    "blocks": [
                        {
                            "id": "pvProduction",
                            "title": "Production",
                            "type": "square",
                            "icons": [
                                {"name": "sun", "size": 48, "fill": "currentColor"}
                            ]
                        },
                        {
                            "id": "gridPower",
                            "title": "Grid Power",
                            "type": "square",
                            "icons": [
                                {"name": "lightning", "size": 48, "fill": "currentColor"}
                            ]
                        },
                        {
                            "id": "batteryPower",
                            "title": "Battery Power",
                            "type": "square_wide",
                            "icons": [
                                {"name": "battery-full", "size": 48, "fill": "currentColor"}
                            ]
                        }
                    ]
                },
                {
                    "title": "Consumers",
                    "blocks": [
                        {
                            "id": "housePower",
                            "title": "House",
                            "type": "square_wide",
                            "icons": [
                                {"name": "house", "size": 48, "fill": "currentColor"}
                            ]
                        },
                        {
                            "id": "wallbox1",
                            "switch_id": "wallbox1_switch",
                            "title": "Wallbox Parkplatz",
                            "type": "square_onoff",
                            "icons": [
                                {"name": "plug", "size": 48, "fill": "currentColor"}
                            ]
                        },
                        {
                            "id": "wallbox2",
                            "switch_id": "wallbox2_switch",
                            "title": "Wallbox Garage",
                            "type": "square_onoff",
                            "icons": [
                                {"name": "plug", "size": 48, "fill": "currentColor"}
                            ]
                        }
                    ]
                },
                {
                    "title": "Automatic Charging",
                    "blocks": [
                        {
                            "id": "automaticCharging",
                            "switch_id": "automaticCharging_switch",
                            "title": "Sun Charging (Garage)",
                            "type": "square_onoff",
                            "icons": [
                                {"name": "sun", "size": 48, "fill": "currentColor"}
                            ]
                        }
                    ]
                }
            ]
        }