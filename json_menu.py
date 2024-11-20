"""
based on the cattery import module, I want to implement my own
"""

import glob
import json
import os
import nuke


# GLOBALS
# generic values, overwrite in init.py with load_globals function
JSON_FILE = "menu.json"
ICONS = {}
FOLDER_NAME = "gizmos"


class NodeInfo:
    "Node Class - collect data and process accordingly"

    def __init__(self, filepath, name, shortcut, icon, ctx):
        self.filepath = filepath
        self.name = name or filepath
        self.shortcut = shortcut
        self.icon = icon
        self.ctx = ctx

    @classmethod
    def from_dict(cls, data):
        "retrieve info from dictionary"
        if not data.get("filepath"):
            return None

        self = cls(
            data["filepath"],
            data.get("name", ""),
            data.get("shortcut", ""),
            data.get("icon", ""),
            data.get("ctx", 0),
        )

        if not self.name or self.name == self.filepath:
            self.name = os.path.splitext(os.path.basename(self.filepath))[0]

        return self

    def to_dict(self):
        "write info into dictionary"
        return {
            "filepath": self.filepath,
            "name": self.name,
            "shortcut": self.shortcut,
            "icon": self.icon,
            "ctx": self.ctx,
        }

    def create_node(self):
        "create Node depending on type"
        if self.filepath.endswith((".gizmo", ".dll")):
            tool = os.path.splitext(os.path.basename(self.filepath))[0]
            return f"import nuke; nuke.createNode({repr(tool)})"

        elif self.filepath.endswith(".nk"):
            return f"import nuke; nuke.nodePaste({repr(self.filepath)})"

        elif self.filepath.endswith((".pdf", ".html")):
            return f"import nukescripts; nukescripts.start({repr(self.filepath)})"

        elif self.filepath.endswith(".tcl"):
            filepath = os.path.splitext(os.path.basename(self.filepath))[0]
            return f"import nuke; nuke.tcl({repr(filepath.strip())})"

        elif self.filepath.startswith("http"):
            return f"import nukescripts; nukescripts.start({repr(self.filepath)})"

        return ""


class PackageInfo:
    "process info from custom json file"

    def __init__(self):
        self.minimum_nuke_version_required = 13.1
        self.version = 1
        self.category = ""
        self.icon = ""
        self.nodes = []

    @classmethod
    def from_dict(cls, data):
        "retrieve info from dictionary"
        self = cls()
        self.minimum_nuke_version_required = data.get("minimum_nuke_version_required", 13.2)
        self.version = data.get("version", 1)
        self.category = data.get("category", "")
        self.icon = data.get("icon", "")
        nodes = [NodeInfo.from_dict(d) for d in data.get("nodes", [])]
        self.nodes = [x for x in nodes if x is not None]  # filter invalid

        return self

    def to_dict(self):
        "write info into dictionary"
        return {
            "minimum_nuke_version_required": self.minimum_nuke_version_required,
            "version": self.version,
            "category": self.category,
            "icon": self.icon,
            "nodes": [node.to_dict() for node in self.nodes],
        }

    @classmethod
    def from_json(cls, filepath):
        "get info from custom json file"
        with open(filepath) as fp:
            data = json.load(fp)
        return cls.from_dict(data)


def normalised_path(filepath):
    """
    Nuke uses forward slash on all platforms, including Windows (which is odd and
    unconventional), this method encapsulates that.
    """
    return filepath.replace("\\", "/")


def find_repositories():
    "yield all pathes that contain gizmos in it's path"
    for path in [pp for pp in nuke.pluginPath() if os.path.exists(pp)]:
        for filename in [name for name in os.listdir(path) if FOLDER_NAME == name.lower()]:
            yield os.path.abspath(os.path.join(path, filename))


def discover_packages(repository, target_version):
    "search for custom json files in repository to include packages in  menu"
    result = []
    for root, _, files in os.walk(repository):
        if JSON_FILE not in files:
            continue

        filepath = os.path.join(root, JSON_FILE)
        package = PackageInfo.from_json(filepath)
        if package.minimum_nuke_version_required > target_version or len(package.nodes) == 0:
            continue

        package_icon = normalised_path(os.path.join(root, package.icon))

        if not os.path.exists(package_icon):
            package_icon = package.icon

        package.icon = package_icon if package.icon else ""

        for node in package.nodes:
            if node.filepath.endswith(".py"):
                node.name = "python"
                continue

            if not node.filepath.startswith("http"):
                node.filepath = normalised_path(os.path.join(root, node.filepath))

            node.icon = node.icon if node.icon else ICONS["default"]
        result.append(package)

    return result


def register_paths():
    "add filepath of node to pluginpath"
    nuke_version = float(f"{nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}")
    for repository in find_repositories():
        for package in discover_packages(repository, nuke_version):
            for node in package.nodes:
                directory = os.path.dirname(node.filepath)
                if directory not in nuke.pluginPath():
                    nuke.pluginAddPath(directory, addToSysPath=False)


def populate_menu(menu):
    "add items to created menu"
    register_paths()
    nuke_version = float(f"{nuke.NUKE_VERSION_MAJOR}.{nuke.NUKE_VERSION_MINOR}")

    packages_by_category = {}
    for repository in find_repositories():
        for package in discover_packages(repository, nuke_version):
            category = package.category if package.category else "_"
            if category not in packages_by_category:
                packages_by_category[category] = []
            packages_by_category[category].append(package)

    for ctgy in sorted(packages_by_category.keys(), key=lambda k: k.lower().replace("_", "~")):
        # for ctgy in sorted(packages_by_category.keys()):
        if ctgy.startswith("../"):
            sub_menu = nuke.menu("Nodes")
            category = ctgy.replace("../", "")
        else:
            sub_menu = menu
            category = ctgy

        if category != "_":
            icon_list = [p.icon for p in packages_by_category[ctgy] if p.icon]
            icon = icon_list[0] if icon_list else ICONS.get(category.lower(), ICONS["other"])

            sub_menu = (
                sub_menu.menu(category)
                if sub_menu.menu(category)
                else sub_menu.addMenu(category, icon)
            )

        nodes = [c for p in packages_by_category[ctgy] for c in p.nodes]
        nodes.sort(key=lambda k: k.name.lower().replace("_", "~"))
        for node in nodes:
            if node.name == "python":
                nuke.load(node.filepath)
                continue

            sub_menu.addCommand(
                node.name,
                node.create_node(),
                icon=node.icon,
                shortcut=node.shortcut,
                shortcutContext=node.ctx,
            )


def load_globals(json_file, folder, default_icons):
    "overwrite global variables in order to not change this file"
    global JSON_FILE
    global ICONS
    global FOLDER_NAME

    JSON_FILE = json_file
    ICONS = default_icons
    FOLDER_NAME = folder


def create_menu(menu_name):
    "create the actual menu"
    toolbar = nuke.menu("Nodes")
    # toolbar.removeItem(menu_name)  # just for now, until it's not in menu_entries anymore
    m = toolbar.menu(menu_name)
    if not m:
        idx = [e for e, m in enumerate(toolbar.items()) if m.name() == "Other"]
        # add Menu after the default Other Menu in Toolbar
        m = toolbar.addMenu(menu_name, ICONS["menu"], index=idx[0] + 1)
    m.clearMenu()

    populate_menu(m)

    m.addSeparator()
    m.addCommand(
        "Update",
        f"{os.path.splitext(os.path.basename(__file__))[0]}.create_menu({repr(menu_name)})",
    )


if __name__ == "__main__":
    icons_dict = {
        "3d": "cvfx_3d.png",
        "default": "cvfx.png",
        "image": "cvfx_image.png",
        "menu": "cvfx_menu.png",
        "other": "cvfx_other.png",
    }
    dir_list = glob.glob(f"{os.environ['nuke_path']}/_v*")

    load_globals("cfx_menu.json", "tools", icons_dict)
    create_menu(f"Celluloid VFX {os.path.basename(dir_list[0]).strip('_')}")
