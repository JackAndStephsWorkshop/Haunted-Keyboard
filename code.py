import os
import time
import ssl
import wifi
import socketpool
import microcontroller
import adafruit_requests
import json 
import board
import keypad
import usb_hid

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

#Keyboard code

km = keypad.KeyMatrix(
    row_pins=(board.GP15, board.GP12, board.GP13, board.GP14),
    column_pins=(board.GP16, board.GP17, board.GP18, board.GP19, board.GP20, board.GP21, board.GP22, board.GP11, board.GP10, board.GP9, board.GP8, board.GP7),
	columns_to_anodes=True,
)
# Get the HID device for the keyboard.
keyboard_device = None
consumer_control_device = None
for device in usb_hid.devices:
    if device.usage_page == 0x01 and device.usage == 0x06:  # Keyboard
        keyboard_device = device
    elif device.usage_page == 0x0C and device.usage == 0x01:  # Consumer Control
        consumer_control_device = device

# Ensure the devices are found.
if not keyboard_device or not consumer_control_device:
    raise RuntimeError("Required HID devices not found")

# Initialize the HID devices.
kbd = Keyboard(keyboard_device)         # Use keyboard_device here
cc = ConsumerControl(consumer_control_device)  # Use consumer_control_device here

KEYMAP = [
    [Keycode.ESCAPE, Keycode.Q, Keycode.W, Keycode.E, Keycode.R, Keycode.T, Keycode.Y, Keycode.U, Keycode.I, Keycode.O, Keycode.P, Keycode.BACKSPACE],
    [Keycode.TAB, Keycode.A, Keycode.S, Keycode.D, Keycode.F, Keycode.G, Keycode.H, Keycode.J, Keycode.K, Keycode.L, Keycode.SEMICOLON, Keycode.ENTER],
    [Keycode.SHIFT, Keycode.Z, Keycode.X, Keycode.C, Keycode.V, Keycode.B, Keycode.N, Keycode.M, Keycode.COMMA, Keycode.PERIOD, Keycode.UP_ARROW, Keycode.SHIFT],
    [Keycode.CONTROL, Keycode.GUI, Keycode.ALT, Keycode.SPACE, None, Keycode.SPACE, None, Keycode.GUI, Keycode.FORWARD_SLASH, Keycode.LEFT_ARROW, Keycode.DOWN_ARROW, Keycode.RIGHT_ARROW]
]

def keycode_to_char(keycode):
    """Converts a keycode to a character."""
    mapping = {
        Keycode.ESCAPE: '[ESC]',  # or just '' if you don't want to record escape presses
        Keycode.Q: 'q',
        Keycode.W: 'w',
        Keycode.E: 'e',
        Keycode.R: 'r',
        Keycode.T: 't',
        Keycode.Y: 'y',
        Keycode.U: 'u',
        Keycode.I: 'i',
        Keycode.O: 'o',
        Keycode.P: 'p',
        Keycode.BACKSPACE: '[BKSP]',  # or handle differently if you prefer
        Keycode.TAB: '[TAB]',  # or just '    ' (four spaces) or '\t' for an actual tab character
        Keycode.A: 'a',
        Keycode.S: 's',
        Keycode.D: 'd',
        Keycode.F: 'f',
        Keycode.G: 'g',
        Keycode.H: 'h',
        Keycode.J: 'j',
        Keycode.K: 'k',
        Keycode.L: 'l',
        Keycode.SEMICOLON: ';',
        Keycode.ENTER: '\n',  # or handle differently if you prefer
        Keycode.SHIFT: '[SHIFT]',  # or just '' if you don't want to record shift presses
        Keycode.Z: 'z',
        Keycode.X: 'x',
        Keycode.C: 'c',
        Keycode.V: 'v',
        Keycode.B: 'b',
        Keycode.N: 'n',
        Keycode.M: 'm',
        Keycode.COMMA: ',',
        Keycode.PERIOD: '.',
        Keycode.UP_ARROW: '[UP]',  # or handle as you see fit
        Keycode.CONTROL: '[CTRL]',  # or just '' if you don't want to record control presses
        Keycode.GUI: '[GUI]',  # or '[WIN]' or '' as preferred
        Keycode.ALT: '[ALT]',
        Keycode.SPACE: ' ',
        Keycode.FORWARD_SLASH: '/',
        Keycode.LEFT_ARROW: '[LEFT]',  # or handle as you see fit
        Keycode.DOWN_ARROW: '[DOWN]',  # or handle as you see fit
        Keycode.RIGHT_ARROW: '[RIGHT]'  # or handle as you see fit
    }
    return mapping.get(keycode, '')

def char_to_keycode(ch):
    """Converts a character to its respective keycode."""
     
    if ch.isupper():
        return (Keycode.SHIFT, char_to_keycode(ch.lower()))

    mapping = {
        '[ESC]': Keycode.ESCAPE,
        'q': Keycode.Q,
        'w': Keycode.W,
        'e': Keycode.E,
        'r': Keycode.R,
        't': Keycode.T,
        'y': Keycode.Y,
        'u': Keycode.U,
        'i': Keycode.I,
        'o': Keycode.O,
        'p': Keycode.P,
        '[BKSP]': Keycode.BACKSPACE,
        '[TAB]': Keycode.TAB, # or if you'd rather map '\t': Keycode.TAB,
        'a': Keycode.A,
        's': Keycode.S,
        'd': Keycode.D,
        'f': Keycode.F,
        'g': Keycode.G,
        'h': Keycode.H,
        'j': Keycode.J,
        'k': Keycode.K,
        'l': Keycode.L,
        ';': Keycode.SEMICOLON,
        '\n': Keycode.ENTER,
        '[SHIFT]': Keycode.SHIFT,
        'z': Keycode.Z,
        'x': Keycode.X,
        'c': Keycode.C,
        'v': Keycode.V,
        'b': Keycode.B,
        'n': Keycode.N,
        'm': Keycode.M,
        ',': Keycode.COMMA,
        '.': Keycode.PERIOD,
        '[UP]': Keycode.UP_ARROW,
        '[CTRL]': Keycode.CONTROL,
        '[GUI]': Keycode.GUI,
        '[ALT]': Keycode.ALT,
        ' ': Keycode.SPACE,
        '/': Keycode.FORWARD_SLASH,
        '[LEFT]': Keycode.LEFT_ARROW,
        '[DOWN]': Keycode.DOWN_ARROW,
        '[RIGHT]': Keycode.RIGHT_ARROW
    }
    return mapping.get(ch, None)

    return None  # If the character isn't recognized

print("Waiting for keypresses...")

#Chat GPT code

url = "https://api.openai.com/v1/chat/completions"
headers = {"Content-Type": "application/json",
			"Authorization": os.getenv('OPEN_AI_KEY')}

#  connect to SSID
wifi.radio.connect('SSID', 'Password')

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())


messages = [
    {"content": "You are an ethereal spirit with a haunted, spooky vibe, who makes brief, dark, barely coherent statements.", "role": "system"}
]
jsonData = {
    "model": "gpt-3.5-turbo",
    "temperature": 1,
    "max_tokens": 200,
    "messages": messages
}


# Step 1: Initialize an empty string for the accumulated keystrokes.
typed_message = ""
enter_pressed = False  # Add this flag

while True:
    event = km.events.get()
    if event:
        # Calculate row and column from the key_number.
        row, col = divmod(event.key_number, len(KEYMAP[0]))

        # Fetch the HID keycode from the KEYMAP.
        keycode = KEYMAP[row][col]
        if keycode is not None:
            if event.pressed:
                kbd.press(keycode)
                
                # Instead of printing the keystrokes, accumulate them.
                if keycode == Keycode.BACKSPACE:
                    typed_message = typed_message[:-1]  # Remove the last character.
                elif keycode == Keycode.ENTER:
                    kbd.release(keycode)
                    if not enter_pressed:  # Check if "Enter" was already pressed
                        # Use the accumulated typed_message as the message for the API.
                        messages.append({"content": typed_message, "role": "user"})
                        jsonData["messages"] = messages

                        response = requests.request("POST", url, json=jsonData, headers=headers, timeout=15)
                        print('response status code=', response.status_code)

                        response = json.loads(response.text)
                        role = str(response['choices'][0]['message']['role'])
                        response_content = str(response['choices'][0]['message']['content'])
                        response = "\n" + response_content + "\n\n"  # add two newline characters before the actual content
                        print(response)

                        # After receiving the response, "type out" the characters
                        for char in response:
                            keycode = char_to_keycode(char)
                            if keycode:
                                if isinstance(keycode, tuple):
                                    kbd.press(keycode[0])  # Press the Shift key
                                    kbd.press(keycode[1])  # Press the character key
                                    kbd.release_all()      # Release all keys
                                else:
                                    kbd.press(keycode)
                                    kbd.release(keycode)
                                time.sleep(0.05)

                        # Reset typed_message and messages for the next input.
                        typed_message = ""
                        messages = [
                            {"content": "You are an ethereal spirit with a haunted, spooky vibe, who makes brief, dark, barely coherent statements.", "role": "system"}
                        ]

                        enter_pressed = True  # Set the flag to True, indicating "Enter" has been pressed
                else:
                    # Handle capital letters, etc.
                    typed_message += keycode_to_char(keycode)

            else:
                kbd.release_all()
                kbd.release(keycode)
