import io
from PIL import ImageGrab

def excute_screenshot():
    # Get the screenshot as a PIL image
    pil_image = ImageGrab.grab()
    
    # Convert the image to bytes
    with io.BytesIO() as output:
        pil_image.save(output, format='PNG')
        return output.getvalue()
