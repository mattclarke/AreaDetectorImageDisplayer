import os
import time

import matplotlib.pyplot as plt
from epics import PV
from PIL import Image

MAX_SIZE = 512
QUALITY = 80


class ADConverter:
    def __init__(self):
        # Create the images folder if it doesn't exist
        self.dir = "./images/"
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def convert_to_jpg(self, data):
        path = f"{self.dir}out-{int(time.time())}.jpg"
        img = Image.frombuffer("L", (data[1], data[2]), data[0], "raw", "L", 0, 1)
        if img.width > MAX_SIZE or img.height > MAX_SIZE:
            if img.width > img.height:
                new_size = (MAX_SIZE, MAX_SIZE * int(img.height / img.width))
            else:
                new_size = (MAX_SIZE * int(img.width / img.height), MAX_SIZE)
            img = img.resize(new_size, Image.BOX)
        img.save(path, "JPEG", quality=QUALITY)
        return os.path.abspath(path)


class PvNotFoundException(Exception):
    pass


class PvGetException(Exception):
    pass


class EpicsFetcher:
    def caget(self, name, as_str=False):
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

    def get_ad_image_data(self, prefix):
        raw = self.caget(f"{prefix}:ArrayData")
        xsize = self.caget(f"{prefix}:ArraySize0_RBV")
        ysize = self.caget(f"{prefix}:ArraySize1_RBV")
        return raw, xsize, ysize


if __name__ == "__main__":
    epics_client = EpicsFetcher()
    test = epics_client.get_ad_image_data("13SIM1:image1")
    converter = ADConverter()
    filepath = converter.convert_to_jpg(test)

    photo = plt.imread(filepath)
    plt.imshow(photo)
    plt.show()
