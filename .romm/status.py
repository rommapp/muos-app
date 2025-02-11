import itertools
import threading

from glyps import glyphs


class View:
    PLATFORMS = "platform"
    COLLECTIONS = "collection"
    ROMS = "roms"


class Filter:
    ALL = "all"
    LOCAL = "local"
    REMOTE = "remote"


class StartMenuOptions:
    ABORT_DOWNLOAD = (f"{glyphs.abort} Abort downloads", 0)
    SD_SWITCH = (f"{glyphs.microsd} Switch SD", 1)
    EXIT = (f"{glyphs.exit} Exit", 2)


class Status:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Status, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.valid_host = True
        self.valid_credentials = True

        self.me = None
        self.profile_pic_path = ""

        self.current_view = View.PLATFORMS
        self.selected_platform = None
        self.selected_collection = None

        self.show_start_menu = False
        self.show_contextual_menu = False

        self.platforms = []
        self.collections = []
        self.roms = []
        self.firmware = []
        self.roms_to_show = []
        self.filters = itertools.cycle([Filter.ALL, Filter.LOCAL, Filter.REMOTE])
        self.current_filter = next(self.filters)

        self.platforms_ready = threading.Event()
        self.collections_ready = threading.Event()
        self.roms_ready = threading.Event()
        self.firmware_ready = threading.Event()
        self.download_rom_ready = threading.Event()
        self.abort_download = threading.Event()
        self.me_ready = threading.Event()

        # Initialize events what won't launch at startup
        self.roms_ready.set()
        self.firmware_ready.set()
        self.download_rom_ready.set()
        self.abort_download.set()

        self.multi_selected_roms = []
        self.download_queue = []
        self.downloading_rom = None
        self.downloading_rom_position = 0
        self.total_downloaded_bytes = 0
        self.downloaded_percent = 0

    def reset_roms_list(self):
        self.roms = []
