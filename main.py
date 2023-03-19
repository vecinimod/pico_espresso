import time
from json import dumps as jdump
from machine import Pin, Timer, I2C
from ssd1306 import SSD1306_I2C
from max6675 import MAX6675
from picozero import Button
from PID import PID #https://github.com/gastmaier/micropython-simple-pid/blob/master/simple_pid/PID.py
from microdot_asyncio import Microdot, Response, send_file
from microdot_asyncio_websocket import with_websocket
import uasyncio as asyncio
from random import randint

#https://stackoverflow.com/questions/74758745/how-to-run-python-microdot-web-api-module-app-run-that-is-already-an-asyncio

import network
from secrets import secrets
   
from hx711_pio import HX711
pin_OUT = Pin(6, Pin.IN, pull=Pin.PULL_UP)
pin_SCK = Pin(5, Pin.OUT)

hx711 = HX711(pin_SCK, pin_OUT)
#scale = 300
hx711.tare(3)
hx711.set_time_constant(.95)

def callhx2():
    value = hx711.get_value()/741.263
    return(value)

class flowmeter:
    def __init__(self, pinin=3):
        self.pin_IN = Pin(pinin, Pin.IN, pull=Pin.PULL_DOWN )
        self.last_time=0
        self.count= 0
        self.flow=0
        self.pin_IN.irq(trigger=self.pin_IN.IRQ_RISING, handler=self.update_flow)


    def update_flow(self,pin):
        self.count +=1
        
    def compute_flow(self):
        if(self.last_time==0):
            self.last_time=time.ticks_ms()
            self.last_count=self.count
            flow = 0
        else:
            this_time = time.ticks_ms()
            dt = time.ticks_diff(this_time, self.last_time)
            dct = self.count - self.last_count
            mlx1000 = 5195 * dct #1000ths of ml i.e. microliters
            flow = (mlx1000 / 1000) / (dt/1000)
            self.last_time = this_time
            self.last_count = self.count
        self.flow = flow

myflow=flowmeter()

# pin_IN = Pin(3, Pin.IN, Pin.PULL_DOWN )
# def update_flow(pinn):
#     print("floooow")
# pin_IN.irq(trigger=pin_IN.IRQ_RISING, handler=update_flow)

# Replace the following with your WIFI Credentials
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

so = Pin(16, Pin.IN)
sck = Pin(18, Pin.OUT)
cs = Pin(17, Pin.OUT)
 
max = MAX6675(sck, cs , so)
async def get_temp():
    data= max.read()
    return data

class oled_ctl:
    def __init__(self,sda, scl):
        i2c=I2C(1,sda=Pin(sda), scl=Pin(scl), freq=400000)
        self.oled = SSD1306_I2C(128, 64, i2c)
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

class ssrCtrl:
    def __init__(self, WindowSize, mypid, mypin, oled):
        self.WindowSize = WindowSize
        self.pulsewidth = 20
        self.maxpulsespersec = WindowSize / self.pulsewidth #for sample period, how often can we
        self.high = False
        self.last_read = 0
        self.end_fire = 0
        self.mypid = mypid
        self.mypin = mypin
        self.oled=oled
        self.weight = 0
        

    def calc_pulse(self, temp):
        if(self.mypid.setpoint - temp > 5):
            self.output=100
        elif(temp - self.mypid.setpoint > 5):
            self.output = 0
        else:
            self.output = self.mypid(temp)
            
        print("input", temp, "setpoint", self.mypid.setpoint, "output", self.output)
        
        if(self.output is None):
            self.target_pulse = 0.1 #
        else:
            self.target_pulse = self.maxpulsespersec * self.output / 100 + 0.1 # number of pulses to fire on out of possible in sample period
        if(self.target_pulse > self.maxpulsespersec):
            self.target_pulse = self.maxpulsespersec
        self.fire_every_pulses = self.maxpulsespersec / self.target_pulse
        self.fire_every_ms = self.pulsewidth * self.fire_every_pulses
            
    async def pulse(self):
        now = time.ticks_ms()

        if(self.last_read==0 or now - self.last_read > self.WindowSize):        #new measurement and target pulse
            self.mypin.low()
            self.last_read = now
            temp=await get_temp()
            self.calc_pulse(temp)    
            self.oled.update(self.mypid.setpoint, await get_temp(), self.output)
            
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
        if(self.target_pulse>0):
            self.target_pulse = 0
            self.output = 0
            self.last_read = 0 

#define app
#https://www.donskytech.com/using-websocket-in-micropython-a-practical-example/
#https://stackoverflow.com/questions/74758745/how-to-run-python-microdot-web-api-module-app-run-that-is-already-an-asyncio
app = Microdot()
Response.default_content_type = 'text/html'

@app.route('/')
async def index(request):
    asyncio.sleep_ms(1)
    print("index request")
    return send_file('index2.html')

@app.route('/echo')
@with_websocket
async def echo(request, ws):
    while True:
        asyncio.sleep_ms(1)
        data = await ws.receive()
        print(data)
        target = "Set Temp {target:.1f}"
        my_espresso.set_shot_temp(int(data))
        target = target.format(target = my_espresso.user_shot_temp)
        asyncio.sleep_ms(1)
        await ws.send(target)
        
@app.route('/mode')
@with_websocket
async def echo(request, ws):
    while True:
        asyncio.sleep_ms(100)
        data = await ws.receive()
        print(data)
        asyncio.sleep_ms(1)
        hx711.tare(3)
        if(my_espresso.mode == "shot"): #check machine mode has to be in shot mode
            my_espresso.ui_mode_change_request()
        else:
            print("Error gui asked for shot mode when not physically in shot mode, turn dial")
        
@app.route('/data')
@with_websocket
async def data(request, ws):    
    while True:
        await asyncio.sleep_ms(my_espresso.sample_period)
        temp = await get_temp()
        weight = callhx2()
        data_str = jdump({"time":my_espresso.mode_elapsed_time/1000,"temperature":temp,
                          "output":my_espresso.myssr.output, "setpoint":my_espresso.mypid.setpoint,
                          "weight":weight, "mode":my_espresso.mode,"mode_change":my_espresso.flag_ui_mode_change,
                          "pump_output":my_espresso.mypump.output,
                          "flow":myflow.flow})
        my_espresso.flag_ui_mode_change = False
        await ws.send(data_str)

        
class pump:
    def __init__(self, profile, psm):
        self.profile = profile
        self.stage = 0
        self.time_start_stage=0
        self.psm = psm
        self.output=0
        
        #extend the profile to create control over time endpoints
        cumultime = 0
        for k in sorted(self.profile.keys()):
            self.profile[k]["start"] = cumultime 
            self.profile[k]["end"] = cumultime + self.profile[k]["duration"]
            cumultime = self.profile[k]["end"]
        print(self.profile)
            
    def update_shot_pump_output(self, time_ms, mass):
        _output = -1
        time_s = time_ms / 1000
        if(self.stage == 0):
            self.time_start_stage = time_s
            self.stage=1
            
        if(mass<0):
            mass = 0
            
        if(self.stage<=len(self.profile)):            
            if(time_s - self.time_start_stage > self.profile[self.stage]["duration"] or self.profile[self.stage]["max_mass"] < mass):
                self.stage += 1
                self.time_start_stage = time_s
            if(self.stage<=len(self.profile)):         
                self.output = (time_s - self.time_start_stage) / self.profile[self.stage]["duration"] * (self.profile[self.stage]["pump_end"] - self.profile[self.stage]["pump_start"]) + self.profile[self.stage]["pump_start"]
        else:
            self.output = 0

    def run_pump(self, start_time, current_time, mass_update_intvl=50):
        timenow = time.ticks_diff(current_time, start_time)
        if(timenow<100):
            self.mass=0
        if(timenow%mass_update_intvl==0):
            self.mass = callhx2()
        self.update_shot_pump_output(timenow, self.mass)
        self.psm.set_output(self.output)
        if(self.stage<=len(self.profile) and timenow%1000==0):
            myflow.compute_flow()
            print("time", timenow/1000,"stage",self.profile[self.stage]["name"],
                  "output", self.output, "mass", self.mass, "flowct", myflow.count,
                  "flow", myflow.flow)
        else:
            return
    def reset(self):
        self.psm.set_output(0)
        self.stage=0
        
    def test_output(self):
        startt=time.ticks_ms()
        timeno = 0
        mass=0
        
        while(True):
            timeno = time.ticks_diff(time.ticks_ms(),startt)
            self.update_shot_pump_output(timeno, mass)
            self.psm.set_output(self.output)
            if(timeno % 1000 == 0):
                mass = callhx2()
                if(self.stage<=len(self.profile)):
                    print("time", timeno/1000,"stage",self.profile[self.stage]["name"], "output", "shoto", self.output, "selfo", self.output, "mass", mass)
                else:
                    return

class psm:
    def __init__(self, psm_pin=12, zc_pin=13):
        self.psm_pin = Pin(psm_pin, Pin.OUT)
        self.zc_pin = Pin(13, Pin.IN, pull=Pin.PULL_DOWN)
        self.zc_pin.irq(trigger=self.zc_pin.IRQ_RISING, handler=self.pulse)
        self.high=False
        self.output=0
        self.start_time= time.ticks_ms()
        self.last_fire = self.start_time
        self.count=0
        self.mypid = PID(40, 0.05, 0.05, setpoint=10, scale='ms',
                         output_limits=[0, 100], proportional_on_measurement=False)

    def set_output(self, req_output):
        if(req_output > 100):
            req_output = 100
        elif(req_output < 0):
            req_output = 0
            
        self.output = req_output
            
    def pulse(self, pin):
        if(self.output<=1):
            self.psm_pin.low()
        elif(self.output==100):
            self.psm_pin.high()
        elif(self.count%(100-self.output)<=10):
            self.psm_pin.high()
        else:
            self.psm_pin.low()
        self.count+=1

    
    def sim(self):
        oo = 0
        startt=time.ticks_ms()
        timeno = 0
        input=0
        while(True):
            timeno = time.ticks_diff(time.ticks_ms(),startt)
            input = timeno/100000 *.2 * oo - randint(0,100)/50
            if(input<0):
                input = 0
            if(input>10):
                input=10
            if(timeno % 1000 == 0):
                oo = self.mypid(input)
                print("time", timeno, "input",input, "output", oo, "seto", self.output)
                self.set_output(oo)
            
        
# a class to manage the loop, run both control + sensor and app tasks
class espresso:
    def __init__(self, oled, profile, sample_period=1000, ssr_pin=2, steam_btn_pin=9, shot_btn_pin=10):

        self.default_shot_temp = 10
        self.user_shot_temp = 0
        self.default_steam_temp = 137
        self.user_steam_temp = 0

        self.sample_period = sample_period
        
        self.steamButton = Button(steam_btn_pin)
        self.shotButton = Button(shot_btn_pin)
        
        self.mypin = machine.Pin(ssr_pin, Pin.OUT)
        self.oled = oled
        
        self.pump_profile = profile
        
        self.last_mode = None
        self.mode = None
        self.mode_change = False
        self.flag_ui_mode_change = False
        self.ui_mode_change_requested = False
        
        self.loop = asyncio.get_event_loop()
        self.start_time = time.ticks_ms()
        
    def call__async_main(self):
        task1 = self.loop.create_task(self.run_machine(self.loop))
        task2 = self.loop.create_task(self.start_web_server())
        self.loop.run_forever()

    def set_shot_temp(self, temp):
        self.user_shot_temp = temp
        
    async def start_web_server(self):
        do_connect()
        await app.start_server(port=5000, debug=True)
        
    def ui_mode_change_request(self):
        self.ui_mode_change_requested = True
        
    def sense_mode(self):
        if(self.shotButton.is_pressed and self.steamButton.is_pressed):
            mode = "steam"
        elif(self.shotButton.is_pressed or self.steamButton.is_pressed):
            mode = "shot"
        elif(not self.shotButton.is_pressed and not self.steamButton.is_pressed):
            mode = "sleep"
        else:
            mode = "sleep"
        
        if(self.last_mode is not None and mode != self.last_mode) or self.ui_mode_change_requested:
            self.mode_change=True
            if(self.last_mode!="shot"):#enable that we can save the graph from getting reset at 0
                self.mode_start_time = time.ticks_ms()
        else:
            self.mode_change = False
            
        self.last_mode = mode
        self.mode = mode

    def run_mode(self):
        if(self.mode_change):
            self.flag_ui_mode_change = True
            self.ui_mode_change_requested = False
            self.mypump.reset()
            if(self.mode=="steam"):
                self.mypid.reset()
                if(self.user_steam_temp>0):
                    self.mypid.setpoint = self.user_steam_temp
                else:
                    self.mypid.setpoint = self.default_steam_temp
            
            elif(self.mode=="shot"):
                self.mypid.reset()
                if(self.user_shot_temp>0):
                    self.mypid.setpoint = self.user_shot_temp
                else:
                    self.mypid.setpoint = self.default_shot_temp
                
            elif(self.mode=="sleep"):
                self.mypin.low()
                self.mypid.setpoint = 0
                self.mypid.reset()
                self.mypid.automode = False
                self.myssr.reset()
                
        self.mode_elapsed_time = time.ticks_diff(time.ticks_ms(),self.mode_start_time)


    async def run_machine(self, parent_loop):        
        self.mypid = PID(1.7, 0.05, 0.05, setpoint=0, scale='ms')
        self.mypid.output_limits = (0, 100)
        
        self.myssr = ssrCtrl(self.sample_period, self.mypid, self.mypin, self.oled)
        
        self.mypsm = psm(12,13)
        self.mypump = pump(self.pump_profile, self.mypsm)
        self.mode_start_time = time.ticks_ms()

        while(True):
            self.current_time = time.ticks_ms()
            self.elapsed_time = time.ticks_diff(self.start_time, self.current_time)
            self.sense_mode()
            self.run_mode()
            
            if(self.mode=="shot"):
                self.mypump.run_pump(self.mode_start_time, time.ticks_ms(), 1000)
            
            if(time.ticks_ms() > shutdownTime):
                await self.mypin.low()
                parent_loop.stop()
                break
            
            elif(self.mypid._last_input is not None and self.mypid._last_input > 155): #exit if 104c or 220f reached
                await  self.mypin.low()
                parent_loop.stop()
                break
            
            #mypsm.pulse()
            await self.myssr.pulse()
            await asyncio.sleep_ms(1)

#show that we're on
led = machine.Pin("LED", machine.Pin.OUT)
led.high()

sample_period=1000 # how often to run PID output calculation
windowStartTime = time.ticks_ms()
shutdownTime = windowStartTime + 20 * 60 * 1000 # turn off after 10 minutes

#setup oled
myoled = oled_ctl(14, 15)

#setup pump

profile = {
    1: {"name":"pre-infusion","duration":10, "pump_start":25, "pump_end":75, "max_mass":1},
    2: {"name":"wait","duration":25, "pump_start":0, "pump_end":0, "max_mass":100},
    3: {"name":"ramp","duration":4, "pump_start":30, "pump_end":65, "max_mass":100},
    4: {"name":"pour","duration":60, "pump_start":65, "pump_end":95, "max_mass":45}
            }

#mypump=pump(profile, mypsm)
#mypump.test_output()

#mypsm.set_output(85)
my_espresso = espresso(myoled, profile) #TODO add pump to espresso as argument
my_espresso.call__async_main()
