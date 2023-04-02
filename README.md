# pico espresso - $25 wifi enabled universal espresso machine PID +++ mod
A simple Raspberry Pi Pico W based espresso machine controller with support for:
+ Web interface with no addtional server (runs on mcu) using websockets for real time data
+ Shot graph generation in web ui and automatic shot timer
+ PID temperature control of boiler with duty cycled SSR
+ digital pump control profiles using PSM and robotdyn dimmer 
+ integrated shot scale with auto tareing and data recording in web app 
+ OLED display for current temperature, setpoint and SSR duty cycle
+ 1kg load cell compatible [scale case design and dimmer case](./scale/)
+ [flow meter](https://kh-technic.dk/wp-content/uploads/2020/02/AB32.pdf) measurement, logging and visualization
+ pressure transducer for real time pressure data

Can be installed on any espresso machine for temperature control but currently installed on a Calphalon temp iq

USE AT YOUR OWN RISK

<img width="525" alt="image" src="https://user-images.githubusercontent.com/7244561/224531848-6d100060-4e1f-419d-9af9-2c0689ea6759.png">

![picoesp](https://user-images.githubusercontent.com/7244561/229332446-6adac624-b477-400c-b5f7-1a8227ca7b18.gif)

<img width="716" alt="image" src="https://user-images.githubusercontent.com/7244561/226081132-0829dc62-02af-465b-8f18-45fab9d41ccb.png">

<img width="424" alt="image" src="https://user-images.githubusercontent.com/7244561/229333048-39a75b4f-cb49-47a4-92df-e838826f6db2.png">


BOM ($25 to $100 depending on basic (ssr + pico + max6675) to complete (Add m6 tap, oled, load cell, dimmer, and transducer)
+ [OLED](https://www.amazon.com/gp/product/B072Q2X2LL/ref=ppx_yo_dt_b_asin_title_o00_s01?ie=UTF8&psc=1) $7
+ [SSR](https://www.amazon.com/gp/product/B08GPB7N2T/ref=ppx_yo_dt_b_asin_title_o01_s00?ie=UTF8&psc=1) $11
+ [pico w](https://www.microcenter.com/product/650108/raspberry-pi-pico-w) $6
+ [max6675](https://www.amazon.com/gp/product/B01HT871SO/ref=ppx_yo_dt_b_asin_title_o01_s00?ie=UTF8&psc=1) $7.69
+ [m6x1.0 tap and bit for thermocouple mounting on thermoblock using stock M4 hole location](https://www.amazon.com/uxcell-Spiral-Titanium-Machine-Threading/dp/B09TYS683J/ref=sr_1_4?keywords=m6+x+1+tap+and+bit&qid=1678515435&sr=8-4) $9
+ [hx711 and 1kg load cell](https://www.amazon.com/gp/product/B08KRV8VYP/ref=ppx_yo_dt_b_asin_title_o07_s03?ie=UTF8&psc=1) $8
+ [robodyne zc triac dimmer](https://www.amazon.com/gp/product/B071X19VL1/ref=ppx_yo_dt_b_asin_title_o03_s00?ie=UTF8&psc=1) $15
+ [200 psi pressure transducer 1/8 npt](https://www.amazon.com/s?k=200+psi+pressure+transducer) $15
+ [1/8 npt female tee](https://www.amazon.com/Winmien-Fitting-Female-Diameter-Forged) $6
+ [1/8 npt to 4mm ptc connectors](https://www.amazon.com/IVLPHA-Connect-Pneumatic-Straight-Connectors/dp/B0B92BM32D) $10
+ [1k ohm and 2.2k ohm resistors](https://www.amazon.com/MCIGICM-Values-Resistor-Assortment-Resistors/dp/B06WRQS97C) $0.02 ($6 for assorment of 600)

Other parts and tools most people attempting this should already have on hand or have similar:
+ jst connectors and crimper
+ spade connectors and crimper
+ xt connectors (for wiring harness connecting mains to ssr, thermoblock)
+ 24 gauge high temp silicone coated wire
+ wire stripper
+ multimeter (handy for chasing down faulty wires and connections)
+ oscilloscope (e.g. to check flowmeter and dimmer function)
+ soldering iron
+ heat shrink tubing
+ electrical tape
+ 3d printer (for scale and cases for pico and dimmer)
+ thermal paste for thermocouple
+ donor usb cables
+ 5W usb power supply
+ [pico w shield/breadboard](https://www.amazon.com/Treedix-Compatible-Raspberry-Breakout-Flexible/dp/B091F7YSCD)
