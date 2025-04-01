import os
import threading
import time
from typing import Any, Tuple

import sdl2
import sdl2.ext
from __version__ import version
from api import API
from filesystem import Filesystem
from glyps import glyphs
from input import Input
from status import Filter, StartMenuOptions, Status, View
from ui import (
    UserInterface,
    color_blue,
    color_gray_1,
    color_green,
    color_red,
    color_violet,
    color_yellow,
)


class RomM:
    running: bool = True
    spinner_speed = 0.05
    start_menu_options = [
        value
        for name, value in StartMenuOptions.__dict__.items()
        if not name.startswith("_")
    ]

    def __init__(self) -> None:
        self.api = API()
        self.fs = Filesystem()
        self.input = Input()
        self.status = Status()
        self.ui = UserInterface()

        self.contextual_menu_options: list[Tuple[str, int, Any]] = []
        self.start_menu_selected_position = 0
        self.contextual_menu_selected_position = 0
        self.platforms_selected_position = 0
        self.collections_selected_position = 0
        self.roms_selected_position = 0

        self.max_n_platforms = 10
        self.max_n_collections = 10
        self.max_n_roms = 10

        self.last_spinner_update = time.time()
        self.current_spinner_status = next(glyphs.spinner)

    def _render_platforms_view(self):
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
                self.ui.draw_loader(self.status.extracted_percent, color=color_yellow)
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
                text_color=color_red,
            )
            self.status.valid_host = True
        elif not self.status.valid_credentials:
            self.ui.draw_log(
                text_line_1="Error: Permission denied", text_color=color_red
            )
            self.status.valid_credentials = True
        else:
            self.ui.button_circle((20, 460), "A", "Select", color=color_red)
            self.ui.button_circle((123, 460), "Y", "Refresh", color=color_green)
            self.ui.button_circle(
                (233, 460),
                "X",
                (
                    "Collections"
                    if self.status.current_view == View.PLATFORMS
                    else "Platforms"
                ),
                color=color_blue,
            )

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
                fill=color_yellow,
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
                self.ui.draw_loader(self.status.extracted_percent, color=color_yellow)
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
                text_color=color_red,
            )
            self.status.valid_host = True
        elif not self.status.valid_credentials:
            self.ui.draw_log(
                text_line_1="Error: Permission denied", text_color=color_red
            )
            self.status.valid_credentials = True
        else:
            self.ui.button_circle((20, 460), "A", "Select", color=color_red)
            self.ui.button_circle((123, 460), "Y", "Refresh", color=color_green)
            self.ui.button_circle(
                (233, 460),
                "X",
                (
                    "Collections"
                    if self.status.current_view == View.PLATFORMS
                    else "Platforms"
                ),
                color=color_blue,
            )

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
            if self.status.show_contextual_menu:
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
            self.collections_selected_position = self.input.handle_navigation(
                self.collections_selected_position,
                self.max_n_collections,
                len(self.status.collections),
            )

    def _render_roms_view(self):
        if self.status.selected_platform:
            header_text = self.status.platforms[
                self.platforms_selected_position
            ].display_name
            header_color = color_violet
            prepend_platform_slug = False
        elif self.status.selected_collection or self.status.selected_virtual_collection:
            header_text = self.status.collections[
                self.collections_selected_position
            ].name
            header_color = color_yellow
            prepend_platform_slug = True
        total_pages = (
            len(self.status.roms_to_show) + self.max_n_roms - 1
        ) // self.max_n_roms
        current_page = (self.roms_selected_position // self.max_n_roms) + 1
        header_text += f" [{current_page if total_pages > 0 else 0}/{total_pages}]"
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
                self.ui.draw_loader(self.status.extracted_percent, color=color_yellow)
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
                text_color=color_red,
            )
            self.status.valid_host = True
        elif not self.status.valid_credentials:
            self.ui.draw_log(
                text_line_1="Error: Permission denied", text_color=color_red
            )
            self.status.valid_credentials = True
        else:
            self.ui.button_circle((20, 460), "A", "Download", color=color_red)
            self.ui.button_circle((135, 460), "B", "Back", color=color_yellow)
            self.ui.button_circle((215, 460), "Y", "Refresh", color=color_green)
            self.ui.button_circle(
                (320, 460),
                "X",
                f"Filter: {self.status.current_filter}",
                color=color_blue,
            )
            self.ui.button_circle(
                (435 + (len(self.status.current_filter) * 9), 460),
                "R1",
                (
                    "Deselect all"
                    if len(self.status.multi_selected_roms) > 0
                    and len(self.status.multi_selected_roms)
                    >= len(self.status.roms_to_show)
                    else "Select all"
                ),
                color=color_gray_1,
            )

    def _update_roms_view(self):
        if self.input.key("A"):
            if (
                self.status.roms_ready.is_set()
                and self.status.download_rom_ready.is_set()
            ):
                self.status.download_rom_ready.clear()
                # If no game is "multi-selected" the current game is added to the download list
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
                self.status.selected_platform = None
                self.status.selected_collection = None
                self.status.selected_virtual_collection = None
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
        elif self.input.key("SELECT"):
            if self.status.download_rom_ready.is_set():
                if (
                    self.status.roms_to_show[self.roms_selected_position]
                    not in self.status.multi_selected_roms
                ):
                    self.status.multi_selected_roms.append(
                        self.status.roms_to_show[self.roms_selected_position]
                    )
                else:
                    self.status.multi_selected_roms.remove(
                        self.status.roms_to_show[self.roms_selected_position]
                    )
        elif self.input.key("START"):
            self.status.show_contextual_menu = not self.status.show_contextual_menu
            if self.status.show_contextual_menu:
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
                is_in_device = os.path.exists(
                    os.path.join(
                        self.fs.get_storage_platform_path(selected_rom.platform_slug),
                        selected_rom.fs_name,
                    )
                )
                if is_in_device:
                    self.contextual_menu_options.append(
                        (
                            f"{glyphs.delete} Remove from device",
                            1,
                            lambda: os.remove(
                                os.path.join(
                                    self.fs.get_storage_platform_path(
                                        self.status.roms_to_show[
                                            self.roms_selected_position
                                        ].platform_slug
                                    ),
                                    self.status.roms_to_show[
                                        self.roms_selected_position
                                    ].fs_name,
                                )
                            ),
                        ),
                    )
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
        if self.status.current_view == View.PLATFORMS:
            self.ui.draw_menu_background(
                pos,
                width,
                n_options,
                option_height,
                gap,
                padding,
            )
        elif self.status.current_view == View.COLLECTIONS:
            self.ui.draw_menu_background(
                pos, width, n_options, option_height, gap, padding
            )
        elif self.status.current_view == View.ROMS:
            self.ui.draw_menu_background(
                pos, width, n_options, option_height, gap, padding
            )
        else:
            self.ui.draw_menu_background(
                pos, width, n_options, option_height, gap, padding
            )
        n_options = len(self.contextual_menu_options)
        if n_options == 0:  # Avoid division by zero when menu is empty
            return
        start_idx = int(self.contextual_menu_selected_position / n_options) * n_options
        end_idx = start_idx + n_options
        for i, option in enumerate(self.contextual_menu_options[start_idx:end_idx]):
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
            self.contextual_menu_options[self.contextual_menu_selected_position][2]()
            self.status.show_contextual_menu = False
        elif self.input.key("B"):
            self.status.show_contextual_menu = not self.status.show_contextual_menu
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
        n_options = len(self.start_menu_options)
        option_height = 32
        gap = 3
        title = "Main menu"
        title_x_adjustement = 35
        version_x_adjustement = 50 / 6 * (len(version) + 2)
        version_height = 20
        self.ui.draw_menu_background(
            pos,
            width,
            n_options,
            option_height,
            gap,
            padding,
            extra_top_offset=version_height,
            extra_bottom_offset=version_height,
        )
        start_idx = int(self.start_menu_selected_position / n_options) * n_options
        end_idx = start_idx + n_options
        for i, option in enumerate(self.start_menu_options[start_idx:end_idx]):
            is_selected = i == (self.start_menu_selected_position % n_options)
            self.ui.row_list(
                option[0],
                (pos[0] + padding, pos[1] + padding + (i * (option_height + gap))),
                width,
                option_height,
                is_selected,
            )
        self.ui.draw_text(
            (
                pos[0] + width - version_x_adjustement,
                pos[1] + padding + len(self.start_menu_options) * (option_height + gap),
            ),
            f"v{version}",
        )
        self.ui.draw_text(
            (
                pos[0] + width / 2 - title_x_adjustement,
                pos[1] - option_height + version_height - padding,
            ),
            title,
        )

    def _update_start_menu(self):
        if self.input.key("A"):
            if self.start_menu_selected_position == StartMenuOptions.ABORT_DOWNLOAD[1]:
                self.status.abort_download.set()
                self.status.show_start_menu = False
            # SD switching temporarily disabled
            # elif self.start_menu_selected_position == StartMenuOptions.SD_SWITCH[1]:
            # current = self.fs.get_sd_storage()
            # self.fs.switch_sd_storage()
            # new = self.fs.get_sd_storage()
            # if new == current:
            # self.ui.draw_log(
            # text_line_1=f"Error: Couldn't find path {self.fs.get_sd2_storage_path()}",
            # text_color=color_red,
            # )
            # else:
            # self.ui.draw_log(
            # text_line_1=f"Set download path to SD {self.fs.get_sd_storage()}: {self.fs.get_sd_storage_path()}",
            # text_color=color_green,
            # )
            elif self.start_menu_selected_position == StartMenuOptions.EXIT[1]:
                self.running = False
        elif self.input.key("B"):
            self.status.show_start_menu = not self.status.show_start_menu
        else:
            self.start_menu_selected_position = self.input.handle_navigation(
                self.start_menu_selected_position,
                len(self.start_menu_options),
                len(self.start_menu_options),
            )

    def _update_common(self):
        if self.input.key("MENUF") and not self.status.show_contextual_menu:
            self.status.show_start_menu = not self.status.show_start_menu
        if self.input.key("START") and not self.status.show_start_menu:
            self.status.show_contextual_menu = not self.status.show_contextual_menu

    def _monitor_input(self):
        while self.running:
            events = sdl2.ext.get_events()
            for event in events:
                self.input.check(event)
                if event.type == sdl2.SDL_QUIT:
                    self.running = False

            sdl2.SDL_Delay(1)  # Delay to prevent high CPU usage

    def start(self):
        self._render_platforms_view()
        threading.Thread(target=self.api.fetch_platforms).start()
        threading.Thread(target=self.api.fetch_collections).start()
        threading.Thread(target=self.api.fetch_me).start()
        threading.Thread(target=self._monitor_input).start()

    def update(self):
        self.ui.draw_clear()

        if self.status.me_ready.is_set():
            self.ui.draw_header(self.api.host, self.api.username)

        if not self.status.valid_host:
            if self.input.key("Y"):
                if self.status.platforms_ready.is_set():
                    self.status.platforms_ready.clear()
                    threading.Thread(target=self.api.fetch_platforms).start()
            self.ui.button_circle((20, 460), "Y", "Refresh", color=color_green)
            self.ui.draw_text(
                (self.ui.screen_width / 2, self.ui.screen_height / 2),
                f"Error: Can't connect to host\n{self.api.host}",
                color=color_red,
                anchor="mm",
            )
        elif not self.status.valid_credentials:
            if self.input.key("Y"):
                if self.status.platforms_ready.is_set():
                    self.status.platforms_ready.clear()
                    threading.Thread(target=self.api.fetch_platforms).start()
            self.ui.button_circle((20, 460), "Y", "Refresh", color=color_green)
            self.ui.draw_text(
                (self.ui.screen_width / 2, self.ui.screen_height / 2),
                "Error: Permission denied",
                color=color_red,
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
