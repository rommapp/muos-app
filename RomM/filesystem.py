import os
from typing import Optional

import platform_maps
from models import Rom


class Filesystem:
    _instance: Optional["Filesystem"] = None

    # Check if the app is running on muOS
    is_muos = os.path.exists("/mnt/mmc/MUOS")

    # Storage paths for ROMs
    _sd1_roms_storage_path: str
    _sd2_roms_storage_path: str | None

    # Resources path: Use current working directory + "resources"
    resources_path = os.path.join(os.getcwd(), "resources")

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Filesystem, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Optionally ensure resources directory exists (not required for roms dir)
        if not os.path.exists(self.resources_path):
            os.makedirs(self.resources_path, exist_ok=True)

        # ROMs storage path
        if self.is_muos:
            self._sd1_roms_storage_path = "/mnt/mmc/ROMS"
            self._sd2_roms_storage_path = "/mnt/sdcard/ROMS"
        else:
            # Go up two levels from the script's directory (e.g., from roms/ports/romm to roms/)
            base_path = os.path.abspath(os.path.join(os.getcwd(), "..", ".."))
            # Default to the ROMs directory, overridable via environment variable
            self._sd1_roms_storage_path = os.environ.get("ROMS_STORAGE_PATH", base_path)
            self._sd2_roms_storage_path = None

        # Ensure the ROMs storage path exists
        if self._sd2_roms_storage_path and not os.path.exists(
            self._sd2_roms_storage_path
        ):
            os.mkdir(self._sd2_roms_storage_path)

        # Set the default SD card based on the existence of the storage path
        self._current_sd = int(
            os.getenv(
                "DEFAULT_SD_CARD",
                1 if os.path.exists(self._sd1_roms_storage_path) else 2,
            )
        )

    ###
    # PRIVATE METHODS
    ###
    def _get_sd1_roms_storage_path(self) -> str:
        """Return the base ROMs storage path."""
        return self._sd1_roms_storage_path

    def _get_sd2_roms_storage_path(self) -> Optional[str]:
        """Return the secondary ROMs storage path if available."""
        return self._sd2_roms_storage_path

    def _get_platform_storage_dir_from_mapping(self, platform: str) -> str:
        """Return the platform-specific storage path, using MUOS mapping if on muOS,
        or using ES mapping if available."""

        # First check if the platform has an entry in the ES map
        platform_dir = platform_maps._ES_FOLDER_MAP.get(platform, platform)

        # If the ES map returns a tuple, use the first element of the tuple
        if isinstance(platform_dir, tuple):
            platform_dir = platform_dir[0]

        # If running on muOS, override the platform_dir with the MUOS mapping
        if self.is_muos:
            platform_dir = platform_maps.MUOS_SUPPORTED_PLATFORMS_FS_MAP.get(
                platform, platform_dir
            )

        return platform_dir

    def _get_sd1_platforms_storage_path(self, platform: str) -> str:
        platforms_dir = self._get_platform_storage_dir_from_mapping(platform)
        return os.path.join(self._sd1_roms_storage_path, platforms_dir)

    def _get_sd2_platforms_storage_path(self, platform: str) -> Optional[str]:
        if self._sd2_roms_storage_path:
            platforms_dir = self._get_platform_storage_dir_from_mapping(platform)
            return os.path.join(self._sd2_roms_storage_path, platforms_dir)
        return None

    ###
    # PUBLIC METHODS
    ###

    def switch_sd_storage(self) -> None:
        """Switch the current SD storage path."""
        if self._current_sd == 1:
            self._current_sd = 2
        else:
            self._current_sd = 1

    def get_roms_storage_path(self) -> str:
        """Return the current SD storage path."""
        if self._current_sd == 2 and self._sd2_roms_storage_path:
            return self._sd2_roms_storage_path

        return self._sd1_roms_storage_path

    def get_platforms_storage_path(self, platform: str) -> str:
        """Return the storage path for a specific platform."""
        if self._current_sd == 2:
            storage_path = self._get_sd2_platforms_storage_path(platform)
            if storage_path:
                return storage_path

        return self._get_sd1_platforms_storage_path(platform)

    def is_rom_in_device(self, rom: Rom) -> bool:
        """Check if a ROM exists in the storage path."""
        rom_path = os.path.join(
            self.get_platforms_storage_path(rom.platform_slug),
            rom.fs_name if not rom.multi else f"{rom.fs_name}.m3u",
        )
        return os.path.exists(rom_path)
