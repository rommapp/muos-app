import os
from typing import Optional

import platform_maps
from models import Rom


class Filesystem:
    _instance: Optional["Filesystem"] = None

    # Check if app is running on muOS
    is_muos = os.path.exists("/mnt/mmc/MUOS")

    # Check is app is running on SpruceOS
    is_spruceos = os.path.exists("/mnt/SDCARD/spruce")

    # Storage paths for ROMs
    _sd1_roms_storage_path: str
    _sd2_roms_storage_path: str | None = None
    _sd1_catalogue_path: str | None = None
    _sd2_catalogue_path: str | None = None

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

        sd1_root_path = None
        sd2_root_path = None

        # ROMs storage path
        if self.is_muos:
            sd1_root_path = "/mnt/mmc"
            sd2_root_path = "/mnt/sdcard"
            self._sd1_roms_storage_path = os.path.join(sd1_root_path, "ROMS")
            self._sd2_roms_storage_path = os.path.join(sd2_root_path, "ROMS")
            self._sd1_catalogue_path = os.path.join(
                sd1_root_path, "MUOS/info/catalogue"
            )
            self._sd2_catalogue_path = os.path.join(
                sd2_root_path, "MUOS/info/catalogue"
            )
        elif self.is_spruceos:
            sd1_root_path = "/mnt/SDCARD"
            self._sd1_roms_storage_path = os.path.join(sd1_root_path, "Roms")
        else:
            # Go up two levels from the script's directory (e.g., from roms/ports/romm to roms/)
            base_path = os.path.abspath(os.path.join(os.getcwd(), "..", ".."))
            # Default to the ROMs directory, overridable via environment variable
            self._sd1_roms_storage_path = os.environ.get("ROMS_STORAGE_PATH", base_path)
            # For non-MuOS/non-SpruceOS devices, use catalogue from environment or create one in the app directory
            self._sd1_catalogue_path = os.environ.get(
                "CATALOGUE_PATH", os.path.join(os.getcwd(), "catalogue")
            )

        # Ensure the ROMs storage path exists on SD2 if SD2 is present
        if (
            self._sd2_roms_storage_path
            and sd2_root_path
            and os.path.exists(sd2_root_path)
            and not os.path.exists(self._sd2_roms_storage_path)
        ):
            try:
                os.mkdir(self._sd2_roms_storage_path)
            except FileNotFoundError:
                print("Cannot create SD2 storage path", self._sd2_roms_storage_path)

        # Ensure the catalogue path exists
        if self._sd1_catalogue_path and not os.path.exists(self._sd1_catalogue_path):
            try:
                os.makedirs(self._sd1_catalogue_path, exist_ok=True)
                print(f"Created catalogue directory: {self._sd1_catalogue_path}")
            except OSError as e:
                print(
                    f"Cannot create catalogue directory {self._sd1_catalogue_path}: {e}"
                )
                self._sd1_catalogue_path = None

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
        """
        Return the platform-specific storage path,
        using MUOS mapping if on muOS,
        or SpruceOS mapping if on SpruceOS,
        or using ES mapping if available.
        """

        # First check if the platform has an entry in the ES map
        platform_dir = platform_maps.ES_FOLDER_MAP.get(platform, platform)

        # If the ES map returns a tuple, use the first element of the tuple
        if isinstance(platform_dir, tuple):
            platform_dir = platform_dir[0]

        # If running on muOS, override the platform_dir with the MUOS mapping
        if self.is_muos:
            platform_dir = platform_maps.MUOS_SUPPORTED_PLATFORMS_FS_MAP.get(
                platform, platform_dir
            )

        if self.is_spruceos:
            platform_dir = platform_maps.SPRUCEOS_SUPPORTED_PLATFORMS_FS_MAP.get(
                platform, platform_dir
            )

        if platform_maps._env_maps and platform in platform_maps._env_platforms:
            platform_dir = platform_maps._env_maps.get(platform, platform_dir)

        return platform_dir

    def _get_sd1_platforms_storage_path(self, platform: str) -> str:
        platforms_dir = self._get_platform_storage_dir_from_mapping(platform)
        return os.path.join(self._sd1_roms_storage_path, platforms_dir)

    def _get_sd2_platforms_storage_path(self, platform: str) -> Optional[str]:
        if self._sd2_roms_storage_path:
            platforms_dir = self._get_platform_storage_dir_from_mapping(platform)
            return os.path.join(self._sd2_roms_storage_path, platforms_dir)
        return None

    def get_sd1_catalogue_platform_path(self, platform: str) -> str:
        if not self._sd1_catalogue_path:
            raise ValueError("SD1 catalogue path is not set.")

        platforms_dir = self._get_platform_storage_dir_from_mapping(platform)
        return os.path.join(self._sd1_catalogue_path, platforms_dir)

    def get_sd2_catalogue_platform_path(self, platform: str) -> str:
        if not self._sd2_catalogue_path:
            raise ValueError("SD2 catalogue path is not set.")

        platforms_dir = self._get_platform_storage_dir_from_mapping(platform)
        return os.path.join(self._sd2_catalogue_path, platforms_dir)

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

    def get_catalogue_platform_path(self, platform: str) -> str:
        """Return the catalogue path for a specific platform."""
        if self._current_sd == 2:
            return self.get_sd2_catalogue_platform_path(platform)

        return self.get_sd1_catalogue_platform_path(platform)

    def is_rom_in_device(self, rom: Rom) -> bool:
        """Check if a ROM exists in the storage path."""
        rom_path = os.path.join(
            self.get_platforms_storage_path(rom.platform_slug),
            rom.fs_name if not rom.has_multiple_files else f"{rom.fs_name}.m3u",
        )
        return os.path.exists(rom_path)
