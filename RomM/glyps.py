import itertools
from collections import namedtuple

Glyphs = namedtuple(
    "Glyphs",
    [
        "host",
        "user",
        "download",
        "abort",
        "spinner",
        "cloud_sync",
        "checkbox",
        "checkbox_selected",
        "about",
        "microsd",
        "delete",
        "exit",
    ],
)

glyphs = Glyphs(
    host="\uf000",
    user="\uf001",
    download="\uf00b",
    abort="\uf00e",
    spinner=itertools.cycle(["\uf004", "\uf005", "\uf006", "\uf007"]),
    checkbox="\uf002",
    checkbox_selected="\uf003",
    cloud_sync="\uf00a",
    about="\uf008",
    microsd="\uf009",
    delete="\uf00d",
    exit="\uf00c",
)
