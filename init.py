import nuke

nuke.pluginAddPath("python")
nuke.pluginAddPath("icons")

# import custom after python path extension
import json_menu

icons_dict = {
    "3d": "3d.png",
    "default": "default.png",
    "image": "image.png",
    "menu": "menu.png",
    "other": "other.png",
}

json_menu.load_globals("menu.json", "examples", icons_dict)
json_menu.register_paths()
