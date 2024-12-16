# nuke_menu_construction_kit

#### !!! This package is still a work in progress !!!

*The functionality is working, but the integration into the pipeline is still not configured for general use.  
When it's done, Users will have the possibilty to incorporate Gizmos, Nuke Scripts and a lot more without needing to adjust the python files of the pipeline.*

## Inspiration and Goal
The inspiration came from Foundry's integration of the Cattery Tools, where you could update your menu without the need to restart Nuke and use the new Gizmos within that same session.  

The *main* goal was to keep the pipeline tidy without long python files all adding Commands to the UI of Nuke. Menu entries will in general be sorted alphabetically, within alphabetically sorted Menus.  
The *secondary* goal is to keep Gizmos seperate in different Software Versions, since you can define a minimum Version Number, making it easier to stick to necessities.

Following there is an example of the defining json file with possible configurations:
```json
{
    "minimum_nuke_version_required": 13.2,
    "version": 1,
    "category": "MENU_NAME",
    "icon": "ICON.png",
    "nodes": [
        {
            "name": "OPTIONAL",
            "filepath": "GIZMO.gizmo",
            "icon": "ICON_IN_PLUGINPATH.png",
            "shortcut": "^+R",
            "ctx": 2
        },
        {
            "name": "OPTIONAL",
            "filepath": "SCRIPT.nk",
            "icon": "../PATH/TO/ICON.png",
            "shortcut": "Ctrl+Shift+P"
        },
        {
            "name": "PDF FILENAME",
            "filepath": "../PATH/TO.pdf",
            "icon": "ICON.png"
        },
        {
            "filepath": "python_file.py"
        }
    ]
}
```

When it is ready for general use, there will be more information on how to configure it, in hopes other Nuke Users find this helpful.
