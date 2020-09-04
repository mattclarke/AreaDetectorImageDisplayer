import os
import time

import matplotlib.pyplot as plt
from epics import PV
from PIL import Image

MAX_SIZE = 512
QUALITY = 80
OUTPUT_DIR = "./images/"


class PvNotFoundException(Exception):
    pass


class PvGetException(Exception):
    pass


def caget(name, as_str=False):
    try:
        pv = PV(name)
        ans = pv.get(as_string=as_str)
        if not pv.connected:
            raise PvNotFoundException(f"Unable to find PV {name}")
        return ans
    except PvNotFoundException as err:
        # PV not found
        print(err)
        raise
    except Exception as err:
        # Something general went wrong
        raise PvGetException(f"Unable to get value for PV {name}: {err}")


def get_ad_image_data(prefix):
    raw = caget(f"{prefix}:ArrayData")
    xsize = caget(f"{prefix}:ArraySize0_RBV")
    ysize = caget(f"{prefix}:ArraySize1_RBV")
    return raw, xsize, ysize


def convert_to_resized_image(data):
    image = Image.frombuffer("L", (data[1], data[2]), data[0], "raw", "L", 0, 1)
    if image.width > MAX_SIZE or image.height > MAX_SIZE:
        if image.width > image.height:
            new_size = (MAX_SIZE, MAX_SIZE * int(image.height / image.width))
        else:
            new_size = (MAX_SIZE * int(image.width / image.height), MAX_SIZE)
        image = image.resize(new_size, Image.BOX)
    return image


def save_image_as_jpeg(image):
    # Create the images folder if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    path = f"{OUTPUT_DIR}out-{int(time.time())}.jpg"
    image.save(path, "JPEG", quality=QUALITY)
    return os.path.abspath(path)


if __name__ == "__main__":
    image_data = get_ad_image_data("13SIM1:image1")
    img = convert_to_resized_image(image_data)
    save_image_as_jpeg(img)

    plt.imshow(img)
    plt.colorbar()
    plt.show()
