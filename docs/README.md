**Installation**
1. Install Micropython on your pico w
2. Install the picozero [library](https://github.com/RaspberryPiFoundation/picozero) using thonny
3. Install the [ssd1306](https://github.com/stlehmann/micropython-ssd1306/blob/master/ssd1306.py) library w/thonny
4. Install [uasyncio](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/TUTORIAL.md) with thonny's package manager
5. Install async [microdot](https://github.com/miguelgrinberg/microdot), and it's websocket helper library by copying the files from github
6. Add contents of lib from this project to the pico's lib directory (max6675.py, PID.py, hx711io.py and secrets.py)
7. Edit secrets.py accordingly for your network
8. copy main.py to your pico w
9. determine your scale factor for the loadcell and edit line 28 of main.py

| Max6675      | GND | VCC  | SCK    | CS     | SO     |
| ------------ | --- | ---- | ------ | ------ | ------ |
| MCU PIN Name | GND | 3.3v | GPIO18 | GPIO17 | GPIO16 |
| MCU PIN #    | 23  | 36   | 24     | 22     | 21     |


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
