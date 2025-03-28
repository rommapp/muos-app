from collections import namedtuple

Rom = namedtuple(
    "Rom",
    [
        "id",
        "name",
        "summary",
        "fs_name",
        "platform_id",
        "platform_slug",
        "fs_extension",
        "fs_size",
        "fs_size_bytes",
        "multi",
        "languages",
        "regions",
        "revision",
        "tags",
        "path_cover_large",
        "path_cover_small",
        "path_screenshot",
        "first_release_date",
        "average_rating",
        "genres",
        "franchises",
        "companies",
        "age_ratings"
    ],
)
Collection = namedtuple("Collection", ["id", "name", "rom_count", "virtual"])
Platform = namedtuple("Platform", ["id", "display_name", "slug", "rom_count"])
