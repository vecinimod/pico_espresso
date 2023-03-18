# pico espresso - $25 wifi enabled universal espresso machine PID mod
A simple Raspberry Pi Pico W based espresso machine controller with support for:
+ Web interface with no addtional server (runs on mcu) using websockets for real time data
+ Shot graph generation in web ui and automatic shot timer
+ PID temperature control of boiler with duty cycled SSR
+ digital pump control profiles using PSM and robotdyn dimmer 
+ integrated shot scale with auto tareing and data recording in web app 
+ OLED display for current temperature, setpoint and SSR duty cycle
+ 1kg load cell compatible [scale case design and dimmer case](./scale/)

Can be installed on any espresso machine for temperature control but currently installed on a Calphalon temp iq

USE AT YOUR OWN RISK

Future support for:
+ flow meter (comes installed on temp iq)

<img width="525" alt="image" src="https://user-images.githubusercontent.com/7244561/224531848-6d100060-4e1f-419d-9af9-2c0689ea6759.png">

<img width="765" alt="image" src="https://user-images.githubusercontent.com/7244561/224582345-2e28960f-3b12-4f8a-a3c9-76c68b5b7ca1.png">

<img width="484" alt="image" src="https://user-images.githubusercontent.com/7244561/224907716-6cad9fbb-22c7-4549-ba82-bac22ce69091.png">

<img width="716" alt="image" src="https://user-images.githubusercontent.com/7244561/226081132-0829dc62-02af-465b-8f18-45fab9d41ccb.png">


BOM ($35 to $67 depending on basic (ssr + pico + max6675 + tap) to complete (Add oled, load cell and dimmer)
+ [OLED](https://www.amazon.com/gp/product/B072Q2X2LL/ref=ppx_yo_dt_b_asin_title_o00_s01?ie=UTF8&psc=1) $7
+ [SSR](https://www.amazon.com/gp/product/B08GPB7N2T/ref=ppx_yo_dt_b_asin_title_o01_s00?ie=UTF8&psc=1) $11
+ [pico w](https://www.microcenter.com/product/650108/raspberry-pi-pico-w) $6
+ [max6675](https://www.amazon.com/gp/product/B01HT871SO/ref=ppx_yo_dt_b_asin_title_o01_s00?ie=UTF8&psc=1) $7.69
+ [m6x1.0 tap and bit for thermocouple mounting on thermoblock using stock M4 hole location](https://www.amazon.com/uxcell-Spiral-Titanium-Machine-Threading/dp/B09TYS683J/ref=sr_1_4?keywords=m6+x+1+tap+and+bit&qid=1678515435&sr=8-4) $9
+ [hx711 and 1kg load cell](https://www.amazon.com/gp/product/B08KRV8VYP/ref=ppx_yo_dt_b_asin_title_o07_s03?ie=UTF8&psc=1) $8
+ [robodyne zc triac dimmer](https://www.amazon.com/gp/product/B071X19VL1/ref=ppx_yo_dt_b_asin_title_o03_s00?ie=UTF8&psc=1) $15
