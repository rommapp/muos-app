from collections import namedtuple

Rom = namedtuple(
    "Rom",
    [
        "id",
        "name",
        "fs_name",
        "platform_slug",
        "fs_extension",
        "fs_size",
        "fs_size_bytes",
        "multi",
        "languages",
        "regions",
        "revision",
        "tags",
    ],
)
Collection = namedtuple("Collection", ["id", "name", "rom_count", "virtual"])
Platform = namedtuple("Platform", ["id", "display_name", "slug", "rom_count"])
