# Installation of software on pico w
1. Install Micropython on your pico w
2. Install the following using thonny's package manager:
    1. [picozero](https://github.com/RaspberryPiFoundation/picozero)
    2. [ssd1306](https://github.com/stlehmann/micropython-ssd1306/blob/master/ssd1306.py)
    3. [uasyncio](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/TUTORIAL.md)
3. Install [microdot](https://github.com/miguelgrinberg/microdot), and it's websocket, async, and async websocket helper libraries by copying the files from github in the src folder of project that correspond to these (4 files total for microdot)
4. Add contents of lib from this project to the pico's lib directory (max6675.py, PID.py, hx711_pio.py and secrets.py)
5. Edit secrets.py accordingly for your network
6. copy main.py to your pico w
7. determine your scale factor for the loadcell and edit line 28 of main.py

# Pinout guides for each peripheral

| Max6675      | GND | VCC  | SCK    | CS     | SO     |
| ------------ | --- | ---- | ------ | ------ | ------ |
| MCU PIN Name | GND | 3.3v | GPIO21 | GPIO20 | GPIO19 |
| MCU PIN #    | 23  | 36   | 27     | 25     | 24     |


| SSR          | +  | \- |
| ------------ | -- | -- |
| MCU PIN Name | GPIO2  | GND |
| MCU PIN #    | 4 | 3 |

| AB32 Flowmeter  | output | ground | 5V In |
| --------------- | ------ | ------ | ----- |
| Logic converter | HV2    |        |       |
| MCU PIN Name    |        | GND    | VSYS  |
| MCU PIN #       |        | 38     | 39    |

| Logic converter | HV   | ground | LV   | LV2   |
| --------------- | ---- | ------ | ---- | ----- |
| MCU PIN Name    | VSYS | GND    | 3.3v | GPIO3 |
| MCU PIN #       | 39   | 38     | 36   | 5     |

| HX711        | GND | DT    | SCK   | VCC  |
| ------------ | --- | ----- | ----- | ---- |
| MCU PIN Name | GND | GPIO6 | GPIO5 | 3.3v |
| MCU PIN #    | 8   | 9     | 7     | 36   |

| Robotdyn Dimmer | VCC  | GND | ZC     | PSM    | OUT              | N               | IN   |
| --------------- | ---- | --- | ------ | ------ | ---------------- | --------------- | ---- |
| Mains           |      |     |        |        |                  | neutral         | live |
| Pump            |      |     |        |        | large gauge wire | pump thin gauge |      |
| MCU PIN Name    | 3.3v | GND | GPIO13 | GPIO12 |                  |                 |      |
| MCU PIN #       | 36   | 18  | 17     | 16     |                  |                 |

| OLED         | GND | VCC  | SCL    | SDA    |
| ------------ | --- | ---- | ------ | ------ |
| MCU PIN Name | GND | 3.3v | GPIO15 | GPIO14 |
| MCU PIN #    | 18  | 36   | 20     | 19     |

| Steam Button | Wire 1 | Wire 2 |
| ------------ | ------ | ------ |
| MCU PIN Name | GPIO9  | GND    |
| MCU PIN #    | 12     | 13     |

| Shot button  | Wire 1 | Wire 2 |
| ------------ | ------ | ------ |
| MCU PIN Name | GPIO10 | GND    |
| MCU PIN #    | 14     | 13     |
