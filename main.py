import time
from json import dumps as jdump
from machine import Pin, Timer, I2C, ADC
from ssd1306 import SSD1306_I2C
from max6675 import MAX6675
from picozero import Button
from PID import PID #https://github.com/gastmaier/micropython-simple-pid/blob/master/simple_pid/PID.py
from microdot_asyncio import Microdot, Response, send_file
from microdot_asyncio_websocket import with_websocket
import uasyncio as asyncio
from random import randint
import network
from secrets import secrets
from hx711_pio import HX711

#input device classes
class scale:
    def __init__(self, outpin=6, sckpin=5):
        pin_OUT = Pin(outpin, Pin.IN, pull=Pin.PULL_UP)
        pin_SCK = Pin(sckpin, Pin.OUT)

        self.hx711 = HX711(pin_SCK, pin_OUT)
        self.hx711.tare(11)
        self.hx711.set_time_constant(.99)

    def get_weight(self):
        value = self.hx711.get_value()/741.263
        return(value)
    
    def tare(self):
        self.hx711.tare(10)
            
class pressure:
    def __init__(self, adcpin=1):
        self.adc=ADC(1)
    
    def read(self):
        self.volts = self.adc.read_u16() * 3.3 / 65535 #volts
        self.psi = (self.volts - .344)/(3.094-.344)*200
        self.bar = self.psi / 14.5038

    def get_bar(self):
        self.read()
        return(self.bar)
    
class flowmeter:
    def __init__(self, pinin=3):
        self.pin_IN = Pin(pinin, Pin.IN, pull=Pin.PULL_DOWN )
        self.last_time=0
        self.count= 0
        self.flow=0
        self.pin_IN.irq(trigger=self.pin_IN.IRQ_RISING, handler=self.update_flow)


    def update_flow(self, pin):
        self.count +=1
        
    def get_flow(self):
        if(self.last_time==0):
            self.last_time=time.ticks_ms()
            self.last_count=self.count
            flow = 0
        else:
            this_time = time.ticks_ms()
            dt = time.ticks_diff(this_time, self.last_time)
            dct = self.count - self.last_count
            mlx1000 = .5195 * dct #1000ths of ml i.e. microliters
            flow = mlx1000 / (dt/1000)
            self.last_time = this_time
            self.last_count = self.count
        self.flow = flow
        return flow
 
class thermocouple:
    def __init__(self, sopin=19, sckpin=21, cspin=20):        
        so = Pin(sopin, Pin.IN)
        sck = Pin(sckpin, Pin.OUT)
        cs = Pin(cspin, Pin.OUT)
 
        self.max = MAX6675(sck, cs , so)
        
    def get_temp(self):
        data = self.max.read()
        return data

#output device classes
class oled:
    def __init(self, sda, scl, pwr):
        return
    
    def update(self, setpoint, input_, output):
        return

class oled_old:
    def __init__(self,sda, scl, pwr):
        i2c=I2C(1,sda=Pin(sda), scl=Pin(scl), freq=400000)
        self.oled = SSD1306_I2C(128, 64, i2c)
        self.pwr = Pin(pwr, Pin.OUT)
        self.pwr.high()
        
    def update(self, setpoint, input_, output):
        self.oled.fill(0)
            
        if(setpoint == 0):
            target = "SLEEPING"
        else:
            target = "Set Temp {target:.1f}"
            target = target.format(target = setpoint*1.8+32)                

        cur = "Mes Temp {cur:.1f}"
        if(input_ is None):
            cur = cur.format(cur = 0)
        else:
            cur = cur.format(cur = input_*1.8+32)
        
        duty = "Power Out {duty:.1f}%"                
        if(output is None):
            duty = duty.format(duty = 0)
        else:
            duty = duty.format(duty = output)                
            
        self.oled.text("VALENTINO Caffe", 0, 0)
        self.oled.text(target, 0, 16)
        self.oled.text(cur, 0, 32)
        self.oled.text(duty, 0, 48)
        self.oled.show()

class heater:
    def __init__(self, WindowSize, mypin=2):
        self.mypid = PID(1.7, 0.05, 0.05, setpoint=0, scale='ms')
        self.mypid.output_limits = (0, 100)
        
        self.WindowSize = WindowSize
        self.pulsewidth = 20
        self.maxpulsespersec = WindowSize / self.pulsewidth #for sample period, how often can we
        self.high = False
        self.last_read = 0
        self.end_fire = 0
        self.mypin = Pin(mypin, Pin.OUT)
        self.oled=oled
        self.weight = 0
        self.output = 0
        
    def set_temp(self, temp):
        self.mypid.setpoint = temp
        
    def calc_pulse(self, temp):
        if(self.mypid.setpoint - temp > 5):
            self.output=100
        elif(temp - self.mypid.setpoint > 5):
            self.output = 0
        else:
            self.output = self.mypid(temp)
            
        print("input", temp, "setpoint", self.mypid.setpoint, "output", self.output)
        
        if(self.output is None):
            self.target_pulse = 0.1 
        else:
            self.target_pulse = self.maxpulsespersec * self.output / 100 + 0.1 # number of pulses to fire on out of possible in sample period
        if(self.target_pulse > self.maxpulsespersec):
            self.target_pulse = self.maxpulsespersec
        self.fire_every_pulses = self.maxpulsespersec / self.target_pulse
        self.fire_every_ms = self.pulsewidth * self.fire_every_pulses
            
    def pulse(self, temp):
        now = time.ticks_ms()

        if(self.last_read==0 or now - self.last_read > self.WindowSize):        #new measurement and target pulse
            self.mypin.low()
            self.last_read = now
            self.calc_pulse(temp)    
            
        if(self.target_pulse >= 1 and self.output < 100): #calling for output

            if(now > self.end_fire ):
                #end pulse          
                self.mypin.low()
                self.high = False
            
            if self.end_fire==0 or (now > self.next_fire and not self.high):
                #new pulse now set it up
                self.start_fire = time.ticks_ms()
                self.end_fire = self.start_fire + self.pulsewidth
                self.next_fire = self.end_fire + self.fire_every_ms
                self.mypin.high()
                self.high = True
                
        elif(self.output==100):
            self.mypin.high()
    
    def reset(self):
        self.target_pulse = 0
        self.output = 0
        self.last_read = 0
        self.mypid.setpoint=0
        self.mypin.low()
        self.mypid.setpoint = 0
        self.mypid.reset()
        self.mypid.automode = False

class pump:
    def __init__(self, psm_pin=12, zc_pin=13):
        self.psm_pin = Pin(psm_pin, Pin.OUT)
        self.zc_pin = Pin(zc_pin, Pin.IN, pull=Pin.PULL_DOWN)
        self.zc_pin.irq(trigger=self.zc_pin.IRQ_RISING, handler=self.pulse)
        self.high=False
        self.output=0
        self.start_time= time.ticks_ms()
        self.last_fire = self.start_time
        self.count=0

    def set_output(self, req_output):
        if(req_output > 100):
            req_output = 100
        elif(req_output < 0):
            req_output = 0
            
        self.output = req_output

    def pulse(self, pin):
        if(self.output==100):
            self.psm_pin.high()
        else:
            if(self.count*100 % (10000//(100-self.output)) < 100): # ct * 100 % (100//((100-output)*100))
                self.psm_pin.low()
            else:
                self.psm_pin.high()
                
        if(self.count==100):
            self.count=1
        else:
            self.count+=1
            
    def reset(self):
        self.set_output(0)
        
class mode_profile:
    def __init__(self, profile):
        self.time_start_stage=0
        self.set_profile(profile)
        self.preheating=True
        self.done=False
        self.output={}
        self.stage_number = 0
        self.output["heater_setpoint"] = self.preheat["setpoint"]
        self.output["pump_setpoint"] = 0
    
    def set_profile(self, profile):
        self.stages = profile["stages"]
        self.preheat = profile["preheat"]
        cumultime = 0

        for k in sorted(self.stages.keys()):
            self.stages[k]["start"] = cumultime 
            self.stages[k]["end"] = cumultime + self.stages[k]["duration"]
            cumultime = self.stages[k]["end"]

        print("updated profile:", self.stages)
 
    def update_stage(self, cur_mass, cur_temp, cur_time):
        time_now = cur_time/1000
        if self.preheating and (self.preheat["exit_temp_range"][0] < cur_temp and self.preheat["exit_temp_range"][1] > cur_temp):
                self.preheating=False
                self.start_first_stage_time = time_now
                self.start_stage_time = time_now
                self.stage_number = 1
                self.current_stage = self.stages[self.stage_number]
                
        if(not self.preheating):   
            self.elapsed_stage_time = time_now - self.start_stage_time
            
            if (self.elapsed_stage_time > self.current_stage["duration"] or cur_mass > self.current_stage["max_mass"]):
                if(self.stage_number < len(self.stages)):
                    self.stage_number += 1                            
                    self.start_stage_time = time_now
                    self.current_stage = self.stages[self.stage_number]
                else:
                    self.done = True

            if(self.done):
                self.output["pump_setpoint"] = 0
                self.output["heater_setpoint"] = 0
            else:
                pump_setpoint = ((self.elapsed_stage_time) / self.current_stage["duration"]) * (self.current_stage["pump_end"] - self.current_stage["pump_start"]) + self.current_stage["pump_start"]
                self.output["pump_setpoint"] = pump_setpoint

            self.output["stage_time_elapsed"] = self.elapsed_stage_time
            self.output["total_time_elapsed"] = time_now - self.start_first_stage_time

#define app
#https://www.donskytech.com/using-websocket-in-micropython-a-practical-example/
#https://stackoverflow.com/questions/74758745/how-to-run-python-microdot-web-api-module-app-run-that-is-already-an-asyncio
app = Microdot()
Response.default_content_type = 'text/html'

@app.route('/')
async def index(request):
    asyncio.sleep_ms(1)
    print("index request")
    return send_file('index.html')

@app.route('/echo')
@with_websocket
async def echo(request, ws):
    while True:
        asyncio.sleep_ms(1)
        data = await ws.receive()
        print(data)
        target = "Set Temp {target:.1f}"
        #my_espresso.set_shot_temp(int(data))
        target = target.format(target = my_pico.myheater.mypid.setpoint)
        asyncio.sleep_ms(1)
        await ws.send(target)
        
# @app.route('/mode')
# @with_websocket
# async def echo(request, ws):
#     while True:
#         asyncio.sleep_ms(100)
#         data = await ws.receive()
#         print(data)
#         asyncio.sleep_ms(1)
#         hx711.tare(3)
#         if(my_espresso.mode == "shot"): #check machine mode has to be in shot mode
#             my_espresso.ui_mode_change_request()
#         else:
#             print("Error gui asked for shot mode when not physically in shot mode, turn dial")
        
@app.route('/data')
@with_websocket
async def data(request, ws):    
    while True:
        await asyncio.sleep_ms(my_pico.sample_period)
        pico_data = my_pico.serialize_data()
        my_pico.flag_ui_mode_change = False
        await ws.send(pico_data)

class pico_espresso:
    def __init__(self, shot_profile, steam_profile, sample_period=1000):

        self.sample_period = sample_period
        
        #watchdog flag
        self.flag_to_shutdown = False
        
        #start in sleep mode regardless of button status
        self.mode = "sleep"
        self.last_mode = "sleep"
        self.mode_change = False
        self.flag_ui_mode_change = False
        
        #store profile config
        self.shot_profile = shot_profile
        self.steam_profile = steam_profile
        self.active_profile = None
        
        #create all inputs
        self.myscale = scale()
        self.mypressure = pressure()
        self.myflowmeter = flowmeter()
        self.mythermocouple=thermocouple()
        
        #get first sensor readings
        self.update_sensors()
        
        #create all outputs
        self.myoled = oled(14, 15, 16)
        self.myheater = heater(WindowSize=sample_period, mypin=2)
        self.mypump = pump()
        
        #create switch callbacks to sense state
        self.steam_button=Button(9)
        self.shot_button=Button(10)
        
        #create a loop object
        self.loop = asyncio.get_event_loop()
        
    def update_sensors(self):
        self.cur_weight = self.myscale.get_weight()
        self.cur_pressure = self.mypressure.get_bar()
        self.cur_flow = self.myflowmeter.get_flow()
        self.cur_temp = self.mythermocouple.get_temp()
        
    def sense_mode(self):
        #self.desetup_buttons()
        if(self.shot_button.is_pressed and self.steam_button.is_pressed):
            mode = "steam"
        elif(self.shot_button.is_pressed or self.steam_button.is_pressed):
            mode = "shot" #TODO add preheat mode when only steam button is pressed
        elif(not self.shot_button.is_pressed and not self.steam_button.is_pressed):
            mode = "sleep"
        else:
            mode = "sleep"
        
        if(mode != self.mode):
            self.mode_change=True
        else:
            self.mode_change = False
            
        self.last_mode = self.mode
        self.mode = mode
        
        #self.setup_buttons()
        
    def sleep(self):
        self.myheater.reset()
        self.mypump.reset()
        
    def watchdogs(self):
        if(self.cur_temp > 170):
            self.sleep()
            print("CAUTION: TEMP OVER 170")
            return True
        else:
            return False
        #set pins low at certain time
    
    def serialize_data(self):
        #get time, if in active profile use start time, if not set to 0
        data_str = jdump({"time":self.mode_elapsed_time/1000,
                          "temperature":self.cur_temp,
                          "heater_output":self.myheater.output,
                          "heater_setpoint":self.myheater.mypid.setpoint,
                          "weight":self.cur_weight,
                          "mode":self.mode,
                          "mode_change":self.flag_ui_mode_change,
                          "pump_output":self.mypump.output,
                          "flow":self.cur_flow,
                          "pressure":self.cur_pressure})
        return data_str
    
    def run_hw(self, parent_loop):
        time_now = time.ticks_ms()
        last_time = 0
        self.mode_start_time = time_now
        while(not self.flag_to_shutdown):
            #update time
            time_now = time.ticks_ms()
            diff_time = time.ticks_diff(time_now, last_time)
            self.mode_elapsed_time = time.ticks_diff(time_now, self.mode_start_time)
            #update sensor readings and output to oled
            if(diff_time > self.sample_period):
                self.sense_mode()
                last_time = time_now
                self.update_sensors()

                #watchdog check condition
                self.flag_to_shutdown=self.watchdogs()

                #update oled
                
                #print sensor output
                print("temp", self.cur_temp, "flow", self.cur_flow, "pressure", self.cur_pressure, "weight", self.cur_weight)
                if(self.active_profile is not None and hasattr(self.active_profile, "current_stage")):
                    print("profile stage", self.active_profile.current_stage)
                    print("profile output", self.active_profile.output)
                    
            #based on self.mode (Set by switch callback) get and set profile stage, thermoblock setpoint, and pump output at update interval
            if(self.mode_change):
                if not (self.last_mode=="shot" and self.mode=="sleep"):                    
                    self.mode_start_time = time_now
                
                print("new mode", self.mode)
                self.myscale.tare()
                
                if(self.mode == "shot"):
                    self.active_profile = mode_profile(self.shot_profile)
                elif(self.mode == "steam"):
                    self.active_profile = mode_profile(self.steam_profile)
                else:
                    self.active_profile = None
                    self.sleep()

                self.flag_ui_mode_change = True
                self.mode_change = False
            
            #get updated profile stage output
            if(not self.mode=="sleep" and self.active_profile is not None):
                #update outputs 4 times per sensor sample period 
                if(diff_time > self.sample_period):
                    self.active_profile.update_stage(self.cur_weight, self.cur_temp, time_now)
                    self.myheater.set_temp(self.active_profile.output["heater_setpoint"])
                    self.mypump.set_output(self.active_profile.output["pump_setpoint"])

                #pulse heater, pulse pump based on zc trigger so no call here
                self.myheater.pulse(self.cur_temp)
     
            await asyncio.sleep_ms(1)

        #if exited loop set output to low just in case!
        self.sleep()
        
    def call__async_main(self):
        task1 = self.loop.create_task(self.run_hw(self.loop))
        task2 = self.loop.create_task(self.start_web_server())
        self.loop.run_forever()

    async def start_web_server(self):
        do_connect()
        await app.start_server(port=5000, debug=True)
        
default_shot_profile = {
    "preheat":{"setpoint":100, "exit_temp_range":[95, 105]},
    "stages":{
        1: {"name":"pre-infusion","duration":7, "pump_start":100, "pump_end":100, "max_mass":3},
        2: {"name":"wait","duration":25, "pump_start":0, "pump_end":0, "max_mass":100},
        3: {"name":"ramp","duration":4, "pump_start":35, "pump_end":75, "max_mass":100},
        4: {"name":"pour","duration":60, "pump_start":25, "pump_end":10, "max_mass":45}
    }
}

default_steam_profile = {
    "preheat":{"setpoint":150, "exit_temp_range":[125, 169]},
    "stages":{
    1: {"name":"preheat","duration":5, "pump_start":0, "pump_end":0, "max_mass":100},
    2: {"name":"steam","duration":250, "pump_start":2, "pump_end":2, "max_mass":100}
            }
}

secrets = secrets()
SSID = secrets.SSID
SSI_PASSWORD = secrets.SSI_PASSWORD

def do_connect():
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(SSID, SSI_PASSWORD)
        while not sta_if.isconnected():
            pass
    print('Connected! Network config:', sta_if.ifconfig())

#show that we're on
led = machine.Pin("LED", machine.Pin.OUT)
led.high()

my_pico = pico_espresso(default_shot_profile, default_steam_profile, 1000)
my_pico.call__async_main()
