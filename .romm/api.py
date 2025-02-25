import base64
import json
import math
import os
import zipfile
from typing import Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from filesystem import MUOS_SUPPORTED_PLATFORMS, Filesystem
from models import Collection, Platform, Rom
from PIL import Image
from status import Status, View

# Load .env file from one folder above
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


class API:
    _platforms_endpoint = "api/platforms"
    _platform_icon_url = "assets/platforms"
    _collections_endpoint = "api/collections"
    _roms_endpoint = "api/roms"
    _user_me_endpoint = "api/users/me"
    _user_profile_picture_url = "assets/romm/assets"

    def __init__(self):
        self.host = os.getenv("HOST", "")
        self.username = os.getenv("USERNAME", "")
        self.password = os.getenv("PASSWORD", "")
        self._credentials = f"{self.username}:{self.password}"
        self._auth_token = base64.b64encode(self._credentials.encode("utf-8")).decode(
            "utf-8"
        )
        self._headers = {"Authorization": f"Basic {self._auth_token}"}
        self._exclude_platforms = set(os.getenv("EXCLUDE_PLATFORMS") or [])
        self._include_collections = set(os.getenv("INCLUDE_COLLECTIONS") or [])
        self._exclude_collections = set(os.getenv("EXCLUDE_COLLECTIONS") or [])
        self._status = Status()
        self._file_system = Filesystem()

    @staticmethod
    def _human_readable_size(size_bytes: int) -> Tuple[float, str]:
        if size_bytes == 0:
            return 0, "B"
        size_name = ("B", "KB", "MB", "GB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return (s, size_name[i])

    def _fetch_user_profile_picture(self, avatar_path: str) -> None:
        fs_extension = avatar_path.split(".")[-1]
        try:
            request = Request(
                f"{self.host}/{self._user_profile_picture_url}/{avatar_path}",
                headers=self._headers,
            )
        except ValueError as e:
            print(e)
            self._status.valid_host = False
            self._status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self._status.valid_host = False
                self._status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            print(e)
            if e.code == 403:
                self._status.valid_host = True
                self._status.valid_credentials = False
                return
            else:
                raise
        except URLError as e:
            print(e)
            self._status.valid_host = False
            self._status.valid_credentials = False
            return
        if not os.path.exists(self._file_system.resources_path):
            os.makedirs(self._file_system.resources_path)
        self._status.profile_pic_path = (
            f"{self._file_system.resources_path}/{self.username}.{fs_extension}"
        )
        with open(self._status.profile_pic_path, "wb") as f:
            f.write(response.read())
        icon = Image.open(self._status.profile_pic_path)
        icon = icon.resize((26, 26))
        icon.save(self._status.profile_pic_path)
        self._status.valid_host = True
        self._status.valid_credentials = True

    def fetch_me(self) -> None:
        try:
            request = Request(
                f"{self.host}/{self._user_me_endpoint}", headers=self._headers
            )
        except ValueError as e:
            print(e)
            self._status.valid_host = False
            self._status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self._status.valid_host = False
                self._status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            print(e)
            if e.code == 403:
                self._status.valid_host = True
                self._status.valid_credentials = False
                return
            else:
                raise
        except URLError as e:
            print(e)
            self._status.valid_host = False
            self._status.valid_credentials = False
            return
        me = json.loads(response.read().decode("utf-8"))
        self._status.me = me
        if me["avatar_path"]:
            self._fetch_user_profile_picture(me["avatar_path"])
        self._status.me_ready.set()

    def _fetch_platform_icon(self, platform_slug) -> None:
        try:
            request = Request(
                f"{self.host}/{self._platform_icon_url}/{platform_slug}.ico",
                headers=self._headers,
            )
        except ValueError as e:
            print(e)
            self._status.valid_host = False
            self._status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self._status.valid_host = False
                self._status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            print(e)
            if e.code == 403:
                self._status.valid_host = True
                self._status.valid_credentials = False
                return
            else:
                raise
        except URLError as e:
            print(e)
            self._status.valid_host = False
            self._status.valid_credentials = False
            return
        if not os.path.exists(self._file_system.resources_path):
            os.makedirs(self._file_system.resources_path)
        with open(f"{self._file_system.resources_path}/{platform_slug}.ico", "wb") as f:
            f.write(response.read())
        icon = Image.open(f"{self._file_system.resources_path}/{platform_slug}.ico")
        icon = icon.resize((30, 30))
        icon.save(f"{self._file_system.resources_path}/{platform_slug}.ico")
        self._status.valid_host = True
        self._status.valid_credentials = True

    def fetch_platforms(self) -> None:
        try:
            request = Request(
                f"{self.host}/{self._platforms_endpoint}", headers=self._headers
            )
        except ValueError:
            self._status.platforms = []
            self._status.valid_host = False
            self._status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self._status.platforms = []
                self._status.valid_host = False
                self._status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            if e.code == 403:
                self._status.platforms = []
                self._status.valid_host = True
                self._status.valid_credentials = False
                return
            else:
                raise
        except URLError:
            self._status.platforms = []
            self._status.valid_host = False
            self._status.valid_credentials = False
            return
        platforms = json.loads(response.read().decode("utf-8"))
        if isinstance(platforms, dict):
            platforms = platforms["items"]
        _platforms: list[Platform] = []
        for platform in platforms:
            if platform["rom_count"] > 0:
                if (
                    platform["slug"] not in MUOS_SUPPORTED_PLATFORMS
                    or platform["slug"] in self._exclude_platforms
                ):
                    continue
                _platforms.append(
                    Platform(
                        id=platform["id"],
                        display_name=platform["display_name"],
                        rom_count=platform["rom_count"],
                        slug=platform["slug"],
                    )
                )
                if not os.path.exists(
                    f"{self._file_system.resources_path}/{platform['slug']}.ico"
                ):
                    self._fetch_platform_icon(platform["slug"])
        _platforms.sort(key=lambda platform: platform.display_name)
        self._status.platforms = _platforms
        self._status.valid_host = True
        self._status.valid_credentials = True
        self._status.platforms_ready.set()

    def fetch_collections(self) -> None:
        try:
            request = Request(
                f"{self.host}/{self._collections_endpoint}", headers=self._headers
            )
        except ValueError:
            self._status.collections = []
            self._status.valid_host = False
            self._status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self._status.collections = []
                self._status.valid_host = False
                self._status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            if e.code == 403:
                self._status.collections = []
                self._status.valid_host = True
                self._status.valid_credentials = False
                return
            else:
                raise
        except URLError:
            self._status.collections = []
            self._status.valid_host = False
            self._status.valid_credentials = False
            return
        collections = json.loads(response.read().decode("utf-8"))
        if isinstance(collections, dict):
            collections = collections["items"]
        _collections: list[Collection] = []
        for collection in collections:
            if collection["rom_count"] > 0:
                if self._include_collections:
                    if collection["name"] not in self._include_collections:
                        continue
                elif self._exclude_collections:
                    if collection["name"] in self._exclude_collections:
                        continue
                _collections.append(
                    Collection(
                        id=collection["id"],
                        name=collection["name"],
                        rom_count=collection["rom_count"],
                    )
                )
        _collections.sort(key=lambda collection: collection.name)
        self._status.collections = _collections
        self._status.valid_host = True
        self._status.valid_credentials = True
        self._status.collections_ready.set()

    def fetch_roms(self) -> None:
        if self._status.selected_platform:
            view = View.PLATFORMS
            id = self._status.selected_platform.id
        elif self._status.selected_collection:
            view = View.COLLECTIONS
            id = self._status.selected_collection.id
        else:
            return

        try:
            request = Request(
                f"{self.host}/{self._roms_endpoint}?{view}_id={id}&order_by=name&order_dir=asc",
                headers=self._headers,
            )
        except ValueError:
            self._status.roms = []
            self._status.valid_host = False
            self._status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self._status.roms = []
                self._status.valid_host = False
                self._status.valid_credentials = False
                return
            response = urlopen(request, timeout=1800)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            if e.code == 403:
                self._status.roms = []
                self._status.valid_host = True
                self._status.valid_credentials = False
                return
            else:
                raise
        except URLError:
            self._status.roms = []
            self._status.valid_host = False
            self._status.valid_credentials = False
            return
        roms = json.loads(response.read().decode("utf-8"))
        if isinstance(roms, dict):
            roms = roms["items"]
        _roms = [
            Rom(
                id=rom["id"],
                name=rom["name"],
                fs_name=rom["fs_name"],
                platform_slug=rom["platform_slug"],
                fs_extension=rom["fs_extension"],
                fs_size=self._human_readable_size(rom["fs_size_bytes"]),
                fs_size_bytes=rom["fs_size_bytes"],
                multi=rom["multi"],
                languages=rom["languages"],
                regions=rom["regions"],
                revision=rom["revision"],
                tags=rom["tags"],
            )
            for rom in roms
            if rom["platform_slug"] in MUOS_SUPPORTED_PLATFORMS
        ]
        _roms.sort(key=lambda rom: rom.name)
        self._status.roms = _roms
        self._status.valid_host = True
        self._status.valid_credentials = True
        self._status.roms_ready.set()

    def _reset_download_status(
        self, valid_host: bool = False, valid_credentials: bool = False
    ) -> None:
        self._status.total_downloaded_bytes = 0
        self._status.downloaded_percent = 0
        self._status.valid_host = valid_host
        self._status.valid_credentials = valid_credentials
        self._status.downloading_rom = None
        self._status.extracting_rom = False
        self._status.multi_selected_roms = []
        self._status.download_queue = []
        self._status.download_rom_ready.set()
        self._status.abort_download.set()

    def download_rom(self) -> None:
        self._status.download_queue.sort(key=lambda rom: rom.name)
        for i, rom in enumerate(self._status.download_queue):
            self._status.downloading_rom = rom
            self._status.downloading_rom_position = i + 1
            dest_path = os.path.join(
                self._file_system.get_sd_storage_platform_path(rom.platform_slug),
                rom.fs_name,
            )
            url = f"{self.host}/{self._roms_endpoint}/{rom.id}/content/{quote(rom.fs_name)}?hidden_folder=True"
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            try:
                print(f"Fetching: {url}")
                request = Request(url, headers=self._headers)
            except ValueError:
                self._reset_download_status()
                return
            try:
                if request.type not in ("http", "https"):
                    self._reset_download_status()
                    return
                print(f"Downloading {rom.name} to {dest_path}")
                with urlopen(request) as response, open(
                    dest_path, "wb"
                ) as out_file:  # trunk-ignore(bandit/B310)
                    self._status.total_downloaded_bytes = 0
                    chunk_size = 1024
                    while True:
                        if not self._status.abort_download.is_set():
                            chunk = response.read(chunk_size)
                            if not chunk:
                                print("Finalized download")
                                break
                            out_file.write(chunk)
                            self._status.valid_host = True
                            self._status.valid_credentials = True
                            self._status.total_downloaded_bytes += len(chunk)
                            self._status.downloaded_percent = (
                                self._status.total_downloaded_bytes
                                / (
                                    self._status.downloading_rom.fs_size_bytes + 1
                                )  # Add 1 virtual byte to avoid division by zero
                            ) * 100
                        else:
                            self._reset_download_status(True, True)
                            os.remove(dest_path)
                            return
                if rom.multi:
                    self._status.extracting_rom = True
                    print("Multi file rom detected. Extracting...")
                    with zipfile.ZipFile(dest_path, "r") as zip_ref:
                        total_size = sum(file.file_size for file in zip_ref.infolist())
                        extracted_size = 0
                        chunk_size = 1024
                        for file in zip_ref.infolist():
                            if not self._status.abort_download.is_set():
                                file_path = os.path.join(
                                    os.path.dirname(dest_path), file.filename
                                )
                                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                                with zip_ref.open(file) as source, open(
                                    file_path, "wb"
                                ) as target:
                                    while True:
                                        chunk = source.read(chunk_size)
                                        if not chunk:
                                            break
                                        target.write(chunk)
                                        extracted_size += len(chunk)
                                        self._status.extracted_percent = (
                                            extracted_size / total_size
                                        ) * 100
                            else:
                                self._reset_download_status(True, True)
                                os.remove(dest_path)
                                return
                    self._status.extracting_rom = False
                    self._status.downloading_rom = None
                    os.remove(dest_path)
                    print(f"Extracted {rom.name} at {os.path.dirname(dest_path)}")
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
