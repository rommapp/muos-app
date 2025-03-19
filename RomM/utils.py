from PIL import ImageFile


def has_alpha_channel(image: ImageFile) -> bool:
    return image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    )
