import time
from machine import Pin, Timer, I2C
from ssd1306 import SSD1306_I2C
from max6675 import MAX6675
from picozero import Button

so = Pin(16, Pin.IN)
sck = Pin(18, Pin.OUT)
cs = Pin(17, Pin.OUT)
 
max = MAX6675(sck, cs , so)
def get_temp():
    data= max.read()
    return data

class PID: #https://github.com/jowood4/PID_controller/blob/master/single_PID/single_PID.ino
    def __init__(self, Input, Output, Setpoint, Kp, Ki, Kd, samp_per):

        self.Input = Input
        self.lastInput = Input
        self.Setpoint = Setpoint
        self.machine_min = 0
        self.machine_max = 100
        
        self.Output = Output
        self.outputSum = Output
        
        self.SampleTime = samp_per
        
        if(Kp<0 or Ki<0 or Kd<0):
               return
    
        self.dispKp = Kp
        self.dispKi = Ki
        self.dispKd = Kd

        self.SampleTimeInSec = self.SampleTime/1000
        self.kp = Kp
        self.ki = Ki * self.SampleTimeInSec
        self.kd = Kd / self.SampleTimeInSec
        
        self.lastTime = time.ticks_ms() - self.SampleTime
        
    def setOutputLimits(self, min,max):
            if(self.Output > self.machine_max):
                self.Output = self.machine_max
            elif(self.Output < self.machine_min):
                self.Output = self.machine_min
                
    def compute(self):
        now = time.ticks_ms()
        timeChange = time.ticks_diff(now, self.lastTime)
        
        if(timeChange >= self.SampleTime):#update nothing if not enough time elapse
            #Compute all the working error variables
            error = self.Setpoint - self.Input
            dInput = (self.Input - self.lastInput)
            self.outputSum += (self.ki * error);

            if(self.outputSum > self.machine_max):
                self.outputSum = self.machine_max
            elif(self.outputSum < self.machine_min):
                self.outputSum = self.machine_min;

            output = self.kp * error
            output += self.outputSum - self.kd * dInput;

            if(output > self.machine_max):
                output = self.machine_max
            elif(output < self.machine_min):
                output = self.machine_min
                
            self.Output = output

            #/*Remember some variables for next time*/
            self.lastInput = self.Input
            self.lastTime = now
            return True
        else:
           return False

class ssrCtrl:
    def __init__(self, WindowSize, windowStartTime):
        self.state = 0
        self.time_delta = 0
        self.min_delta = 20
        self.WindowSize = WindowSize
        self.windowStartTime = windowStartTime
        self.pulsewidth = 20
        self.maxpulsespersec = WindowSize / self.pulsewidth #for sample period, how often can we
        self.high = False
        self.start = True
        self.last_read=0
        
    def pulse(self, pid, ssr_pin):
        #https://github.com/shmick/Espresso-PID-Controller/blob/master/Espresso-PID-Controller.ino
        now = time.ticks_ms()

        pid.Input = get_temp()
        pid.compute()
        
        
        if(self.WindowSize < now - self.windowStartTime):
            self.windowStartTime += self.WindowSize

        #// Calculate the number of milliseconds that have passed in the current PWM cycle.
        #// If that is less than the Output value, the relay is turned ON
        #// If that is greater than (or equal to) the Output value, the relay is turned OFF.
        self.PWMOutput = pid.Output * (self.WindowSize / 100.00)
        self.deltat = now - self.windowStartTime
        if((self.PWMOutput > 100) and (self.PWMOutput > (now - self.windowStartTime))):
            self.high=True
            ssr_pin.high()
        else:
            self.high=False
            ssr_pin.low()
            
    def pulse2(self, pid, ssr_pin):
        #https://github.com/shmick/Espresso-PID-Controller/blob/master/Espresso-PID-Controller.ino
        now = time.ticks_ms()
        if(self.last_read==0 or now - self.last_read > self.WindowSize):
            self.last_read = now
            ssr_pin.low()
            pid.Input = get_temp()
            pid.compute()
            self.target_pulse = self.maxpulsespersec * pid.Output / 100 +0.1 # number of pulses to fire on out of possible in sample period
        
            self.fire_every_pulses = self.maxpulsespersec / self.target_pulse
            self.fire_every_ms = self.pulsewidth * self.fire_every_pulses
            self.PWMOutput = self.fire_every_ms
        
        if(self.start and self.target_pulse >= 1):
            self.start=False
            self.start_fire = time.ticks_ms()
            self.end_fire = time.ticks_ms() + self.pulsewidth
            self.next_fire = self.start_fire + self.fire_every_ms
            self.high=True
            ssr_pin.high()
            
        elif(not self.start and self.target_pulse >= 1):
            if(now > self.end_fire):
                self.high=False
                ssr_pin.low()
            if((now > self.next_fire) and not self.high):
                self.start_fire = time.ticks_ms()
                self.end_fire = time.ticks_ms() + self.pulsewidth
                self.next_fire = self.start_fire + self.fire_every_ms
                self.high=True
                ssr_pin.high()

    def pulse3(self, pid, ssr_pin, oled=False):
        now = time.ticks_ms()

        if(self.last_read==0 or now - self.last_read > self.WindowSize):        #new measurement and target pulse
            self.last_read = now
            ssr_pin.low()
            pid.Input = get_temp()
            pid.compute()
            self.target_pulse = self.maxpulsespersec * pid.Output / 100 +0.1 # number of pulses to fire on out of possible in sample period
        
            self.fire_every_pulses = self.maxpulsespersec / self.target_pulse
            self.fire_every_ms = self.pulsewidth * self.fire_every_pulses
            self.PWMOutput = self.fire_every_ms
            self.start=True
            if(oled):
                oled.fill(0)
                
                if(pid.Setpoint == 0):
                    target = "SLEEPING"
                else:
                    target = "Set Temp {target:.1f}"
                    target = target.format(target = pid.Setpoint*1.8+32)                
                cur = "Mes Temp {cur:.1f}"
                cur = cur.format(cur = pid.Input*1.8+32)
                duty = "Power Out {duty:.1f}%"
                duty = duty.format(duty = pid.Output)
                
                oled.text("VALENTINO Caffe", 0, 0)
                oled.text(target, 0, 16)
                oled.text(cur, 0, 32)
                oled.text(duty, 0, 48)
                oled.show()

            print("input",pid.Input,  "output % ", round(pid.Output/100,2)*100, "ssr state ", self.PWMOutput, "pinstate ", self.high, "pulsewidth",self.pulsewidth)
            
        if(self.target_pulse >= 1):
            if(self.start):
                #first fire
                self.start_fire = time.ticks_ms()
                self.end_fire = self.start_fire + self.pulsewidth
                self.next_fire = self.start_fire + self.fire_every_ms
                ssr_pin.high()
                self.high = True
                self.start=False
                #print("hee")

            if(now > self.end_fire ):#and self.high):
                #end pulse          
                ssr_pin.low()
                self.high = False
            
            if(now > self.next_fire and not self.high):
                #new pulse now set it up
                self.start_fire = time.ticks_ms()
                self.end_fire = self.start_fire + self.pulsewidth
                self.next_fire = self.end_fire + self.fire_every_ms
                ssr_pin.high()
                self.high = True
                
            #else:
            #    return


sample_period=1000
target_temperature=100
windowStartTime = time.ticks_ms()
shutdownTime = windowStartTime + 10 * 60 * 1000 # turn off after 10 minutes
mypid = PID(10,0,target_temperature,1.7,.05,2.5, sample_period)
myssr = ssrCtrl(sample_period, windowStartTime)
led = machine.Pin("LED", machine.Pin.OUT)
led.high()
mypin = machine.Pin(2, Pin.OUT)
ct=0

i2c=I2C(1,sda=Pin(14), scl=Pin(15), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

steamButton = Button(9)
shotButton = Button(10)

while(True):
    if(shotButton.is_pressed and steamButton.is_pressed):
        mypid.Setpoint = 137
    elif(steamButton.is_pressed or shotButton.is_pressed):
        if(mypid.Setpoint > 100):
            mypid.outputSum = 0
        mypid.Setpoint = 102

    else:
        mypid.Setpoint = 0
        mypid.outputSum = 0
    if(time.ticks_ms() > shutdownTime):
        mypin.low()
        break
    elif(mypid.Input > 155): #exit if 104c or 220f reached
        mypin.low()
        break
    myssr.pulse3(mypid, mypin, oled)



# DONE drill and tap
# DONE design mount
# DONE add watchdog
# DONE screen integration current temp, target
# DONE 7 degree offset
# add web interface for temp and steam or brew
# DONE button functions




