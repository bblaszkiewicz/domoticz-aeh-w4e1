# Plugin Hisense AС (AEH-W4A1)
#
# Author: X-Th-Unicorn
#
"""
<plugin key="aehw4a1" name="Hisense AС (AEH-W4A1)" author="x-th-unicorn" version="1.0.0">
    <description>
        <h2>Hisense AС (AEH-W4A1)</h2><br/>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>On/Off</li>
            <li>HVAC Mode: Cool, Heat, Fan, Dry</li>
            <li>Fan speed: Mute, Low, Medium, High, Auto</li>
            <li>Swing: Off, Vertical, Horizontal, Both</li>
            <li>Set temp of (C) from 16 to 32</li>
            <li>Presets: Normal, ECO, Boost, Sleep 1, Sleep 2, Sleep 3, Sleep 4</li>
            <li>Display: On/Off</li>
        </ul>
        <h3>Confirmed working on the following AC's</h3>
        <ul style="list-style-type:square">
            <li>Ballu BSAGI-09HN1-17Y-01</li>
        </ul>
        <p>This plugin is based on https://github.com/bannhead/pyaehw4a1</p>
        <p>Using "asyncio" caused plugin system to fall, had to be rewritten</p>
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="10.10.0.106"/>
        <param field="Mode1" label="Update interval (sec):" width="75px">
            <options>
                <option label="30" value="3" />
                <option label="60" value="6" default="true" />
                <option label="90" value="9" />
                <option label="120" value="12" />
            </options>
        </param>
        <param field="Mode2" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
from dz_aehw4a1.aehw4a1 import Domoticz_AehW4a1
from dz_aehw4a1.commands import UpdateCommand
from dz_aehw4a1.commands import ReadCommand
from dz_aehw4a1.exceptions import *

MIN_TEMP_C = 16
MAX_TEMP_C = 32

MIN_TEMP_F = 61
MAX_TEMP_F = 90

HVAC_MODE_HEAT = 10
HVAC_MODE_COOL = 20
HVAC_MODE_DRY = 30
HVAC_MODE_FAN_ONLY = 40

FAN_AUTO_HEAT = 10
FAN_AUTO = 20
FAN_MUTE = 30
FAN_LOW = 40
FAN_MEDIUM = 50
FAN_HIGH = 60

SWING_OFF = 0
SWING_VERTICAL = 10
SWING_HORIZONTAL = 20
SWING_BOTH = 30

PRESET_NORMAL = 10
PRESET_ECO = 20
PRESET_BOOST = 30
PRESET_SLEEP_1 = 40
PRESET_SLEEP_2 = 50
PRESET_SLEEP_3 = 60
PRESET_SLEEP_4 = 70

AC_STATE = {
    "0001": HVAC_MODE_HEAT,
    "0010": HVAC_MODE_COOL,
    "0011": HVAC_MODE_DRY,
    "0000": HVAC_MODE_FAN_ONLY,
}

AC_FAN_MODES = {
    "00000000": FAN_AUTO_HEAT,
    "00000001": FAN_AUTO,
    "00000010": FAN_MUTE,
    "00000100": FAN_LOW,
    "00000110": FAN_MEDIUM,
    "00001000": FAN_HIGH,
}

AC_SWING_MODES = {
    "00": SWING_OFF,
    "10": SWING_VERTICAL,
    "01": SWING_HORIZONTAL,
    "11": SWING_BOTH,
}

AC_MODES_COMMAND = {
    HVAC_MODE_HEAT: "mode_heat",
    HVAC_MODE_COOL: "mode_cool",
    HVAC_MODE_DRY: "mode_dry",
    HVAC_MODE_FAN_ONLY: "mode_fan",
}

AC_FAN_MODES_COMMAND = {
    FAN_MUTE: "speed_mute",
    FAN_LOW: "speed_low",
    FAN_MEDIUM: "speed_med",
    FAN_HIGH: "speed_max",
    FAN_AUTO: "speed_auto",
}

class BasePlugin:
    enabled = True

    hvac_device = None
    command_output = None
    power_on = 0
    temperature_unit = 0
    current_indoor_temperature = 0
    current_outdoor_temperature = 0
    target_temperature = 0
    hvac_mode = 20
    fan_mode = 10
    swing_mode = 0
    preset_mode = 10
    previous_state = 10
    display_on = 0

    run_counter = 0

    def __init__(self):
        return

    def onStart(self):
        Domoticz.Debug("onStart called")

        self.hvac_device = Domoticz_AehW4a1(Parameters["Address"])

        if Parameters["Mode2"] == "Debug":
            Domoticz.Debugging(1)

        if (len(Devices) == 0):
            Domoticz.Device(Name="Power", Unit=1, Image=9, TypeName="Switch", Used=1).Create()
            Domoticz.Device(Name="Temp IN", Unit=2, TypeName="Temperature", Used=1).Create()
            Domoticz.Device(Name="Temp OUT", Unit=3, TypeName="Temperature",Used=1).Create()
            Domoticz.Device(Name="Temp TARGET", Unit=4, Type=242, Subtype=1, Image=16, Used=1).Create()

            Options = {"LevelActions" : "||||",
                       "LevelNames" : "|Heat|Cool|Dry|Fan",
                       "LevelOffHidden" : "true",
                       "SelectorStyle" : "1"}

            Domoticz.Device(Name="Mode", Unit=5, TypeName="Selector Switch", Image=16, Options=Options, Used=1).Create()

            Options = {"LevelActions" : "||||||",
                       "LevelNames" : "|AutoHeat|Auto|Mute|Low|Medium|High",
                       "LevelOffHidden" : "true",
                       "SelectorStyle" : "1"}

            Domoticz.Device(Name="Fan Rate", Unit=6, TypeName="Selector Switch", Image=7, Options=Options, Used=1).Create()

            Options = {"LevelActions" : "|||",
                       "LevelNames" : "Off|Vertical|Horizontal|Both",
                       "LevelOffHidden" : "false",
                       "SelectorStyle" : "1"}

            Domoticz.Device(Name="Swing", Unit=7, TypeName="Selector Switch", Image=7, Options=Options, Used=1).Create()

            Options = {"LevelActions" : "|||||||",
                       "LevelNames" : "|Normal|Eco|Boost|Sleep1|Sleep2|Sleep3|Sleep4",
                       "LevelOffHidden" : "true",
                       "SelectorStyle" : "1"}

            Domoticz.Device(Name="Preset", Unit=8, TypeName="Selector Switch", Image=9, Options=Options, Used=1).Create()

            Domoticz.Device(Name="Display", Unit=9, Image=9, TypeName="Switch", Used=1).Create()

            Domoticz.Debug("Device created.")

        DumpConfigToLog()

        Domoticz.Heartbeat(10)

        self.DataUpdate()

    def onStop(self):
        Domoticz.Debug("onStop called")
        return True

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("Command received U="+str(Unit)+" C="+str(Command)+" L= "+str(Level)+" H= "+str(Hue))

        try:
            self.hvac_device.check()
        except:
            Domoticz.Error("AC ("+ Parameters["Address"] + ") unavailable")
            return


        if (Unit == 1):
            if(Command == "On"):
                self.power_on = 1
                Devices[1].Update(nValue = 1, sValue ="100")
                self.hvac_device.command("on")
            else:
                self.power_on = 0
                Devices[1].Update(nValue = 0, sValue ="0")
                self.hvac_device.command("off")

            Devices[4].Update(nValue = self.power_on, sValue = Devices[4].sValue)
            Devices[5].Update(nValue = self.power_on, sValue = Devices[5].sValue)
            Devices[6].Update(nValue = self.power_on, sValue = Devices[6].sValue)
            Devices[7].Update(nValue = self.power_on, sValue = Devices[7].sValue)
            Devices[8].Update(nValue = self.power_on, sValue = Devices[8].sValue)

            Devices[9].Update(nValue = self.display_on, sValue = str(self.display_on*100))

        if (Unit == 4):
            if Level > MAX_TEMP_C:
                Level = MAX_TEMP_C
            elif Level < MIN_TEMP_C:
                Level = MIN_TEMP_C

            self.hvac_device.command("temp_"+str(int(Level))+"_C")
            Devices[4].Update(nValue = self.power_on, sValue = str(Level))

        if (Unit == 5):
            Devices[5].Update(nValue = self.power_on, sValue = str(Level))
            self.hvac_device.command(AC_MODES_COMMAND[Level])

        if (Unit == 6):
            if self.hvac_mode in (HVAC_MODE_COOL, HVAC_MODE_FAN_ONLY) and (
                self.hvac_mode != HVAC_MODE_FAN_ONLY or Level != FAN_AUTO
            ):
                self.hvac_device.command(AC_FAN_MODES_COMMAND[Level])
                Devices[6].Update(nValue = self.power_on, sValue = str(Level))

        if (Unit == 7):
            if Level == SWING_OFF and self.swing_mode != SWING_OFF:
                if self.swing_mode in (SWING_HORIZONTAL, SWING_BOTH):
                    self.hvac_device.command("hor_dir")
                if self.swing_mode in (SWING_VERTICAL, SWING_BOTH):
                    self.hvac_device.command("vert_dir")

            if Level == SWING_BOTH and self.swing_mode != SWING_BOTH:
                if self.swing_mode in (SWING_OFF, SWING_HORIZONTAL):
                    self.hvac_device.command("vert_swing")
                if self.swing_mode in (SWING_OFF, SWING_VERTICAL):
                    self.hvac_device.command("hor_swing")

            if Level == SWING_VERTICAL and self.swing_mode != SWING_VERTICAL:
                if self.swing_mode in (SWING_OFF, SWING_HORIZONTAL):
                    self.hvac_device.command("vert_swing")
                if self.swing_mode in (SWING_BOTH, SWING_HORIZONTAL):
                    self.hvac_device.command("hor_dir")

            if Level == SWING_HORIZONTAL and self.swing_mode != SWING_HORIZONTAL:
                if self.swing_mode in (SWING_BOTH, SWING_VERTICAL):
                    self.hvac_device.command("vert_dir")
                if self.swing_mode in (SWING_OFF, SWING_VERTICAL):
                    self.hvac_device.command("hor_swing")

            Devices[7].Update(nValue = self.power_on, sValue = str(Level))

        if (Unit == 8):
            if Level == PRESET_ECO:
                self.hvac_device.command("energysave_on")
                self.previous_state = Level
            elif Level == PRESET_BOOST:
                self.hvac_device.command("turbo_on")
                self.previous_state = Level
            elif Level == PRESET_SLEEP_1:
                self.hvac_device.command("sleep_1")
                self.previous_state = self.hvac_mode
            elif Level == PRESET_SLEEP_2:
                self.hvac_device.command("sleep_2")
                self.previous_state = self.hvac_mode
            elif Level == PRESET_SLEEP_3:
                self.hvac_device.command("sleep_3")
                self.previous_state = self.hvac_mode
            elif Level == PRESET_SLEEP_4:
                self.hvac_device.command("sleep_4")
                self.previous_state = self.hvac_mode
            elif Level == PRESET_NORMAL:
                if self.previous_state == PRESET_ECO:
                    self.hvac_device.command("energysave_off")
                elif self.previous_state == PRESET_BOOST:
                    self.hvac_device.command("turbo_off")
                elif self.previous_state in (PRESET_SLEEP_1, PRESET_SLEEP_2, PRESET_SLEEP_3,  PRESET_SLEEP_4):
                    self.hvac_device.command("sleep_off")
                elif self.previous_state in AC_STATE:
                    self.hvac_device.command(AC_STATE[self.previous_state])
                self.previous_state = PRESET_NORMAL

            Devices[8].Update(nValue = self.power_on, sValue = str(Level))

        if (Unit == 9):
            if(Command == "On"):
                self.display_on = 1
                Devices[9].Update(nValue = 1, sValue ="100")
                self.hvac_device.command("display_on")
            else:
                self.display_on = 0
                Devices[9].Update(nValue = 0, sValue ="0")
                self.hvac_device.command("display_off")

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        self.run_counter = self.run_counter - 1
        if self.run_counter <= 0:
            Domoticz.Debug("Poll unit")
            self.run_counter = int(Parameters["Mode1"])
            self.DataUpdate()
        else:
            Domoticz.Debug("Polling unit in " + str(self.run_counter) + " heartbeats.")

    def DataUpdate(self):
        try:
            self.command_output = self.hvac_device.command("status_102_0")
            self.power_on = int(self.command_output["run_status"],2)
            self.current_indoor_temperature = int(self.command_output["indoor_temperature_status"],2)
            self.current_outdoor_temperature = int(self.command_output["outdoor_temperature"],2)
            self.target_temperature = int(self.command_output["indoor_temperature_setting"],2)
            self.hvac_mode = AC_STATE[self.command_output["mode_status"]]
            self.fan_mode = AC_FAN_MODES[self.command_output["wind_status"]]
            self.swing_mode = AC_SWING_MODES[self.command_output["up_down"]+self.command_output["left_right"]]
            self.display_on = int(self.command_output["back_led"],2)

            if self.hvac_mode in (HVAC_MODE_COOL, HVAC_MODE_HEAT):
                self.target_temperature = int(self.command_output["indoor_temperature_setting"], 2)
            else:
                self.target_temperature = 0

            if self.command_output["efficient"] == "1":
                self.preset_mode = PRESET_BOOST
            elif self.command_output["low_electricity"] == "1":
                self.preset_mode = PRESET_ECO
            elif self.command_output["sleep_status"] == "0000001":
                self.preset_mode = PRESET_SLEEP_1
            elif self.command_output["sleep_status"] == "0000010":
                self.preset_mode = PRESET_SLEEP_2
            elif self.command_output["sleep_status"] == "0000011":
                self.preset_mode = PRESET_SLEEP_3
            elif self.command_output["sleep_status"] == "0000100":
                self.preset_mode = PRESET_SLEEP_4
            else:
                self.preset_mode = PRESET_NORMAL

            Devices[1].Update(nValue = self.power_on, sValue = str(self.power_on*100))
            Devices[2].Update(nValue = self.power_on, sValue = str(self.current_indoor_temperature))
            Devices[3].Update(nValue = self.power_on, sValue = str(self.current_outdoor_temperature))
            Devices[4].Update(nValue = self.power_on, sValue = str(self.target_temperature))

            Devices[5].Update(nValue = self.power_on, sValue = str(self.hvac_mode))
            Devices[6].Update(nValue = self.power_on, sValue = str(self.fan_mode))
            Devices[7].Update(nValue = self.power_on, sValue = str(self.swing_mode))
            Devices[8].Update(nValue = self.power_on, sValue = str(self.preset_mode))
            Devices[9].Update(nValue = self.display_on, sValue = str(self.display_on*100))

        except:
            Domoticz.Error("AC ("+ Parameters["Address"] + ") unavailable")

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
