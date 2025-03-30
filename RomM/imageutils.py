from typing import Optional

from PIL import Image, ImageDraw


class ImageUtils:
    _instance: Optional["ImageUtils"] = None
    _initialized: bool = False

    def __new__(cls, width: int, height: int):
        if cls._instance is None:
            cls._instance = super(ImageUtils, cls).__new__(cls)
        return cls._instance

    def __init__(self, width: int, height: int) -> None:
        if not self._initialized:
            self.width = width
            self.height = height
            self.fade_mask = self.generate_fade_mask(width, height)
            self._initialized = True

    def generate_fade_mask(self, width: int, height: int) -> Image.Image:
        fade_mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(fade_mask)
        x_crit = width / 3.0

        for x in range(width):
            if x < x_crit:
                t = x / x_crit
                alpha = int((t**2) * (255 / 3))  # a x = x_crit, alpha = 255/3 ≈ 85
            else:
                t = (x - x_crit) / (width - x_crit)
                alpha = int(85 + t * (255 - 85))
            draw.line([(x, 0), (x, height)], fill=alpha)

        return fade_mask

    def add_rounded_corners(self, image, radius):
        rounded_mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(rounded_mask)
        draw.rounded_rectangle(
            (0, 0, image.size[0], image.size[1]), radius=radius, fill=255
        )
        image.putalpha(rounded_mask)
        return image

    def load_image_from_url(self, url: str, headers) -> Image.Image:
        from io import BytesIO
        from urllib.request import Request, urlopen

        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=60) as response:  # trunk-ignore(bandit/B310)
                data = response.read()
            return Image.open(BytesIO(data)).convert("RGBA")
        except Exception as e:
            print(f"Error loading image from URL {url}: {e}")
            return None

    def process_assets(
        self,
        fullscreen: bool,
        cover_url: str,
        screenshot_url: str,
        box_path: str,
        preview_path: str,
        headers,
    ) -> None:
        print(
            f"process_assets -> {fullscreen} {cover_url} - {screenshot_url} - {box_path} - {preview_path}"
        )

        if not cover_url and not screenshot_url:
            return

        final_width, final_height = self.width, self.height

        background = None

        preview = (
            self.load_image_from_url(screenshot_url, headers)
            if screenshot_url
            else None
        )

        if preview:
            preview = preview.resize((final_width, final_height))
            preview.save(preview_path)

        if fullscreen:
            if preview:
                background = preview
            else:
                background = Image.new(
                    "RGBA", (final_width, final_height), (0, 0, 0, 0)
                )
            background.putalpha(self.fade_mask)

        foreground = self.load_image_from_url(cover_url, headers) if cover_url else None

        if foreground:
            max_cover_width = 215
            max_cover_height = int(final_height * 3 / 5)
            scale_w = max_cover_width / foreground.width
            scale_h = max_cover_height / foreground.height
            scale = min(scale_w, scale_h)
            new_cover_width = int(foreground.width * scale)
            new_cover_height = int(foreground.height * scale)
            foreground = foreground.resize((new_cover_width, new_cover_height))

            foreground = self.add_rounded_corners(foreground, radius=20)

            fg_x = final_width - new_cover_width - 20
            fg_y = (final_height - new_cover_height) // 2

            if background:
                background.paste(foreground, (fg_x, fg_y), foreground)
            else:
                background = foreground

        if background:
            background.save(box_path)
