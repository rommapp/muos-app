import os
import sys
import threading
import time
from typing import Any, Tuple

import sdl2
import sdl2.ext

if os.path.exists(os.path.join(os.path.dirname(__file__), "__version__.py")):
    from __version__ import version
else:
    version = "unknown"

from api import API
from filesystem import Filesystem
from glyps import glyphs
from input import Input
from status import Filter, Status, View
from ui import (
    UserInterface,
    color_btn_a,
    color_btn_b,
    color_btn_shoulder,
    color_btn_x,
    color_btn_y,
    color_menu_bg,
    color_sel,
    color_text,
)
from update import Update


class StartMenuOptions:
    ABORT_DOWNLOAD = f"{glyphs.abort} Abort downloads"
    SD_SWITCH = f"{glyphs.microsd} Switch SD"
    EXIT = f"{glyphs.exit} Exit"


class RomM:
    running: bool = True
    spinner_speed = 0.05

    def __init__(self) -> None:
        self.api = API()
        self.fs = Filesystem()
        self.input = Input()
        self.status = Status()
        self.ui = UserInterface()
        self.updater = Update(self)

        self.contextual_menu_options: list[Tuple[str, int, Any]] = []
        self.start_menu_selected_position = 0
        self.contextual_menu_selected_position = 0
        self.platforms_selected_position = 0
        self.collections_selected_position = 0
        self.roms_selected_position = 0

        self.max_n_platforms = 10
        self.max_n_collections = 10
        self.max_n_roms = 10
        self.buttons_config: list[dict[str, str]] = []

        self.last_spinner_update = time.time()
        self.current_spinner_status = next(glyphs.spinner)

        # Set update variables
        self.awaiting_input = False
        self.latest_version = None
        self.download_url = None

        # Set start menu options
        self.start_menu_options = [
            (StartMenuOptions.ABORT_DOWNLOAD, 0),
            (StartMenuOptions.SD_SWITCH, 1 if self.fs._sd2_roms_storage_path else -1),
            (StartMenuOptions.EXIT, 2 if self.fs._sd2_roms_storage_path else 1),
        ]

    def draw_buttons(self):
        # Button rendering with adjusted spacing
        pos_x = 20  # Starting x position
        radius = 20  # Diameter of button circle
        char_width = 6  # Pixels per character (font=12, adjust as needed)
        padding = 10  # Fixed spacing between buttons

        for config in self.buttons_config:
            self.ui.button_circle(
                (pos_x, 460), config["key"], config["label"], color=config["color"]
            )
            # Calculate width: circle + margin to text + text length
            label_length = len(config["label"])
            text_width = label_length * char_width
            total_width = (
                radius + 20 + text_width
            )  # 20 is label_margin_l from button_circle
            pos_x += total_width + padding

    def _check_for_updates(self):
        self.ui.draw_clear()
        self.status.updating.set()
        if self.status.updating.is_set():
            current_time = time.time()
            if current_time - self.last_spinner_update >= self.spinner_speed:
                self.last_spinner_update = current_time
                self.current_spinner_status = next(glyphs.spinner)
            self.ui.draw_log(
                text_line_1=f"{self.current_spinner_status} Checking for updates"
            )
            self.ui.render_to_screen()

        # Get latest release from GitHub API
        release_info = self.updater.get_latest_release_info()

        if release_info is None:
            self.ui.draw_log(
                text_line_1=f"{self.current_spinner_status} Failed to get release info, check internet connection"
            )
            self.ui.render_to_screen()
            self.status.updating.clear()
            sdl2.SDL_Delay(1000)
            return

        latest_tag = release_info.get("tag_name", "")
        if not latest_tag:
            print("Failed to find latest release tag")
            self.status.updating.clear()
            return

        latest_version = latest_tag.lstrip("v")
        download_url = None
        for asset in release_info.get("assets", []):
            if "browser_download_url" in asset:
                download_url = asset["browser_download_url"]
                break

        if not download_url:
            print("Failed to find download URL")
            self.status.updating.clear()
            return

        # Compare versions
        if (
            self.updater.compare_versions(self.updater.current_version, latest_version)
            < 0
        ):
            self.awaiting_input = True
            self.latest_version = latest_version
            self.download_url = download_url
        else:
            self.ui.draw_clear()
            self.ui.draw_log(
                text_line_1=f"App is up to date (v{self.updater.current_version})"
            )
            self.ui.render_to_screen()
            self.status.updating.clear()
            sdl2.SDL_Delay(1000)

    def _handle_update_confirmation(self):
        if self.awaiting_input:
            sdl2.SDL_Delay(100)
            self.ui.draw_clear()
            self.ui.draw_text(
                (self.ui.screen_width / 2, self.ui.screen_height / 2 - 20),
                f"New RomM App version available: v{self.latest_version}",
                color=color_text,
                anchor="mm",
            )
            self.ui.draw_text(
                (self.ui.screen_width / 2, self.ui.screen_height / 2 + 20),
                "Download update?",
                color=color_text,
                anchor="mm",
            )
            self.buttons_config = [
                {"key": "A", "label": "Yes", "color": color_btn_a},
                {"key": "B", "label": "No", "color": color_btn_b},
            ]
            self.draw_buttons()

            if self.input.key("A"):
                self.awaiting_input = False
                self.ui.draw_clear()
                if self.updater.download_update(self.download_url):
                    self.ui.draw_log(text_line_1="Update downloaded successfully")
                    # We need to restart here so main.py can extract the update before we've loaded anything into memory
                    os.execv(sys.executable, [sys.executable] + sys.argv)  # nosec B606
                else:
                    self.ui.draw_log(text_line_1="Update failed")
                self.ui.render_to_screen()
                sdl2.SDL_Delay(1000)
                self.status.updating.clear()
            elif self.input.key("B"):
                self.awaiting_input = False
                self.ui.draw_clear()
                self.ui.draw_log(
                    text_line_1=f"Proceeding with current version (v{self.updater.current_version})"
                )
                self.ui.render_to_screen()
                sdl2.SDL_Delay(1000)
                self.status.updating.clear()

    def _render_platforms_view(self):
        if self.status.updating.is_set():
            return

        if self.status.platforms_ready.is_set():
            self.ui.draw_platforms_list(
                self.platforms_selected_position,
                self.max_n_platforms,
                self.status.platforms,
            )
        if not self.status.platforms_ready.is_set():
            current_time = time.time()
            if current_time - self.last_spinner_update >= self.spinner_speed:
                self.last_spinner_update = current_time
                self.current_spinner_status = next(glyphs.spinner)
            self.ui.draw_log(
                text_line_1=f"{self.current_spinner_status} Fetching platforms"
            )
        elif not self.status.download_rom_ready.is_set():
            if self.status.extracting_rom:
                self.ui.draw_loader(self.status.extracted_percent, color=color_btn_b)
                self.ui.draw_log(
                    text_line_1=f"{self.status.downloading_rom_position}/{len(self.status.download_queue)} | {self.status.extracted_percent:.2f}% | Extracting {self.status.downloading_rom.name}",
                    text_line_2=f"({self.status.downloading_rom.fs_name})",
                    background=False,
                )
            elif self.status.downloading_rom:
                self.ui.draw_loader(self.status.downloaded_percent)
                self.ui.draw_log(
                    text_line_1=f"{self.status.downloading_rom_position}/{len(self.status.download_queue)} | {self.status.downloaded_percent:.2f}% | {glyphs.download} {self.status.downloading_rom.name}",
                    text_line_2=f"({self.status.downloading_rom.fs_name})",
                    background=False,
                )
        elif not self.status.valid_host:
            self.ui.draw_log(
                text_line_1=f"Error: Can't connect to host {self.api.host}",
                text_color=color_btn_a,
            )
            self.status.valid_host = True
        elif not self.status.valid_credentials:
            self.ui.draw_log(
                text_line_1="Error: Permission denied", text_color=color_btn_a
            )
            self.status.valid_credentials = True
        else:
            self.buttons_config = [
                {"key": "A", "label": "Select", "color": color_btn_a},
                {"key": "Y", "label": "Refresh", "color": color_btn_y},
                {"key": "X", "label": "Collections", "color": color_btn_x},
            ]
            self.draw_buttons()

    def _update_platforms_view(self):
        if self.input.key("A"):
            if self.status.roms_ready.is_set() and len(self.status.platforms) > 0:
                self.status.roms_ready.clear()
                self.status.roms = []
                self.status.selected_platform = self.status.platforms[
                    self.platforms_selected_position
                ]
                self.status.current_view = View.ROMS
                threading.Thread(target=self.api.fetch_roms).start()
        elif self.input.key("Y"):
            if self.status.platforms_ready.is_set():
                self.status.platforms_ready.clear()
                threading.Thread(target=self.api.fetch_platforms).start()
        elif self.input.key("X"):
            self.status.current_view = View.COLLECTIONS
        elif self.input.key("START"):
            self.status.show_contextual_menu = not self.status.show_contextual_menu
            if self.status.show_contextual_menu and len(self.status.platforms) > 0:
                self.contextual_menu_options = [
                    (
                        f"{glyphs.about} Platform info",
                        0,
                        lambda: self.ui.draw_log(
                            text_line_1=f"Platform name: {self.status.platforms[self.platforms_selected_position].display_name}"
                        ),
                    ),
                ]
            else:
                self.contextual_menu_options = []
        else:
            # Reset position if list is empty to avoid out-of-bounds
            if len(self.status.platforms) == 0:
                self.platforms_selected_position = 0
            else:
                self.platforms_selected_position = self.input.handle_navigation(
                    self.platforms_selected_position,
                    self.max_n_platforms,
                    len(self.status.platforms),
                )

    def _render_collections_view(self):
        if self.status.collections_ready.is_set():
            self.ui.draw_collections_list(
                self.collections_selected_position,
                self.max_n_collections,
                self.status.collections,
                fill=color_btn_b,
            )
        if not self.status.collections_ready.is_set():
            current_time = time.time()
            if current_time - self.last_spinner_update >= self.spinner_speed:
                self.last_spinner_update = current_time
                self.current_spinner_status = next(glyphs.spinner)
            self.ui.draw_log(
                text_line_1=f"{self.current_spinner_status} Fetching collections"
            )
        elif not self.status.download_rom_ready.is_set():
            if self.status.extracting_rom:
                self.ui.draw_loader(self.status.extracted_percent, color=color_btn_b)
                self.ui.draw_log(
                    text_line_1=f"{self.status.downloading_rom_position}/{len(self.status.download_queue)} | {self.status.extracted_percent:.2f}% | Extracting {self.status.downloading_rom.name}",
                    text_line_2=f"({self.status.downloading_rom.fs_name})",
                    background=False,
                )
            elif self.status.downloading_rom:
                self.ui.draw_loader(self.status.downloaded_percent)
                self.ui.draw_log(
                    text_line_1=f"{self.status.downloading_rom_position}/{len(self.status.download_queue)} | {self.status.downloaded_percent:.2f}% | {glyphs.download} {self.status.downloading_rom.name}",
                    text_line_2=f"({self.status.downloading_rom.fs_name})",
                    background=False,
                )
        elif not self.status.valid_host:
            self.ui.draw_log(
                text_line_1=f"Error: Can't connect to host {self.api.host}",
                text_color=color_btn_a,
            )
            self.status.valid_host = True
        elif not self.status.valid_credentials:
            self.ui.draw_log(
                text_line_1="Error: Permission denied", text_color=color_btn_a
            )
            self.status.valid_credentials = True
        else:
            self.buttons_config = [
                {"key": "A", "label": "Select", "color": color_btn_a},
                {"key": "Y", "label": "Refresh", "color": color_btn_y},
                {"key": "X", "label": "Platforms", "color": color_btn_x},
            ]
            self.draw_buttons()

    def _update_collections_view(self):
        if self.input.key("A"):
            if self.status.roms_ready.is_set() and len(self.status.collections) > 0:
                self.status.roms_ready.clear()
                self.status.roms = []
                selected_collection = self.status.collections[
                    self.collections_selected_position
                ]
                if selected_collection.virtual:
                    self.status.selected_virtual_collection = selected_collection
                else:
                    self.status.selected_collection = selected_collection
                self.status.current_view = View.ROMS
                threading.Thread(target=self.api.fetch_roms).start()
        elif self.input.key("Y"):
            if self.status.collections_ready.is_set():
                self.status.collections_ready.clear()
                threading.Thread(target=self.api.fetch_collections).start()
        elif self.input.key("X"):
            self.status.current_view = View.PLATFORMS
        elif self.input.key("START"):
            self.status.show_contextual_menu = not self.status.show_contextual_menu
            if self.status.show_contextual_menu and len(self.status.collections) > 0:
                self.contextual_menu_options = [
                    (
                        f"{glyphs.about} Collection info",
                        0,
                        lambda: self.ui.draw_log(
                            text_line_1=f"Collection name: {self.status.collections[self.collections_selected_position].name}"
                        ),
                    ),
                ]
            else:
                self.contextual_menu_options = []
        else:
            self.collections_selected_position = self.input.handle_navigation(
                self.collections_selected_position,
                self.max_n_collections,
                len(self.status.collections),
            )

    def _render_roms_view(self):
        if len(self.status.roms) == 0 and self.status.roms_ready.is_set():
            header_text = "No ROMs available"
            header_color = color_btn_a
            prepend_platform_slug = False
        elif self.status.selected_platform:
            header_text = self.status.platforms[
                self.platforms_selected_position
            ].display_name
            header_color = color_sel
            prepend_platform_slug = False
        elif self.status.selected_collection or self.status.selected_virtual_collection:
            header_text = self.status.collections[
                self.collections_selected_position
            ].name
            header_color = color_btn_b
            prepend_platform_slug = True
        else:
            header_text = "ROMs"
            header_color = color_sel
            prepend_platform_slug = False

        total_pages = (
            len(self.status.roms_to_show) + self.max_n_roms - 1
        ) // self.max_n_roms
        current_page = (self.roms_selected_position // self.max_n_roms) + 1
        header_text += f" [{current_page if total_pages > 0 else 0}/{total_pages}]"

        if len(self.status.multi_selected_roms) > 0:
            header_text += f" ({len(self.status.multi_selected_roms)} selected)"
        if self.status.current_filter == Filter.ALL:
            self.status.roms_to_show = self.status.roms
        elif self.status.current_filter == Filter.LOCAL:
            self.status.roms_to_show = [
                r for r in self.status.roms if self.fs.is_rom_in_device(r)
            ]
        elif self.status.current_filter == Filter.REMOTE:
            self.status.roms_to_show = [
                r for r in self.status.roms if not self.fs.is_rom_in_device(r)
            ]

        self.ui.draw_roms_list(
            self.roms_selected_position,
            self.max_n_roms,
            self.status.roms_to_show,
            header_text,
            header_color,
            self.status.multi_selected_roms,
            prepend_platform_slug=prepend_platform_slug,
        )

        if not self.status.roms_ready.is_set():
            current_time = time.time()
            if current_time - self.last_spinner_update >= self.spinner_speed:
                self.last_spinner_update = current_time
                self.current_spinner_status = next(glyphs.spinner)
            self.ui.draw_log(text_line_1=f"{self.current_spinner_status} Fetching roms")
        elif not self.status.download_rom_ready.is_set():
            if self.status.extracting_rom:
                self.ui.draw_loader(self.status.extracted_percent, color=color_btn_b)
                self.ui.draw_log(
                    text_line_1=f"{self.status.downloading_rom_position}/{len(self.status.download_queue)} | {self.status.extracted_percent:.2f}% | Extracting {self.status.downloading_rom.name}",
                    text_line_2=f"({self.status.downloading_rom.fs_name})",
                    background=False,
                )
            elif self.status.downloading_rom:
                self.ui.draw_loader(self.status.downloaded_percent)
                self.ui.draw_log(
                    text_line_1=f"{self.status.downloading_rom_position}/{len(self.status.download_queue)} | {self.status.downloaded_percent:.2f}% | {glyphs.download} {self.status.downloading_rom.name}",
                    text_line_2=f"({self.status.downloading_rom.fs_name})",
                    background=False,
                )
        elif not self.status.valid_host:
            self.ui.draw_log(
                text_line_1=f"Error: Can't connect to host {self.api.host}",
                text_color=color_btn_a,
            )
            self.status.valid_host = True
        elif not self.status.valid_credentials:
            self.ui.draw_log(
                text_line_1="Error: Permission denied", text_color=color_btn_a
            )
            self.status.valid_credentials = True
        else:
            self.buttons_config = [
                {"key": "A", "label": "Download", "color": color_btn_a},
                {"key": "B", "label": "Back", "color": color_btn_b},
                {"key": "Y", "label": "Refresh", "color": color_btn_y},
                {
                    "key": "X",
                    "label": f"Filter:{self.status.current_filter}",
                    "color": color_btn_x,
                },
                {
                    "key": "L1",
                    "label": (
                        "Deselect rom"
                        if (
                            len(self.status.roms_to_show) > 0
                            and self.status.roms_to_show[self.roms_selected_position]
                            in self.status.multi_selected_roms
                        )
                        else "Select rom"
                    ),
                    "color": color_btn_shoulder,
                },
                {
                    "key": "R1",
                    "label": (
                        "Deselect all"
                        if len(self.status.multi_selected_roms)
                        == len(self.status.roms_to_show)
                        else "Select all"
                    ),
                    "color": color_btn_shoulder,
                },
            ]
            self.draw_buttons()

    def _update_roms_view(self):
        if self.input.key("A"):
            if (
                self.status.roms_ready.is_set()
                and self.status.download_rom_ready.is_set()
                and len(self.status.roms_to_show) > 0
            ):
                self.status.download_rom_ready.clear()
                if len(self.status.multi_selected_roms) == 0:
                    self.status.multi_selected_roms.append(
                        self.status.roms_to_show[self.roms_selected_position]
                    )
                self.status.download_queue = self.status.multi_selected_roms
                self.status.abort_download.clear()
                threading.Thread(target=self.api.download_rom).start()
        elif self.input.key("B"):
            if self.status.selected_platform:
                self.status.current_view = View.PLATFORMS
                self.status.selected_platform = None
            elif self.status.selected_collection:
                self.status.current_view = View.COLLECTIONS
                self.status.selected_collection = None
            elif self.status.selected_virtual_collection:
                self.status.current_view = View.COLLECTIONS
                self.status.selected_virtual_collection = None
            else:
                self.status.current_view = View.PLATFORMS
            self.status.reset_roms_list()
            self.roms_selected_position = 0
            self.status.multi_selected_roms = []
        elif self.input.key("Y"):
            if self.status.roms_ready.is_set():
                self.status.roms_ready.clear()
                threading.Thread(target=self.api.fetch_roms).start()
                self.status.multi_selected_roms = []
        elif self.input.key("X"):
            self.status.current_filter = next(self.status.filters)
            self.roms_selected_position = 0
        elif self.input.key("R1"):
            if len(self.status.multi_selected_roms) == len(self.status.roms_to_show):
                self.status.multi_selected_roms = []
            else:
                self.status.multi_selected_roms = self.status.roms_to_show.copy()
        elif self.input.key("L1"):
            if (
                self.status.download_rom_ready.is_set()
                and len(self.status.roms_to_show) > 0
            ):
                selected_rom = self.status.roms_to_show[self.roms_selected_position]
                if selected_rom not in self.status.multi_selected_roms:
                    self.status.multi_selected_roms.append(selected_rom)
                else:
                    self.status.multi_selected_roms.remove(selected_rom)
        elif self.input.key("START"):
            self.status.show_contextual_menu = not self.status.show_contextual_menu
            if self.status.show_contextual_menu and len(self.status.roms_to_show) > 0:
                selected_rom = self.status.roms_to_show[self.roms_selected_position]
                self.contextual_menu_options = [
                    (
                        f"{glyphs.about} Rom info",
                        0,
                        lambda: self.ui.draw_log(
                            text_line_1=f"Rom name: {selected_rom.name}"
                        ),
                    ),
                ]

                if self.fs.is_rom_in_device(selected_rom):
                    self.contextual_menu_options.append(
                        (
                            f"{glyphs.delete} Remove from device",
                            1,
                            lambda: os.remove(
                                os.path.join(
                                    self.fs.get_platforms_storage_path(
                                        selected_rom.platform_slug
                                    ),
                                    selected_rom.fs_name,
                                )
                            ),
                        ),
                    )
            else:
                self.contextual_menu_options = []
        else:
            self.roms_selected_position = self.input.handle_navigation(
                self.roms_selected_position,
                self.max_n_roms,
                len(self.status.roms_to_show),
            )

    def _render_contextual_menu(self):
        pos = [self.ui.screen_width / 3, self.ui.screen_height / 3]
        padding = 5
        width = 200
        n_options = len(self.contextual_menu_options)
        option_height = 32
        gap = 3

        self.ui.draw_menu_background(pos, width, n_options, option_height, gap, padding)

        n_options = len(self.contextual_menu_options)
        if n_options == 0:  # Avoid division by zero when menu is empty
            return

        for i, option in enumerate(self.contextual_menu_options):
            is_selected = i == (self.contextual_menu_selected_position % n_options)
            self.ui.row_list(
                option[0],
                (pos[0] + padding, pos[1] + padding + (i * (option_height + gap))),
                width,
                option_height,
                is_selected,
            )

    def _update_contextual_menu(self):
        if self.input.key("A"):
            if len(self.contextual_menu_options) > 0:
                self.contextual_menu_options[self.contextual_menu_selected_position][
                    2
                ]()
                self.status.show_contextual_menu = False
        elif self.input.key("B"):
            self.status.show_contextual_menu = False
            self.contextual_menu_options = []
        else:
            self.contextual_menu_selected_position = self.input.handle_navigation(
                self.contextual_menu_selected_position,
                len(self.contextual_menu_options),
                len(self.contextual_menu_options),
            )

    def _render_start_menu(self):
        pos = [self.ui.screen_width / 3, self.ui.screen_height / 3]
        padding = 5
        width = 200
        n_selectable_options = 3 if self.fs._sd2_roms_storage_path else 2
        option_height = 24
        gap = 3
        title = "Main menu"
        title_x_adjustment = 35
        version_x_adjustment = 50 / 6 * (len(version) + 2)
        version_height = 20
        self.ui.draw_menu_background(
            pos,
            width,
            len(self.start_menu_options),
            option_height,
            gap,
            padding,
            extra_top_offset=version_height,
            extra_bottom_offset=version_height,
        )

        selected_position = self.start_menu_selected_position % n_selectable_options
        for i, option in enumerate(self.start_menu_options):
            self.ui.row_list(
                text=option[0],
                position=(
                    pos[0] + padding,
                    pos[1] + padding + (i * (option_height + gap)),
                ),
                width=width,
                height=option_height,
                selected=selected_position == option[1],
                color=color_text if option[1] > -1 else color_menu_bg,
            )

        self.ui.draw_text(
            (
                pos[0] + width - version_x_adjustment,
                pos[1] + padding + len(self.start_menu_options) * (option_height + gap),
            ),
            f"v{version}",
        )
        self.ui.draw_text(
            (
                pos[0] + width / 2 - title_x_adjustment,
                pos[1] - option_height + version_height - padding,
            ),
            title,
        )

    def _update_start_menu(self):
        if self.input.key("A"):
            if self.start_menu_selected_position == self.start_menu_options[0][1]:
                self.status.abort_download.set()
                self.status.show_start_menu = False
            elif self.start_menu_selected_position == self.start_menu_options[1][1]:
                self.fs.switch_sd_storage()
                self.status.show_start_menu = False
            elif self.start_menu_selected_position == self.start_menu_options[2][1]:
                self.running = False
                self.status.show_start_menu = False
        elif self.input.key("B"):
            self.status.show_start_menu = not self.status.show_start_menu
        else:
            n_selectable_options = 3 if self.fs._sd2_roms_storage_path else 2
            self.start_menu_selected_position = self.input.handle_navigation(
                self.start_menu_selected_position,
                n_selectable_options,
                n_selectable_options,
            )

    def _update_common(self):
        if (
            self.input.key("MENUF") or self.input.key("SELECT")
        ) and not self.status.show_contextual_menu:
            self.status.show_start_menu = not self.status.show_start_menu
        if self.input.key("START") and not self.status.show_start_menu:
            self.status.show_contextual_menu = not self.status.show_contextual_menu

    def _monitor_input(self):
        while self.running:
            events = sdl2.ext.get_events()
            for event in events:
                self.input.check_event(event)
                if event.type == sdl2.SDL_QUIT:
                    self.running = False

    def start(self):
        threading.Thread(target=self._monitor_input, daemon=True).start()
        self._check_for_updates()
        if not self.status.updating.is_set():
            self._render_platforms_view()
        threading.Thread(target=self.api.fetch_platforms).start()
        threading.Thread(target=self.api.fetch_collections).start()
        threading.Thread(target=self.api.fetch_me).start()

    def update(self):
        self.ui.draw_clear()

        if self.awaiting_input:
            self._handle_update_confirmation()
            return

        if self.status.updating.is_set():
            return

        if self.status.me_ready.is_set():
            self.ui.draw_header(self.api.host, self.api.username)

        if not self.status.valid_host:
            if self.input.key("Y"):
                if self.status.platforms_ready.is_set():
                    self.status.platforms_ready.clear()
                    threading.Thread(target=self.api.fetch_platforms).start()
            self.ui.button_circle((20, 460), "Y", "Refresh", color=color_btn_y)
            self.ui.draw_text(
                (self.ui.screen_width / 2, self.ui.screen_height / 2),
                f"Error: Can't connect to host\n{self.api.host}",
                color=color_btn_a,
                anchor="mm",
            )
        elif not self.status.valid_credentials:
            if self.input.key("Y"):
                if self.status.platforms_ready.is_set():
                    self.status.platforms_ready.clear()
                    threading.Thread(target=self.api.fetch_platforms).start()
            self.ui.button_circle((20, 460), "Y", "Refresh", color=color_btn_y)
            self.ui.draw_text(
                (self.ui.screen_width / 2, self.ui.screen_height / 2),
                "Error: Permission denied",
                color=color_btn_a,
                anchor="mm",
            )
        else:
            if self.status.current_view == View.PLATFORMS:
                self._render_platforms_view()
                if (
                    not self.status.show_start_menu
                    and not self.status.show_contextual_menu
                ):
                    self._update_platforms_view()
            elif self.status.current_view == View.COLLECTIONS:
                self._render_collections_view()
                if (
                    not self.status.show_start_menu
                    and not self.status.show_contextual_menu
                ):
                    self._update_collections_view()
            elif self.status.current_view == View.ROMS:
                self._render_roms_view()
                if (
                    not self.status.show_start_menu
                    and not self.status.show_contextual_menu
                ):
                    self._update_roms_view()
            else:
                self._render_platforms_view()
                if (
                    not self.status.show_start_menu
                    and not self.status.show_contextual_menu
                ):
                    self._update_platforms_view()
        # Render start menu
        if self.status.show_start_menu:
            self._render_start_menu()
            self._update_start_menu()
        elif self.status.show_contextual_menu:
            self._render_contextual_menu()
            self._update_contextual_menu()

        self._update_common()
