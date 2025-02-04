import os


class Filesystem:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Filesystem, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.__sd1_rom_storage_path = "/mnt/mmc/roms"
        self.__sd2_rom_storage_path = "/mnt/sdcard/roms"
        self.__current_sd = int(
            os.getenv(
                "DEFAULT_SD_CARD",
                1 if os.path.exists(self.__sd1_rom_storage_path) else 2,
            )
        )
        if self.__current_sd not in [1, 2]:
            raise Exception(f"Invalid default SD card: {self.__current_sd}")
        self.resources_path = "/mnt/mmc/MUOS/application/.romm/resources"

    def get_sd1_storage_path(self):
        return self.__sd1_rom_storage_path

    def get_sd2_storage_path(self):
        return self.__sd2_rom_storage_path

    def get_sd1_storage_platform_path(self, platform):
        return os.path.join(self.__sd1_rom_storage_path, platform)

    def get_sd2_storage_platform_path(self, platform):
        return os.path.join(self.__sd2_rom_storage_path, platform)

    def set_sd_storage(self, sd):
        if sd == 1:
            self.__current_sd = sd
        elif sd == 2 and os.path.exists(self.__sd2_rom_storage_path):
            self.__current_sd = sd

    def get_sd_storage(self):
        return self.__current_sd

    def switch_sd_storage(self):
        if self.__current_sd == 1:
            if not os.path.exists(self.__sd2_rom_storage_path):
                os.mkdir(self.__sd2_rom_storage_path)
            self.__current_sd = 2
        else:
            self.__current_sd = 1

    def get_sd_storage_path(self):
        if self.__current_sd == 1:
            return self.get_sd1_storage_path()
        else:
            return self.get_sd2_storage_path()

    def get_sd_storage_platform_path(self, platform):
        if self.__current_sd == 1:
            return self.get_sd1_storage_platform_path(platform)
        else:
            return self.get_sd2_storage_platform_path(platform)

    def is_rom_in_device(self, rom):
        return os.path.exists(os.path.join(self.get_sd_storage_platform_path(rom.platform_slug), rom.file_name))
