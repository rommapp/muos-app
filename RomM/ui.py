import ctypes
import os
import shutil
import time
from typing import Optional

import sdl2
from config import (
    color_btn_a,
    color_btn_b,
)
from filesystem import Filesystem
from glyps import glyphs
from models import Collection, Platform, Rom
from PIL import Image, ImageDraw, ImageFont
from status import Status

FONT_FILE = {15: ImageFont.truetype(os.path.join(os.getcwd(), "fonts/romm.ttf"), 12)}

color_row_bg = "#383838"
color_menu_bg = "#141414"
color_progress_bar = "#3d6b39"
color_text = "#ffffff"


class UserInterface:
    _instance: Optional["UserInterface"] = None
    _initialized: bool = False

    fs = Filesystem()
    status = Status()

    screen_width = 640
    screen_height = 480
    font_file = FONT_FILE
    layout_name = os.getenv("CONTROLLER_LAYOUT", "nintendo")

    active_image: Image.Image
    active_draw: ImageDraw.ImageDraw

    def __init__(self):
        if self._initialized:
            return
        self.window = self._create_window()
        self.renderer = self._create_renderer()
        self.draw_start()
        self.opt_stretch = True
        self._initialized = True

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(UserInterface, cls).__new__(cls)
        return cls._instance

    ###
    # WINDOW MANAGEMENT
    ###

    def create_image(self):
        """Create a new blank RGBA image for drawing."""
        return Image.new("RGBA", (self.screen_width, self.screen_height), color="black")

    def draw_start(self):
        """Initialize drawing for a new frame."""
        # Render directly to the screen
        sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(self.renderer)
        self.active_image = self.create_image()
        self.active_draw = ImageDraw.Draw(self.active_image)

    def _create_window(self):
        window = sdl2.SDL_CreateWindow(
            "RomM".encode("utf-8"),
            sdl2.SDL_WINDOWPOS_UNDEFINED,
            sdl2.SDL_WINDOWPOS_UNDEFINED,
            0,
            0,  # Size ignored in fullscreen mode
            sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP | sdl2.SDL_WINDOW_SHOWN,
        )

        if not window:
            print(f"Failed to create window: {sdl2.SDL_GetError()}")
            raise RuntimeError("Failed to create window")

        return window

    def _create_renderer(self):
        renderer = sdl2.SDL_CreateRenderer(
            self.window, -1, sdl2.SDL_RENDERER_ACCELERATED
        )

        if not renderer:
            print(f"Failed to create renderer: {sdl2.SDL_GetError()}")
            raise RuntimeError("Failed to create renderer")

        sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, b"0")
        return renderer

    def render_to_screen(self):
        # Convert PIL image to SDL2 texture at base resolution
        rgba_data = self.active_image.tobytes()
        surface = sdl2.SDL_CreateRGBSurfaceWithFormatFrom(
            rgba_data,
            self.screen_width,
            self.screen_height,
            32,
            self.screen_width * 4,
            sdl2.SDL_PIXELFORMAT_RGBA32,
        )
        texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, surface)
        sdl2.SDL_FreeSurface(surface)

        # Get current window size
        window_width = ctypes.c_int()
        window_height = ctypes.c_int()
        sdl2.SDL_GetWindowSize(
            self.window, ctypes.byref(window_width), ctypes.byref(window_height)
        )
        window_width, window_height = window_width.value, window_height.value

        # Let the user decide whether to stretch to fit or preserve aspect ratio
        if not self.opt_stretch:
            scale = min(
                window_width / self.screen_width, window_height / self.screen_height
            )
            dst_width = int(self.screen_width * scale)
            dst_height = int(self.screen_height * scale)
            dst_x = (window_width - dst_width) // 2
            dst_y = (window_height - dst_height) // 2
            dst_rect = sdl2.SDL_Rect(dst_x, dst_y, dst_width, dst_height)
        else:
            dst_rect = sdl2.SDL_Rect(0, 0, window_width, window_height)

        sdl2.SDL_RenderCopy(self.renderer, texture, None, dst_rect)
        sdl2.SDL_RenderPresent(self.renderer)
        sdl2.SDL_DestroyTexture(texture)

    def cleanup(self):
        sdl2.SDL_DestroyRenderer(self.renderer)
        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

    ###
    # DRAWING FUNCTIONS
    ###

    def draw_clear(self):
        self.active_draw.rectangle(
            [0, 0, self.screen_width, self.screen_height], fill="black"
        )

    def draw_text(
        self,
        position: tuple[float, float],
        text: str,
        font: int = 15,
        color: str = color_text,
        **kwargs,
    ):
        self.active_draw.text(
            position, text, font=self.font_file[font], fill=color, **kwargs
        )

    def draw_rectangle(
        self,
        position: ImageDraw.Coords,
        fill: str | None = None,
        outline: str | None = None,
        width: int = 1,
    ):
        self.active_draw.rectangle(position, fill=fill, outline=outline, width=width)

    def draw_rectangle_r(
        self,
        position: ImageDraw.Coords,
        radius: float,
        fill: str | None = None,
        outline: str | None = None,
    ):
        self.active_draw.rounded_rectangle(position, radius, fill=fill, outline=outline)

    def row_list(
        self,
        text: str,
        position: ImageDraw.Coords,
        width: int,
        height: int,
        selected: bool = False,
        fill: Optional[str] = None,
        color: str = color_text,
        outline: str | None = None,
        append_icon_path: str | None = None,
    ):
        if fill is None:
            fill = color_btn_a if self.layout_name == "nintendo" else color_btn_b
        try:
            icon = Image.open(append_icon_path) if append_icon_path else None
        except (FileNotFoundError, AttributeError):
            icon = None

        radius = 5
        margin_left_text = 12 + (35 if icon else 0)
        margin_top_text = 8
        self.draw_rectangle_r(
            [position[0], position[1], position[0] + width, position[1] + height],
            radius,
            fill=fill if selected else color_row_bg,
            outline=outline,
        )

        if icon:
            margin_left_icon = 10
            margin_top_icon = 5
            self.active_image.paste(
                icon,
                (position[0] + margin_left_icon, position[1] + margin_top_icon),
                mask=icon if icon.mode == "RGBA" else None,
            )

        self.draw_text(
            (position[0] + margin_left_text, position[1] + margin_top_text),
            text,
            color=color,
        )

    def draw_circle(
        self,
        position: ImageDraw.Coords,
        radius: int,
        fill: str | None = None,
        outline: str | None = color_text,
    ):
        self.active_draw.ellipse(
            [
                position[0] - radius,
                position[1] - radius,
                position[0] + radius,
                position[1] + radius,
            ],
            fill=fill,
            outline=outline,
        )

    def button_circle(
        self,
        position: ImageDraw.Coords,
        button: str,
        text: str,
        color: Optional[str] = None,
    ):
        if color is None:
            color = color_btn_a if self.layout_name == "nintendo" else color_btn_b
        radius = 10
        btn_text_offset = 1
        label_margin_l = 20

        self.draw_circle(position, radius, fill=color, outline=None)
        self.draw_text(
            (position[0] + btn_text_offset, position[1] + btn_text_offset),
            button,
            anchor="mm",
        )
        self.draw_text(
            (position[0] + label_margin_l, position[1] + btn_text_offset),
            text,
            font=15,
            anchor="lm",
        )

    def draw_log(
        self,
        text_line_1: str = "",
        text_line_2: str = "",
        fill: str = "black",
        outline: str = "black",
        text_color: str = color_text,
        background: bool = True,
    ):
        margin_bg = 5
        margin_bg_bottom = 40
        radius_bg = 5
        max_len_text = 65
        margin_left_text = 15
        margin_text_bottom = 29
        margin_text_bottom_multiline_line_1 = 38
        margin_text_bottom_multiline_line_2 = 21

        if background:
            self.draw_rectangle_r(
                [
                    margin_bg,
                    self.screen_height - margin_bg_bottom,
                    self.screen_width - margin_bg,
                    self.screen_height - margin_bg,
                ],
                radius_bg,
                fill=fill,
                outline=outline,
            )

        self.draw_text(
            (
                margin_left_text,
                (
                    self.screen_height - margin_text_bottom
                    if not text_line_2
                    else self.screen_height - margin_text_bottom_multiline_line_1
                ),
            ),
            (
                text_line_1
                if len(text_line_1) <= max_len_text
                else text_line_1[:max_len_text] + "..."
            ),
            color=text_color,
        )

        if text_line_2:
            self.draw_text(
                (
                    margin_left_text,
                    self.screen_height - margin_text_bottom_multiline_line_2,
                ),
                (
                    text_line_2
                    if len(text_line_2) <= max_len_text
                    else text_line_2[:max_len_text] + "..."
                ),
                color=text_color,
            )

    def draw_loader(self, percent: int, color: str = color_progress_bar):
        margin = 10
        margin_top = 38
        margin_bottom = 4
        radius = 2

        self.draw_rectangle_r(
            [
                margin,
                self.screen_height - margin_top,
                margin + (self.screen_width - 2 * margin) * (percent / 100),
                self.screen_height - margin_bottom,
            ],
            radius,
            fill=color,
            outline=None,
        )

    def draw_header(self, host: str, username: str):
        username = username if len(username) <= 22 else username[:19] + "..."
        logo = Image.open(os.path.join(os.getcwd(), "resources/romm.png"))
        pos_logo = [15, 15]
        pos_text = [55, 9]
        self.active_image.paste(
            logo, (pos_logo[0], pos_logo[1]), mask=logo if logo.mode == "RGBA" else None
        )

        roms_path = self.fs.get_roms_storage_path()
        total, used, _free = shutil.disk_usage(roms_path)

        # Convert to GB
        total_gb = total / (1024**3)
        used_gb = used / (1024**3)

        # Calculate percentage
        used_percentage = (used / total) * 100

        self.draw_text(
            (pos_text[0], pos_text[1]),
            f"{glyphs.host} {host} | {glyphs.user} {username}\n"
            f"{glyphs.microsd} {roms_path} ({used_gb:.1f}/{total_gb:.1f} GB, {used_percentage:.1f}% used)",
        )

        if self.status.profile_pic_path:
            profile_pic = Image.open(self.status.profile_pic_path)
            margin_right_profile_pic = 45
            margin_top_profile_pic = 5
            pos_profile_pic = [
                self.screen_width - margin_right_profile_pic,
                margin_top_profile_pic,
            ]

            self.active_image.paste(
                profile_pic,
                (pos_profile_pic[0], pos_profile_pic[1]),
                mask=profile_pic if profile_pic.mode == "RGBA" else None,
            )

    def draw_platforms_list(
        self,
        platforms_selected_position: int,
        max_n_platforms: int,
        platforms: list[Platform],
        fill: Optional[str] = None,
    ):
        if fill is None:
            fill = color_btn_a if self.layout_name == "nintendo" else color_btn_b

        self.draw_rectangle_r(
            [10, 50, self.screen_width - 10, 100], 5, outline=color_menu_bg
        )
        self.draw_text(
            (self.screen_width / 2, 62),
            "Platforms",
            anchor="mm",
        )
        self.draw_rectangle_r(
            [10, 70, self.screen_width - 10, self.screen_height - 43],
            0,
            fill=color_menu_bg,
            outline=None,
        )

        start_idx = int(platforms_selected_position / max_n_platforms) * max_n_platforms
        end_idx = start_idx + max_n_platforms

        for i, p in enumerate(platforms[start_idx:end_idx]):
            is_selected = i == (platforms_selected_position % max_n_platforms)
            row_text = (
                f"{p.display_name} ({p.rom_count})"
                if len(p.display_name) <= 55
                else p.display_name[:55] + f"... ({p.rom_count})"
            )
            self.row_list(
                row_text,
                (20, 80 + (i * 35)),
                self.screen_width - 40,
                32,
                is_selected,
                fill=fill,
                append_icon_path=f"{self.fs.resources_path}/{p.slug}.ico",
            )

    def draw_collections_list(
        self,
        collections_selected_position: int,
        max_n_collections: int,
        collections: list[Collection],
        fill: Optional[str] = None,
    ):
        if fill is None:
            fill = color_btn_b if self.layout_name == "nintendo" else color_btn_a

        self.draw_rectangle_r(
            [10, 50, self.screen_width - 10, 100], 5, outline=color_menu_bg
        )
        self.draw_text(
            (self.screen_width / 2, 62),
            "Collections",
            anchor="mm",
        )
        self.draw_rectangle_r(
            [10, 70, self.screen_width - 10, self.screen_height - 43],
            0,
            fill=color_menu_bg,
            outline=None,
        )

        start_idx = (
            int(collections_selected_position / max_n_collections) * max_n_collections
        )
        end_idx = start_idx + max_n_collections
        max_len_text = 60
        for i, c in enumerate(collections[start_idx:end_idx]):
            is_selected = i == (collections_selected_position % max_n_collections)
            row_text = c.name

            if len(row_text) > max_len_text:
                row_text = row_text + " "  # Add empty space for the rotation

            # Calculate shift offset based on time
            shift_offset = (int(time.time() * 2)) % len(row_text)
            # Shift text
            row_text = (
                row_text[shift_offset:] + row_text[:shift_offset]
                if len(row_text) > max_len_text
                else row_text
            )
            row_text = (
                f"{row_text} ({c.rom_count})"
                if len(row_text) <= max_len_text
                else row_text[:max_len_text] + f" ({c.rom_count})"
            )

            self.row_list(
                row_text,
                (20, 80 + (i * 35)),
                self.screen_width - 40,
                32,
                is_selected,
                fill=fill,
            )

    def draw_roms_list(
        self,
        roms_selected_position: int,
        max_n_roms: int,
        roms: list[Rom],
        header_text: str,
        header_color: str,
        multi_selected_roms: list[Rom],
        prepend_platform_slug: bool = False,
    ):
        self.draw_rectangle_r(
            [10, 50, self.screen_width - 10, 100], 5, outline=color_menu_bg
        )
        self.draw_text(
            (self.screen_width / 2, 62),
            header_text,
            color=header_color,
            anchor="mm",
        )
        self.draw_rectangle_r(
            [10, 70, self.screen_width - 10, self.screen_height - 43],
            0,
            fill=color_menu_bg,
            outline=None,
        )

        # Adjust max text length to reserve space for file size and padding
        padding = 4  # Additional padding in characters
        max_len_text = (
            int((self.screen_width - 71) / 11)
            - (4 if prepend_platform_slug else 0)
            - padding
        )

        start_idx = int(roms_selected_position / max_n_roms) * max_n_roms
        end_idx = min(start_idx + max_n_roms, len(roms))
        for i, r in enumerate(roms[start_idx:end_idx]):
            is_selected = i == (roms_selected_position % max_n_roms)
            is_in_device = self.fs.is_rom_in_device(r)
            sync_flag_text = f"{glyphs.cloud_sync}" if is_in_device else ""

            # Build base row text
            row_text = r.name
            row_text += f" ({','.join(r.languages)})" if r.languages else ""
            row_text += f" ({','.join(r.regions)})" if r.regions else ""
            row_text += f" ({','.join(r.revision)})" if r.revision else ""
            row_text += f" ({','.join(r.tags)})" if r.tags else ""

            # Handle text scrolling
            if len(row_text) > max_len_text:
                row_text = row_text + " "
                shift_offset = (int(time.time() * 2)) % len(row_text)
                row_text = row_text[shift_offset:] + row_text[:shift_offset]

            # Truncate base text and append file size with padding
            size_text = f"[{r.fs_size[0]}{r.fs_size[1]}] {sync_flag_text}"
            if len(row_text) > max_len_text:
                row_text = row_text[:max_len_text]
            row_text = f"{row_text} {size_text}"

            # Add checkbox
            row_text = f"{glyphs.checkbox_selected if r in multi_selected_roms else glyphs.checkbox} {row_text}"

            self.row_list(
                row_text,
                (20, 80 + (i * 35)),
                self.screen_width - 40,
                32,
                is_selected,
                fill=header_color,
                outline=header_color if r in multi_selected_roms else None,
                append_icon_path=(
                    f"{self.fs.resources_path}/{r.platform_slug}.ico"
                    if prepend_platform_slug
                    else ""
                ),
            )

    def draw_menu_background(
        self,
        pos,
        width,
        n_options,
        option_height,
        gap,
        padding,
        extra_top_offset=0,
        extra_bottom_offset=0,
    ):
        self.draw_rectangle_r(
            [
                pos[0],
                pos[1] - extra_top_offset,
                pos[0] + width + padding * 2,
                pos[1]
                + n_options * (option_height + gap)
                + padding * 2
                - gap
                + extra_bottom_offset,
            ],
            5,
            fill=color_menu_bg,
            outline=(
                color_btn_a if UserInterface.layout_name == "nintendo" else color_btn_b
            ),
        )
