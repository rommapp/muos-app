import os
from typing import Optional

from models import Rom


class Filesystem:
    _instance: Optional["Filesystem"] = None
    _sd1_rom_storage_path = "/mnt/mmc/roms"
    _sd2_rom_storage_path = "/mnt/sdcard/roms"
    resources_path = "/mnt/mmc/MUOS/application/.romm/resources"

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Filesystem, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self._current_sd = int(
            os.getenv(
                "DEFAULT_SD_CARD",
                1 if os.path.exists(self._sd1_rom_storage_path) else 2,
            )
        )
        if self._current_sd not in [1, 2]:
            raise Exception(f"Invalid default SD card: {self._current_sd}")

    def get_sd1_storage_path(self) -> str:
        return self._sd1_rom_storage_path

    def get_sd2_storage_path(self) -> str:
        return self._sd2_rom_storage_path

    def get_sd1_storage_platform_path(self, platform: str) -> str:
        return os.path.join(
            self._sd1_rom_storage_path,
            MUOS_SUPPORTED_PLATFORMS_FS_MAP.get(platform, platform),
        )

    def get_sd2_storage_platform_path(self, platform: str) -> str:
        return os.path.join(self._sd2_rom_storage_path, platform)

    def set_sd_storage(self, sd: int) -> None:
        if sd == 1:
            self._current_sd = sd
        elif sd == 2 and os.path.exists(self._sd2_rom_storage_path):
            self._current_sd = sd

    def get_sd_storage(self) -> int:
        return self._current_sd

    def switch_sd_storage(self) -> None:
        if self._current_sd == 1:
            if not os.path.exists(self._sd2_rom_storage_path):
                os.mkdir(self._sd2_rom_storage_path)
            self._current_sd = 2
        else:
            self._current_sd = 1

    def get_sd_storage_path(self) -> str:
        if self._current_sd == 1:
            return self.get_sd1_storage_path()
        else:
            return self.get_sd2_storage_path()

    def get_sd_storage_platform_path(self, platform: str) -> str:
        if self._current_sd == 1:
            return self.get_sd1_storage_platform_path(platform)
        else:
            return self.get_sd2_storage_platform_path(platform)

    def is_rom_in_device(self, rom: Rom) -> bool:
        return os.path.exists(
            os.path.join(
                self.get_sd_storage_platform_path(rom.platform_slug),
                rom.fs_name if not rom.multi else f"{rom.fs_name}.m3u",
            )
        )


MUOS_SUPPORTED_PLATFORMS_FS_MAP = {
    "acpc": "Amstrad",
    "arcade": "Arcade",
    "arduboy": "Arduboy",
    "atari2600": "Atari 2600",
    "atari5200": "Atari 5200",
    "atari7800": "Atari 7800",
    "jaguar": "Atari Jaguar",
    "lynx": "Atari Lynx",
    "atari-st": "Atari ST-STE-TT-Falcon",
    "wonderswan": "Bandai WonderSwan-Color",
    "wonderswan-color": "Book Reader",
    "cave-story": "Cave Story",
    "chailove": "ChaiLove",
    "chip-8": "CHIP-8",
    "colecovision": "ColecoVision",
    "amiga": "Commodore Amiga",
    "c128": "Commodore C128",
    "c64": "Commodore C64",
    "cbm-ii": "Commodore CBM-II",
    "cpet": "Commodore PET",
    "vic-20": "Commodore VIC-20",
    "dos": "DOS",
    "doom": "Doom",
    "ports": "External - Ports",
    "fairchild-channel-f": "Fairchild ChannelF",
    "vectrex": "GCE - Vectrex",
    "galaksija": "Galaksija Retro Computer",
    "g-and-w": "Handheld Electronic - Game and Watch",
    "j2me": "Java J2ME",
    "karaoke": "Karaoke",
    "lowres": "Lowres NX",
    "lua": "Lua Engine",
    "odyssey--1": "Magnavox Odyssey - VideoPac",
    "intellivision": "Mattel - Intellivision",
    "media-player": "Media Player",
    "mega-duck-slash-cougar-boy": "Mega Duck",
    "msx": "Microsoft - MSX",
    "turbografx-16-slash-pc-engine-cd": "NEC PC Engine CD",
    "supergrafx": "NEC PC Engine SuperGrafx",
    "turbografx16--1": "NEC PC Engine",
    "pc-8000": "NEC PC-8000 - PC-8800 series",
    "pc-fx": "NEC PC-FX",
    "pc-9800-series": "NEC PC98",
    "nds": "Nintendo DS",
    "fds": "Nintendo FDS",
    "gba": "Nintendo Game Boy Advance",
    "gbc": "Nintendo Game Boy Color",
    "gb": "Nintendo Game Boy",
    "n64": "Nintendo N64",
    "nes": "Nintendo NES-Famicom",
    "famicom": "Nintendo NES-Famicom",
    "snes": "Nintendo SNES-SFC",
    "sfam": "Nintendo SNES-SFC",
    "pokemon-mini": "Nintendo Pokemon Mini",
    "virtualboy": "Nintendo Virtual Boy",
    "onscripter": "Onscripter",
    "openbor": "OpenBOR",
    "pico-8": "PICO-8",
    "philips-cd-i": "Philips CDi",
    "quake": "Quake",
    "rpg-maker": "RPG Maker 2000 - 2003",
    "neogeoaes": "SNK Neo Geo",
    "neogeomvs": "SNK Neo Geo",
    "neo-geo-cd": "SNK Neo Geo CD",
    "neo-geo-pocket": "SNK Neo Geo Pocket - Color",
    "neo-geo-pocket-color": "SNK Neo Geo Pocket - Color",
    "scummvm": "ScummVM",
    "sega-32x": "Sega 32X",
    "naomi": "Sega Atomiswave Naomi",
    "dc": "Sega Dreamcast",
    "gamegear": "Sega Game Gear",
    "sega-master-system": "Sega Master System",
    "genesis-slash-megadrive": "Sega Mega Drive - Genesis",
    "sega-pico": "Sega Pico",
    "segacd": "Sega Mega CD - Sega CD",
    "sg1000": "Sega SG-1000",
    "saturn": "Sega Saturn",
    "x1": "Sharp X1",
    "sharp-x68000": "Sharp X68000",
    "sinclair-zx81": "Sinclair ZX 81",
    "zxs": "Sinclair ZX Spectrum",
    "ps": "Sony Playstation",
    "psp": "Sony Playstation Portable",
    "tic-80": "TIC-80",
    "ti-83": "Texas Instruments TI-83",
    "3do": "The 3DO Company - 3DO",
    "uzebox": "Uzebox",
    "vemulator": "VeMUlator",
    "vircon-32": "Vircon32",
    "wasm-4": "WASM-4",
    "watara-slash-quickshot-supervision": "Watara Supervision",
    "wolfenstein-3d": "Wolfenstein 3D",
}

MUOS_SUPPORTED_PLATFORMS = frozenset(MUOS_SUPPORTED_PLATFORMS_FS_MAP.keys())
MUOS_SUPPORTED_PLATFORMS_FS = frozenset(MUOS_SUPPORTED_PLATFORMS_FS_MAP.values())
