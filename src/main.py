import time
from machine import Pin, Timer, I2C
from ssd1306 import SSD1306_I2C
from max6675 import MAX6675
from picozero import Button
from PID import PID #https://github.com/gastmaier/micropython-simple-pid/blob/master/simple_pid/PID.pysa
from microdot_asyncio import Microdot, Response, send_file
from microdot_asyncio_websocket import with_websocket
import uasyncio as asyncio

#https://stackoverflow.com/questions/74758745/how-to-run-python-microdot-web-api-module-app-run-that-is-already-an-asyncio
# boot.py -- run on boot-up
import network

# Replace the following with your WIFI Credentials
SSID = "cdv"
SSI_PASSWORD = "060609143"

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
    
print("Connecting to your wifi...")
#https://www.donskytech.com/using-websocket-in-micropython-a-practical-example/
#https://stackoverflow.com/questions/74758745/how-to-run-python-microdot-web-api-module-app-run-that-is-already-an-asyncio
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
        sample_period, mypid, mypin, oled

    def calc_pulse(self, temp):
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
            self.last_read = now
            temp=await get_temp()
            self.calc_pulse(temp)    
            self.oled.update(self.mypid.setpoint, self.mypid._last_input, self.output)
            #print("input",pid._last_input,  "output % ", round(pid._last_output/100,2)*100, "ssr state ", self.PWMOutput, "pinstate ", self.high, "pulsewidth",self.pulsewidth)
            
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
        
#show that we're on
led = machine.Pin("LED", machine.Pin.OUT)
led.high()

sample_period=1000 # how often to run PID output calculation
windowStartTime = time.ticks_ms()
shutdownTime = windowStartTime + 10 * 60 * 1000 # turn off after 10 minutes
global mypid
mypid = PID(1.7, 0.05, 0.05, setpoint=0, scale='ms')
mypid.output_limits = (0, 100)


oled = oled_ctl(14, 15)

#ssr output pin
mypin = machine.Pin(2, Pin.OUT)

myssr = ssrCtrl(sample_period, mypid, mypin, oled)


steamButton = Button(9)
shotButton = Button(10)

steam_temp = 137
global gshot_temp
gshot_temp = 0
mypid.web=False
async def set_setpoint(v):
    global shot_temp
#    print(v)
    mypid.web = True
    #mypid.setpoint=v
#    print(mypid.setpoint)
    gshot_temp = v
    asyncio.sleep_ms(1)
#    print(shot_temp)

do_connect()

app = Microdot()
Response.default_content_type = 'text/html'

@app.route('/')
async def index(request):
    asyncio.sleep_ms(1)
    return send_file('index.html')



@app.route('/echo')
@with_websocket
async def echo(request, ws):
    while True:
        #await print("foofofofo")
        asyncio.sleep_ms(1)
        data = await ws.receive()
        print(data)
#        await set_setpoint(int(data))
#        data = await get_temp()
        targetr = "Set Temp {targetr:.1f}"
        targetr = targetr.format(targetr = int(data))
        shot_temp = int(data)
        asyncio.sleep_ms(1)
        await ws.send(targetr)

        
async def start_web_server():
    print("Were")
    await app.start_server(port=5000, debug=True)
    #await sycio.sleep_ms(1)
async def run_ssr():
    global shot_temp
    shot_temp = 102

    while(True): #todo move ssr pulse to each outcome here and encapsulate mypid and create reset method

        if(shotButton.is_pressed and steamButton.is_pressed):
            await print("dee dee")
            mypid.reset()
            mypid.setpoint = steam_temp

        elif(steamButton.is_pressed or shotButton.is_pressed):
            mypid.reset()
            mypid.setpoint = shot_temp

        elif(mypin.value()==1):        
            mypin.low()
            mypid.setpoint = 0
            mypid.reset()
            mypid.automode = False
            myssr.reset()
            
        if(time.ticks_ms() > shutdownTime):
            mypin.low()
            break
        
        elif(mypid._last_input is not None and mypid._last_input > 155): #exit if 104c or 220f reached
            mypin.low()
            break
        
        await myssr.pulse()
        await asyncio.sleep_ms(1)

aloop = asyncio.get_event_loop()
#async def main():
#     asyncio.create_task(run_ssr())
#     asyncio.create_task(run_app())
#     await asyncio.sleep_ms(100000)
    
    
#     task1 = aloop.create_task(run_ssr())
#     task2 = aloop.create_task(start_web_server())
    # Iterate over the tasks and wait for them to complete one by one
    #for task in asyncio.as_completed([task1, task2]):
    #    await task
task1 = aloop.create_task(run_ssr())
task2 = aloop.create_task(start_web_server())
aloop.run_forever()
