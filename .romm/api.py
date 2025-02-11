import base64
import json
import math
import os
from collections import namedtuple
from os import makedirs
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from filesystem import MUOS_SUPPORTED_PLATFORMS, Filesystem
from PIL import Image
from status import Status, View

# Load .env file from one folder above
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

Rom = namedtuple(
    "Rom",
    [
        "id",
        "name",
        "file_name",
        "platform_slug",
        "file_extension",
        "file_size",
        "file_size_bytes",
    ],
)
Firmware = namedtuple("Firmware", ["id", "file_name", "is_verified", "file_extension", "file_size", "file_size_bytes"])
Collection = namedtuple("Collection", ["id", "name", "rom_count"])
Platform = namedtuple("Platform", ["id", "display_name", "slug", "rom_count"])

#     full_path: str
#     is_verified: bool
#     crc_hash: str
#     md5_hash: str
#     sha1_hash: str

class API:

    def __init__(self):
        self.host = os.getenv("HOST", "")
        self.__platforms_endpoint = "api/platforms"
        self.__platform_icon_url = "assets/platforms"
        self.__collections_endpoint = "api/collections"
        self.__roms_endpoint = "api/roms"
        self.__firmware_endpoint = "api/firmware"
        self.__user_me_endpoint = "api/users/me"
        self.__user_profile_picture_url = "assets/romm/assets"
        self.username = os.getenv("USERNAME", "")
        self.__password = os.getenv("PASSWORD", "")
        self.__credentials = f"{self.username}:{self.__password}"
        self.__auth_token = base64.b64encode(self.__credentials.encode("utf-8")).decode(
            "utf-8"
        )
        self.__headers = {"Authorization": f"Basic {self.__auth_token}"}
        self.__exclude_platforms = set(os.getenv("EXCLUDE_PLATFORMS") or [])
        self.__include_collections = set(os.getenv("INCLUDE_COLLECTIONS") or [])
        self.__exclude_collections = set(os.getenv("EXCLUDE_COLLECTIONS") or [])
        self.__status = Status()
        self.__fs = Filesystem()

    @staticmethod
    def _human_readable_size(size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return (s, size_name[i])

    def _fetch_user_profile_picture(self, avatar_path):
        file_extension = avatar_path.split(".")[-1]
        try:
            request = Request(
                f"{self.host}/{self.__user_profile_picture_url}/{avatar_path}",
                headers=self.__headers,
            )
        except ValueError as e:
            print(e)
            self.__status.valid_host = False
            self.__status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self.__status.valid_host = False
                self.__status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            print(e)
            if e.code == 403:
                self.__status.valid_host = True
                self.__status.valid_credentials = False
                return
            else:
                raise
        except URLError as e:
            print(e)
            self.__status.valid_host = False
            self.__status.valid_credentials = False
            return
        if not os.path.exists(self.__fs.resources_path):
            makedirs(self.__fs.resources_path)
        self.__status.profile_pic_path = (
            f"{self.__fs.resources_path}/{self.username}.{file_extension}"
        )
        with open(self.__status.profile_pic_path, "wb") as f:
            f.write(response.read())
        icon = Image.open(self.__status.profile_pic_path)
        icon = icon.resize((30, 30))
        icon.save(self.__status.profile_pic_path)
        self.__status.valid_host = True
        self.__status.valid_credentials = True

    def fetch_me(self):
        try:
            request = Request(
                f"{self.host}/{self.__user_me_endpoint}", headers=self.__headers
            )
        except ValueError as e:
            print(e)
            self.__status.valid_host = False
            self.__status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self.__status.valid_host = False
                self.__status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            print(e)
            if e.code == 403:
                self.__status.valid_host = True
                self.__status.valid_credentials = False
                return
            else:
                raise
        except URLError as e:
            print(e)
            self.__status.valid_host = False
            self.__status.valid_credentials = False
            return
        me = json.loads(response.read().decode("utf-8"))
        self.__status.me = me
        if me["avatar_path"]:
            self._fetch_user_profile_picture(me["avatar_path"])
        self.__status.me_ready.set()

    def _fetch_platform_icon(self, platform_slug):
        try:
            request = Request(
                f"{self.host}/{self.__platform_icon_url}/{platform_slug}.ico",
                headers=self.__headers,
            )
        except ValueError as e:
            print(e)
            self.__status.valid_host = False
            self.__status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self.__status.valid_host = False
                self.__status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            print(e)
            if e.code == 403:
                self.__status.valid_host = True
                self.__status.valid_credentials = False
                return
            else:
                raise
        except URLError as e:
            print(e)
            self.__status.valid_host = False
            self.__status.valid_credentials = False
            return
        if not os.path.exists(self.__fs.resources_path):
            makedirs(self.__fs.resources_path)
        with open(f"{self.__fs.resources_path}/{platform_slug}.ico", "wb") as f:
            f.write(response.read())
        icon = Image.open(f"{self.__fs.resources_path}/{platform_slug}.ico")
        icon = icon.resize((30, 30))
        icon.save(f"{self.__fs.resources_path}/{platform_slug}.ico")
        self.__status.valid_host = True
        self.__status.valid_credentials = True

    def fetch_platforms(self):
        try:
            request = Request(
                f"{self.host}/{self.__platforms_endpoint}", headers=self.__headers
            )
        except ValueError:
            self.__status.platforms = []
            self.__status.valid_host = False
            self.__status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self.__status.platforms = []
                self.__status.valid_host = False
                self.__status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            if e.code == 403:
                self.__status.platforms = []
                self.__status.valid_host = True
                self.__status.valid_credentials = False
                return
            else:
                raise
        except URLError:
            self.__status.platforms = []
            self.__status.valid_host = False
            self.__status.valid_credentials = False
            return
        platforms = json.loads(response.read().decode("utf-8"))
        __platforms = []
        for platform in platforms:
            if platform["rom_count"] > 0:
                if (
                    platform["slug"] not in MUOS_SUPPORTED_PLATFORMS
                    or platform["slug"] in self.__exclude_platforms
                ):
                    continue
                __platforms.append(
                    Platform(
                        id=platform["id"],
                        display_name=platform["display_name"],
                        rom_count=platform["rom_count"],
                        slug=platform["slug"],
                    )
                )
                if not os.path.exists(
                    f"{self.__fs.resources_path}/{platform['slug']}.ico"
                ):
                    self._fetch_platform_icon(platform["slug"])
        __platforms.sort(key=lambda platform: platform.display_name)
        self.__status.platforms = __platforms
        self.__status.valid_host = True
        self.__status.valid_credentials = True
        self.__status.platforms_ready.set()

    def fetch_collections(self):
        try:
            request = Request(
                f"{self.host}/{self.__collections_endpoint}", headers=self.__headers
            )
        except ValueError:
            self.__status.collections = []
            self.__status.valid_host = False
            self.__status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self.__status.collections = []
                self.__status.valid_host = False
                self.__status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            if e.code == 403:
                self.__status.collections = []
                self.__status.valid_host = True
                self.__status.valid_credentials = False
                return
            else:
                raise
        except URLError:
            self.__status.collections = []
            self.__status.valid_host = False
            self.__status.valid_credentials = False
            return
        collections = json.loads(response.read().decode("utf-8"))
        __collections = []
        for collection in collections:
            if collection["rom_count"] > 0:
                if self.__include_collections:
                    if collection["name"] not in self.__include_collections:
                        continue
                elif self.__exclude_collections:
                    if collection["name"] in self.__exclude_collections:
                        continue
                __collections.append(
                    Collection(
                        id=collection["id"],
                        name=collection["name"],
                        rom_count=collection["rom_count"],
                    )
                )
        __collections.sort(key=lambda collection: collection.name)
        self.__status.collections = __collections
        self.__status.valid_host = True
        self.__status.valid_credentials = True
        self.__status.collections_ready.set()

    def fetch_firmware(self):
        if not self.__status.selected_platform:
            return

        try:
            request  = Request(
                f"{self.host}/{self.__firmware_endpoint}?platform_id={self.__status.selected_platform.id}",
                headers=self.__headers
            )
        except ValueError:
            self.__status.firmware = []
            self.__status.valid_host = False
            self.__status.valid_credentials = False
            return

        try:
            if request.type not in ("http", "https"):
                self.__status.firmware = []
                self.__status.valid_host = False
                self.__status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            if e.code == 403:
                self.__status.firmware = []
                self.__status.valid_host = True
                self.__status.valid_credentials = False
                return
            else:
                raise
        except URLError:
            self.__status.firmware = []
            self.__status.valid_host = False
            self.__status.valid_credentials = False
            return

        firmware = json.loads(response.read().decode("utf-8"))
        __firmware = [
            Firmware(
                id=f["id"],
                file_name=f["file_name"],
                is_verified=f["is_verified"],
                file_extension=f["file_extension"],
                file_size=self._human_readable_size(f["file_size_bytes"]),
                file_size_bytes=f["file_size_bytes"],
            )
            for f in firmware
        ]
        __firmware.sort(key=lambda f: f.file_name)
        self.__status.firmware = __firmware
        self.__status.valid_host = True
        self.__status.valid_credentials = True
        self.__status.firmware_ready.set()

    def download_firmware(self):
        self.__status.download_queue.sort(key=lambda rom: rom.name)
        for i, rom in enumerate(self.__status.download_queue):
            self.__status.downloading_rom = rom
            self.__status.downloading_rom_position = i + 1
            dest_path = os.path.join(
                self.__fs.get_sd_storage_platform_path(rom.platform_slug),
                rom.file_name,
            )
            url = f"{self.host}/{self.__roms_endpoint}/{rom.id}/content/{quote(rom.file_name)}"
            makedirs(os.path.dirname(dest_path), exist_ok=True)

            try:
                request = Request(url, headers=self.__headers)
            except ValueError:
                self._reset_download_status()
                return
            try:
                if request.type not in ("http", "https"):
                    self._reset_download_status()
                    return
                with urlopen(request) as response, open(  # trunk-ignore(bandit/B310)
                    dest_path, "wb"
                ) as out_file:
                    self.__status.total_downloaded_bytes = 0
                    chunk_size = 1024
                    print(
                        f"Can Downloading: {not self.__status.abort_download.is_set()}"
                    )
                    while True:
                        if not self.__status.abort_download.is_set():
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            out_file.write(chunk)
                            self.__status.valid_host = True
                            self.__status.valid_credentials = True
                            self.__status.total_downloaded_bytes += len(chunk)
                            self.__status.downloaded_percent = (
                                self.__status.total_downloaded_bytes
                                / self.__status.downloading_rom.file_size_bytes
                            ) * 100
                        else:
                            self._reset_download_status(True, True)
                            os.remove(dest_path)
                            return
            except HTTPError as e:
                if e.code == 403:
                    self._reset_download_status(valid_host=True)
                    return
                else:
                    raise
            except URLError:
                self._reset_download_status(valid_host=True)
                return
        # End of download
        self._reset_download_status(valid_host=True, valid_credentials=True)

    def fetch_roms(self):
        if self.__status.selected_platform:
            view = View.PLATFORMS
            id = self.__status.selected_platform.id
        elif self.__status.selected_collection:
            view = View.COLLECTIONS
            id = self.__status.selected_collection.id

        try:
            request = Request(
                f"{self.host}/{self.__roms_endpoint}?{view}_id={id}&order_by=name&order_dir=asc",
                headers=self.__headers,
            )
        except ValueError:
            self.__status.roms = []
            self.__status.valid_host = False
            self.__status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self.__status.roms = []
                self.__status.valid_host = False
                self.__status.valid_credentials = False
                return
            response = urlopen(request, timeout=1800)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            if e.code == 403:
                self.__status.roms = []
                self.__status.valid_host = True
                self.__status.valid_credentials = False
                return
            else:
                raise
        except URLError:
            self.__status.roms = []
            self.__status.valid_host = False
            self.__status.valid_credentials = False
            return
        roms = json.loads(response.read().decode("utf-8"))
        __roms = [
            Rom(
                id=rom["id"],
                name=rom["name"],
                file_name=rom["file_name"],
                platform_slug=rom["platform_slug"],
                file_extension=rom["file_extension"],
                file_size=self._human_readable_size(rom["file_size_bytes"]),
                file_size_bytes=rom["file_size_bytes"],
            )
            for rom in roms
            if rom["platform_slug"] in MUOS_SUPPORTED_PLATFORMS
        ]
        __roms.sort(key=lambda rom: rom.name)
        self.__status.roms = __roms
        self.__status.valid_host = True
        self.__status.valid_credentials = True
        self.__status.roms_ready.set()

    def _reset_download_status(self, valid_host=False, valid_credentials=False):
        self.__status.total_downloaded_bytes = 0
        self.__status.downloaded_percent = 0
        self.__status.valid_host = valid_host
        self.__status.valid_credentials = valid_credentials
        self.__status.downloading_rom = None
        self.__status.multi_selected_roms = []
        self.__status.download_queue = []
        self.__status.download_rom_ready.set()
        self.__status.abort_download.set()

    def download_rom(self):
        self.__status.download_queue.sort(key=lambda rom: rom.name)
        for i, rom in enumerate(self.__status.download_queue):
            self.__status.downloading_rom = rom
            self.__status.downloading_rom_position = i + 1
            dest_path = os.path.join(
                self.__fs.get_sd_storage_platform_path(rom.platform_slug),
                rom.file_name,
            )
            url = f"{self.host}/{self.__roms_endpoint}/{rom.id}/content/{quote(rom.file_name)}"
            makedirs(os.path.dirname(dest_path), exist_ok=True)

            try:
                request = Request(url, headers=self.__headers)
            except ValueError:
                self._reset_download_status()
                return
            try:
                if request.type not in ("http", "https"):
                    self._reset_download_status()
                    return
                with urlopen(request) as response, open(  # trunk-ignore(bandit/B310)
                    dest_path, "wb"
                ) as out_file:
                    self.__status.total_downloaded_bytes = 0
                    chunk_size = 1024
                    print(
                        f"Can Downloading: {not self.__status.abort_download.is_set()}"
                    )
                    while True:
                        if not self.__status.abort_download.is_set():
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            out_file.write(chunk)
                            self.__status.valid_host = True
                            self.__status.valid_credentials = True
                            self.__status.total_downloaded_bytes += len(chunk)
                            self.__status.downloaded_percent = (
                                self.__status.total_downloaded_bytes
                                / self.__status.downloading_rom.file_size_bytes
                            ) * 100
                        else:
                            self._reset_download_status(True, True)
                            os.remove(dest_path)
                            return
            except HTTPError as e:
                if e.code == 403:
                    self._reset_download_status(valid_host=True)
                    return
                else:
                    raise
            except URLError:
                self._reset_download_status(valid_host=True)
                return
        # End of download
        self._reset_download_status(valid_host=True, valid_credentials=True)
