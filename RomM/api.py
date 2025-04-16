import base64
import json
import math
import os
import re
import zipfile
from typing import Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import platform_maps
from filesystem import Filesystem
from models import Collection, Platform, Rom
from PIL import Image
from status import Status, View


class API:
    _platforms_endpoint = "api/platforms"
    _platform_icon_url = "assets/platforms"
    _collections_endpoint = "api/collections"
    _virtual_collections_endpoint = "api/collections/virtual"
    _roms_endpoint = "api/roms"
    _user_me_endpoint = "api/users/me"
    _user_profile_picture_url = "assets/romm/assets"

    def __init__(self):
        self.status = Status()
        self.file_system = Filesystem()

        self.host = os.getenv("HOST", "")
        self.username = os.getenv("USERNAME", "")
        self.password = os.getenv("PASSWORD", "")
        self.headers = {}
        self._exclude_platforms = set(self._getenv_list("EXCLUDE_PLATFORMS"))
        self._include_collections = set(self._getenv_list("INCLUDE_COLLECTIONS"))
        self._exclude_collections = set(self._getenv_list("EXCLUDE_COLLECTIONS"))
        self._collection_type = os.getenv("COLLECTION_TYPE", "collection")

        if self.username and self.password:
            credentials = f"{self.username}:{self.password}"
            auth_token = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
            self.headers = {"Authorization": f"Basic {auth_token}"}

    @staticmethod
    def _getenv_list(key: str) -> list[str]:
        value = os.getenv(key)
        return [item.strip() for item in value.split(",")] if value is not None else []

    @staticmethod
    def _human_readable_size(size_bytes: int) -> Tuple[float, str]:
        if size_bytes == 0:
            return 0, "B"
        size_name = ("B", "KB", "MB", "GB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return (s, size_name[i])

    def _sanitize_filename(self, filename: str) -> str:
        path_parts = os.path.normpath(filename).split(os.sep)
        sanitized_parts = []

        for _i, part in enumerate(path_parts):
            sanitized = re.sub(r'[\\/*?:"<>|\t\n\r\b]', "_", part)
            sanitized_parts.append(sanitized)

        return os.path.join(*sanitized_parts)

    def _fetch_user_profile_picture(self, avatar_path: str) -> None:
        fs_extension = avatar_path.split(".")[-1]
        try:
            request = Request(
                f"{self.host}/{self._user_profile_picture_url}/{avatar_path}",
                headers=self.headers,
            )
        except ValueError as e:
            print(e)
            self.status.valid_host = False
            self.status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self.status.valid_host = False
                self.status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            print(e)
            if e.code == 403:
                self.status.valid_host = True
                self.status.valid_credentials = False
                return
            else:
                raise
        except URLError as e:
            print(e)
            self.status.valid_host = False
            self.status.valid_credentials = False
            return
        if not os.path.exists(self.file_system.resources_path):
            os.makedirs(self.file_system.resources_path)
        self.status.profile_pic_path = (
            f"{self.file_system.resources_path}/{self.username}.{fs_extension}"
        )
        with open(self.status.profile_pic_path, "wb") as f:
            f.write(response.read())
        icon = Image.open(self.status.profile_pic_path)
        icon = icon.resize((26, 26))
        icon.save(self.status.profile_pic_path)
        self.status.valid_host = True
        self.status.valid_credentials = True

    def fetch_me(self) -> None:
        try:
            request = Request(
                f"{self.host}/{self._user_me_endpoint}", headers=self.headers
            )
        except ValueError as e:
            print(e)
            self.status.valid_host = False
            self.status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self.status.valid_host = False
                self.status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            print(e)
            if e.code == 403:
                self.status.valid_host = True
                self.status.valid_credentials = False
                return
            else:
                raise
        except URLError as e:
            print(e)
            self.status.valid_host = False
            self.status.valid_credentials = False
            return
        me = json.loads(response.read().decode("utf-8"))
        self.status.me = me
        if me["avatar_path"]:
            self._fetch_user_profile_picture(me["avatar_path"])
        self.status.me_ready.set()

    def _fetch_platform_icon(self, platform_slug) -> None:
        try:
            mapped_slug, icon_filename = platform_maps._ES_FOLDER_MAP.get(
                platform_slug.lower(), (platform_slug, platform_slug)
            )
            icon_url = f"{self.host}/{self._platform_icon_url}/{icon_filename}.ico"
            request = Request(
                f"{self.host}/{self._platform_icon_url}/{icon_filename}.ico",
                headers=self.headers,
            )
        except ValueError as e:
            print(e)
            self.status.valid_host = False
            self.status.valid_credentials = False
            return

        try:
            if request.type not in ("http", "https"):
                self.status.valid_host = False
                self.status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            print(e)
            if e.code == 403:
                self.status.valid_host = True
                self.status.valid_credentials = False
                return
            # Icon is missing on the server
            elif e.code == 404:
                self.status.valid_host = True
                self.status.valid_credentials = True
                print(f"Requested icon not found: {icon_url}")
                return
            else:
                raise
        except URLError as e:
            print(e)
            self.status.valid_host = False
            self.status.valid_credentials = False
            return

        self.file_system.resources_path = os.getcwd() + "/resources"
        if not os.path.exists(self.file_system.resources_path):
            os.makedirs(self.file_system.resources_path)

        with open(f"{self.file_system.resources_path}/{platform_slug}.ico", "wb") as f:
            f.write(response.read())

        icon = Image.open(f"{self.file_system.resources_path}/{platform_slug}.ico")
        icon = icon.resize((30, 30))
        icon.save(f"{self.file_system.resources_path}/{platform_slug}.ico")
        self.status.valid_host = True
        self.status.valid_credentials = True

    def fetch_platforms(self) -> None:
        try:
            request = Request(
                f"{self.host}/{self._platforms_endpoint}", headers=self.headers
            )
        except ValueError:
            self.status.platforms = []
            self.status.valid_host = False
            self.status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self.status.platforms = []
                self.status.valid_host = False
                self.status.valid_credentials = False
                return
            response = urlopen(request, timeout=60)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            print(f"HTTP Error in fetching platforms: {e}")
            if e.code == 403:
                self.status.platforms = []
                self.status.valid_host = True
                self.status.valid_credentials = False
                return
            else:
                raise
        except URLError:
            print("URLError in fetching platforms")
            self.status.platforms = []
            self.status.valid_host = False
            self.status.valid_credentials = False
            return
        platforms = json.loads(response.read().decode("utf-8"))
        _platforms: list[Platform] = []

        # Get the list of subfolders in the ROMs directory for non-muOS filtering
        roms_subfolders = set()
        if not self.file_system.is_muos:
            roms_path = self.file_system.get_roms_storage_path()
            print(f"ROMs path: {roms_path}")
            if os.path.exists(roms_path):
                roms_subfolders = {
                    d.lower()
                    for d in os.listdir(roms_path)
                    if os.path.isdir(os.path.join(roms_path, d))
                }

        for platform in platforms:
            if platform["rom_count"] > 0:
                platform_slug = platform["slug"].lower()
                if self.file_system.is_muos:
                    if (
                        platform_slug not in platform_maps.MUOS_SUPPORTED_PLATFORMS
                        or platform_slug in self._exclude_platforms
                    ):
                        continue
                else:
                    # Map the slug to the folder name for non-muOS
                    mapped_folder, icon_file = platform_maps._ES_FOLDER_MAP.get(
                        platform_slug.lower(), (platform_slug, platform_slug)
                    )
                    if (
                        mapped_folder.lower() not in roms_subfolders
                        or platform_slug in self._exclude_platforms
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

                self.file_system.resources_path = os.getcwd() + "/resources"
                icon_path = f"{self.file_system.resources_path}/{platform['slug']}.ico"
                if not os.path.exists(icon_path):
                    self._fetch_platform_icon(platform["slug"])

        self.status.platforms = _platforms
        print(f"Fetched {len(_platforms)} platforms")
        self.status.valid_host = True
        self.status.valid_credentials = True
        self.status.platforms_ready.set()

    def fetch_collections(self) -> None:
        try:
            collections_request = Request(
                f"{self.host}/{self._collections_endpoint}", headers=self.headers
            )
            v_collections_request = Request(
                f"{self.host}/{self._virtual_collections_endpoint}?type={self._collection_type}",
                headers=self.headers,
            )
        except ValueError:
            self.status.collections = []
            self.status.valid_host = False
            self.status.valid_credentials = False
            return

        try:
            if collections_request.type not in ("http", "https"):
                self.status.collections = []
                self.status.valid_host = False
                self.status.valid_credentials = False
                return

            collections_response = urlopen(  # trunk-ignore(bandit/B310)
                collections_request, timeout=60
            )
            v_collections_response = urlopen(  # trunk-ignore(bandit/B310)
                v_collections_request, timeout=60
            )
        except HTTPError as e:
            if e.code == 403:
                self.status.collections = []
                self.status.valid_host = True
                self.status.valid_credentials = False
                return
            else:
                raise
        except URLError:
            self.status.collections = []
            self.status.valid_host = False
            self.status.valid_credentials = False
            return

        collections = json.loads(collections_response.read().decode("utf-8"))
        v_collections = json.loads(v_collections_response.read().decode("utf-8"))

        if isinstance(collections, dict):
            collections = collections["items"]
        if isinstance(v_collections, dict):
            v_collections = v_collections["items"]

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
                        virtual=False,
                    )
                )

        for v_collection in v_collections:
            if v_collection["rom_count"] > 0:
                if self._include_collections:
                    if v_collection["name"] not in self._include_collections:
                        continue
                elif self._exclude_collections:
                    if v_collection["name"] in self._exclude_collections:
                        continue
                _collections.append(
                    Collection(
                        id=v_collection["id"],
                        name=v_collection["name"],
                        rom_count=v_collection["rom_count"],
                        virtual=True,
                    )
                )

        self.status.collections = _collections
        self.status.valid_host = True
        self.status.valid_credentials = True
        self.status.collections_ready.set()

    def fetch_roms(self) -> None:
        if self.status.selected_platform:
            view = View.PLATFORMS
            id = self.status.selected_platform.id
            selected_platform_slug = self.status.selected_platform.slug.lower()
        elif self.status.selected_collection:
            view = View.COLLECTIONS
            id = self.status.selected_collection.id
            selected_platform_slug = None
        elif self.status.selected_virtual_collection:
            view = View.VIRTUAL_COLLECTIONS
            id = self.status.selected_virtual_collection.id
            selected_platform_slug = None
        else:
            return

        try:
            request = Request(
                f"{self.host}/{self._roms_endpoint}?{view}_id={id}&order_by=name&order_dir=asc&limit=1000",
                headers=self.headers,
            )
        except ValueError:
            self.status.roms = []
            self.status.valid_host = False
            self.status.valid_credentials = False
            return
        try:
            if request.type not in ("http", "https"):
                self.status.roms = []
                self.status.valid_host = False
                self.status.valid_credentials = False
                return
            response = urlopen(request, timeout=1800)  # trunk-ignore(bandit/B310)
        except HTTPError as e:
            if e.code == 403:
                self.status.roms = []
                self.status.valid_host = True
                self.status.valid_credentials = False
                return
            else:
                raise
        except URLError:
            self.status.roms = []
            self.status.valid_host = False
            self.status.valid_credentials = False
            return

        # { 'items': list[dict], 'total': number, 'limit': number, 'offset': number }
        roms = json.loads(response.read().decode("utf-8"))
        if isinstance(roms, dict):
            roms = roms["items"]

        # Get the list of subfolders in the ROMs directory for non-muOS filtering
        roms_subfolders = set()
        if not self.file_system.is_muos:
            roms_path = self.file_system.get_roms_storage_path()
            if os.path.exists(roms_path):
                roms_subfolders = {
                    d.lower()
                    for d in os.listdir(roms_path)
                    if os.path.isdir(os.path.join(roms_path, d))
                }

        _roms = []
        for rom in roms:
            platform_slug = rom["platform_slug"].lower()
            if self.file_system.is_muos:
                if platform_slug not in platform_maps.MUOS_SUPPORTED_PLATFORMS:
                    continue
            else:
                mapped_folder, icon_file = platform_maps._ES_FOLDER_MAP.get(
                    platform_slug.lower(), (platform_slug, platform_slug)
                )
                if mapped_folder.lower() not in roms_subfolders:
                    continue
            if view == View.PLATFORMS and platform_slug != selected_platform_slug:
                continue
            _roms.append(
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
            )

        self.status.roms = _roms
        self.status.valid_host = True
        self.status.valid_credentials = True
        self.status.roms_ready.set()

    def _reset_download_status(
        self, valid_host: bool = False, valid_credentials: bool = False
    ) -> None:
        self.status.total_downloaded_bytes = 0
        self.status.downloaded_percent = 0
        self.status.valid_host = valid_host
        self.status.valid_credentials = valid_credentials
        self.status.downloading_rom = None
        self.status.extracting_rom = False
        self.status.multi_selected_roms = []
        self.status.download_queue = []
        self.status.download_rom_ready.set()
        self.status.abort_download.set()

    def download_rom(self) -> None:
        self.status.download_queue.sort(key=lambda rom: rom.name)
        for i, rom in enumerate(self.status.download_queue):
            self.status.downloading_rom = rom
            self.status.downloading_rom_position = i + 1
            dest_path = os.path.join(
                self.file_system.get_platforms_storage_path(rom.platform_slug),
                self._sanitize_filename(rom.fs_name),
            )
            url = f"{self.host}/{self._roms_endpoint}/{rom.id}/content/{quote(rom.fs_name)}?hidden_folder=true"
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            try:
                print(f"Fetching: {url}")
                request = Request(url, headers=self.headers)
            except ValueError:
                self._reset_download_status()
                return
            try:
                if request.type not in ("http", "https"):
                    self._reset_download_status()
                    return
                print(f"Downloading {rom.name} to {dest_path}")
                with (
                    urlopen(request) as response,  # trunk-ignore(bandit/B310)
                    open(dest_path, "wb") as out_file,
                ):
                    self.status.total_downloaded_bytes = 0
                    chunk_size = 1024
                    while True:
                        if not self.status.abort_download.is_set():
                            chunk = response.read(chunk_size)
                            if not chunk:
                                print("Finalized download")
                                break
                            out_file.write(chunk)
                            self.status.valid_host = True
                            self.status.valid_credentials = True
                            self.status.total_downloaded_bytes += len(chunk)
                            self.status.downloaded_percent = (
                                self.status.total_downloaded_bytes
                                / (
                                    self.status.downloading_rom.fs_size_bytes + 1
                                )  # Add 1 virtual byte to avoid division by zero
                            ) * 100
                        else:
                            self._reset_download_status(True, True)
                            os.remove(dest_path)
                            return
                # Handle multi-file (ZIP) ROMs
                if rom.multi:
                    self.status.extracting_rom = True
                    print("Multi file rom detected. Extracting...")
                    with zipfile.ZipFile(dest_path, "r") as zip_ref:
                        total_size = sum(file.file_size for file in zip_ref.infolist())
                        extracted_size = 0
                        chunk_size = 1024
                        for file in zip_ref.infolist():
                            if not self.status.abort_download.is_set():
                                file_path = os.path.join(
                                    os.path.dirname(dest_path),
                                    self._sanitize_filename(file.filename),
                                )
                                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                                with (
                                    zip_ref.open(file) as source,
                                    open(file_path, "wb") as target,
                                ):
                                    while True:
                                        chunk = source.read(chunk_size)
                                        if not chunk:
                                            break
                                        target.write(chunk)
                                        extracted_size += len(chunk)
                                        self.status.extracted_percent = (
                                            extracted_size / total_size
                                        ) * 100
                            else:
                                self._reset_download_status(True, True)
                                os.remove(dest_path)
                                return
                    self.status.extracting_rom = False
                    self.status.downloading_rom = None
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
