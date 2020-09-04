import os
import time

import matplotlib.pyplot as plt
from epics import PV
from PIL import Image

MAX_SIZE = 1024
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
        img.save(path, "JPEG", quality=QUALITY)
        if img.width > MAX_SIZE or img.height > MAX_SIZE:
            self._resize_image(path)
        return os.path.abspath(path)

    def _resize_image(self, path):
        # For some reason we have to save then reopen the file
        # to be able to resize it correctly!
        img = Image.open(path)
        img.thumbnail((MAX_SIZE, MAX_SIZE), Image.NEAREST)
        img.save(path, "JPEG", quality=QUALITY)


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
                raise PvNotFoundException("Unable to find PV %s" % name)
            return ans
        except PvNotFoundException as err:
            # PV not found
            print(err)
            raise
        except Exception as err:
            # Something general went wrong
            raise PvGetException("Unable to get value for PV %s: %s" % (name, err))

    def get_ad_image_data(self, prefix):
        raw = self.caget("%s:ArrayData" % prefix)
        xsize = self.caget("%s:ArraySize0_RBV" % prefix)
        ysize = self.caget("%s:ArraySize1_RBV" % prefix)
        return raw, xsize, ysize


if __name__ == "__main__":
    epics_client = EpicsFetcher()
    test = epics_client.get_ad_image_data("13SIM1:image1")
    print(test)
    converter = ADConverter()
    filepath = converter.convert_to_jpg(test)

    photo = plt.imread(filepath)
    plt.imshow(photo)
    plt.show()
