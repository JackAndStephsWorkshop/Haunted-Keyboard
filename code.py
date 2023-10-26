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
import neopixel

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

chatGPT_enabled = True  # By default, the ChatGPT section is enabled.

# === Keyboard Setup ===
km = keypad.KeyMatrix(
    row_pins=(board.GP15, board.GP12, board.GP13, board.GP14),
    column_pins=(
        board.GP16, board.GP17, board.GP18, board.GP19, board.GP20, board.GP21,
        board.GP22, board.GP11, board.GP10, board.GP9, board.GP8, board.GP7
    ),
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


# === NeoPixel Setup ===

pixel_pin = board.GP26

# The number of NeoPixels
num_pixels = 6

ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.5, auto_write=False, pixel_order=ORDER
)

# === Keymap Configuration ===
KEYMAP = [
    [Keycode.ESCAPE, Keycode.Q, Keycode.W, Keycode.E, Keycode.R, Keycode.T, Keycode.Y, Keycode.U, Keycode.I, Keycode.O, Keycode.P, Keycode.BACKSPACE],
    [Keycode.TAB, Keycode.A, Keycode.S, Keycode.D, Keycode.F, Keycode.G, Keycode.H, Keycode.J, Keycode.K, Keycode.L, Keycode.SEMICOLON, Keycode.ENTER],
    [Keycode.SHIFT, Keycode.Z, Keycode.X, Keycode.C, Keycode.V, Keycode.B, Keycode.N, Keycode.M, Keycode.COMMA, Keycode.PERIOD, Keycode.UP_ARROW, Keycode.SHIFT],
    [Keycode.CONTROL, Keycode.GUI, Keycode.ALT, Keycode.SPACE, None, Keycode.SPACE, None, Keycode.QUOTE, Keycode.FORWARD_SLASH, Keycode.LEFT_ARROW, Keycode.DOWN_ARROW, Keycode.RIGHT_ARROW]
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
        Keycode.QUOTE: '"',
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
        '"': Keycode.QUOTE,
        '/': Keycode.FORWARD_SLASH,
        '[LEFT]': Keycode.LEFT_ARROW,
        '[DOWN]': Keycode.DOWN_ARROW,
        '[RIGHT]': Keycode.RIGHT_ARROW
    }
    return mapping.get(ch, None)

    return None  # If the character isn't recognized

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b) if ORDER in (neopixel.RGB, neopixel.GRB) else (r, g, b, 0)


def rainbow_cycle(wait):
    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)


# === Main Execution ===
escape_sequence_count = 0
chatgpt_enabled = True

print("Waiting for keypresses...")



#Chat GPT code

url = "https://api.openai.com/v1/chat/completions"
headers = {"Content-Type": "application/json",
         "Authorization": os.getenv('OPEN_AI_KEY')}

# List of SSID and password pairs
networks = [
    ('Unintended Consequences', 'entropy!'),
    ('STRONGHOLD', 'strongholdclimb'),
    ("Jack's iPhone", "inininin")
]


connected = False

for ssid, password in networks:
    try:
        wifi.radio.connect(ssid, password)
        connected = True
        print(f"Connected to {ssid}.")
        break
    except Exception as e:
        print(f"Failed to connect to {ssid}. Error: {e}")

if connected:
    pool = socketpool.SocketPool(wifi.radio)
    requests = adafruit_requests.Session(pool, ssl.create_default_context())
    # Add other code here for when you are connected
else:
    print("Failed to connect to any network.")


messages = [
    {"content": "You are an ethereal spirit that haunts this mechanical keyboard with a spooky vibe, who makes brief, haunting predictive statements.", "role": "system"}
]
jsonData = {
    "model": "gpt-3.5-turbo",
    "temperature": 1,
    "max_tokens": 200,
    "messages": messages
}

chatgpt_enabled = True  # This variable will determine whether Chat GPT functionality is active

# Step 1: Initialize an empty string for the accumulated keystrokes.
typed_message = ""
enter_pressed = False  # Add this flag

# Initialize a list to track the last three keypresses and their timestamps
last_three_keys = [(None, 0), (None, 0), (None, 0)]


while True:
    pixels.fill((255, 165, 0))
    pixels.show()
    event = km.events.get()
    if event:
        # Calculate row and column from the key_number.
        row, col = divmod(event.key_number, len(KEYMAP[0]))

        # Fetch the HID keycode from the KEYMAP.
        keycode = KEYMAP[row][col]
        if keycode is not None:
            if event.pressed:
                kbd.press(keycode)
                
                # Update the last_three_keys list
                current_time = time.time()
                last_three_keys.pop(0)  # Remove the oldest key
                last_three_keys.append((keycode, current_time))

                # Check for three consecutive "Escape" key presses within 2 seconds
                if all(k == Keycode.ESCAPE for k, _ in last_three_keys) and (last_three_keys[2][1] - last_three_keys[0][1] <= 2):
                    chatgpt_enabled = not chatgpt_enabled
                    print("Chat GPT is now", "enabled" if chatgpt_enabled else "disabled")
                    last_three_keys = [(None, 0), (None, 0), (None, 0)]  # Reset the list to prevent immediate re-triggering

                # Instead of printing the keystrokes, accumulate them.
                if keycode == Keycode.BACKSPACE:
                    typed_message = typed_message[:-1]  # Remove the last character.
                elif keycode == Keycode.ENTER:
                    kbd.release(keycode)
                    if not enter_pressed and chatgpt_enabled:  # Check if "Enter" was already pressed AND if Chat GPT is enabled
                        enter_pressed = True
                        
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
                            
                else:
                    # Handle capital letters, etc.
                    typed_message += keycode_to_char(keycode)

            else:
                if keycode == Keycode.ENTER:
                    enter_pressed = False  # Reset the enter_pressed flag on Keycode.ENTER release
                kbd.release_all()
                kbd.release(keycode)






