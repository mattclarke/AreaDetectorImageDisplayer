import argparse
import os
import time

import matplotlib.pyplot as plt
from epics import caget
from matplotlib.animation import FuncAnimation
from p4p.client.thread import Context
from PIL import Image

MAX_SIZE = 512
QUALITY = 80
OUTPUT_DIR = "./images/"
P4P_CONTEXT = Context("pva")


def get_ad_image_data(prefix, use_ca=False):
    if use_ca:
        get_pv = caget
    else:
        get_pv = P4P_CONTEXT.get

    raw = get_pv(f"{prefix}:ArrayData")
    size_0 = get_pv(f"{prefix}:ArraySize0_RBV")
    size_1 = get_pv(f"{prefix}:ArraySize1_RBV")
    size_2 = get_pv(f"{prefix}:ArraySize2_RBV")
    colour_mode = get_pv(f"{prefix}:ColorMode_RBV")
    return raw, colour_mode, [size_0, size_1, size_2]


def convert_to_resized_image(data):
    buffer, colour_mode, sizes = data
    if colour_mode == 0:  # Mono
        image = Image.frombuffer("L", (sizes[0], sizes[1]), buffer, "raw", "L", 0, 1)
    elif colour_mode == 2:  # RGB1
        image = Image.frombuffer(
            "RGB", (sizes[1], sizes[2]), buffer, "raw", "RGB", 0, 1
        )
    elif colour_mode == 3:  # RGB2
        image = Image.frombuffer(
            "RGB", (sizes[0], sizes[2]), buffer, "raw", "RGB", 0, 1
        )
    else:
        raise Exception(f"Cannot handle {colour_mode}")
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--animation-mode",
        action="store_true",
        help="runs as an updating animation",
    )
    parser.add_argument(
        "-s", "--save", action="store_true", help="save the image as jpeg"
    )

    parser.add_argument("-c", "--ca", action="store_true", help="use channel access")

    args = parser.parse_args()

    if args.animation_mode:
        # Basic updating image
        fig, _ = plt.subplots()

        def update(frame):
            raw_image_data = get_ad_image_data("13SIM1:image1", args.ca)
            img = convert_to_resized_image(raw_image_data)
            return plt.imshow(img)

        animation = FuncAnimation(fig, update, interval=500)
        plt.show()
    else:
        raw_image_data = get_ad_image_data("13SIM1:image1", args.ca)
        img = convert_to_resized_image(raw_image_data)
        if args.save:
            save_image_as_jpeg(img)

        image_plot = plt.imshow(img)
        plt.colorbar()
        plt.show()
