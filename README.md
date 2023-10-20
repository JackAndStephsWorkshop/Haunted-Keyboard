# haunted-keyboard
# Have spooky conversations with ethereal AI through this magical keyboard.

![IMG_1320](https://github.com/JackAndStephsWorkshop/haunted-keyboard/assets/131804912/6dd85e7a-a3f0-4030-a411-394bf739c23c)

This custom PCB keyboard is powered by a Raspberry Pi Pico W and connects to any computer via USB. The Pi Pico W connects to WiFi in order to send keyboard input to ChatGPT, which returns a spooky response that gets typed out wherever your cursor is.

Find out more on the project's [Hackaday.io page](https://hackaday.io/project/192798-haunted-keyboard).

Find this section in the code.py file and replace with your SSID and password. 
wifi.radio.connect('SSID', 'Password')

Also create an environmental variable file called settings.toml with your Open AI key listed as Open_AI_Key="Bearer your key here"
