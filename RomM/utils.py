import os
from PIL import Image, ImageFile


def has_alpha_channel(image: ImageFile) -> bool:
    return image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    )

def add_alpha_channel(path: str) -> ImageFile:
    img = Image.open(path)
    if not has_alpha_channel(img):
        img = img.convert("RGBA")
        img.save(path)
    return img

def jpg_to_png(path: str) -> ImageFile:
    img = Image.open(path)
    png_path = path.rsplit('.', 1)[0] + '.png'
    img.save(png_path, 'PNG')
    os.remove(path)
    return img

def str_to_bool(s: str) -> bool:
    return s.lower() in ("yes", "true", "t", "1")
