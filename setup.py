from pathlib import Path
import sys
import tkinter
from setuptools import setup

if sys.version_info >= (3, 14):
    raise SystemExit("py2app build is not supported on Python 3.14 yet. Use Python 3.9-3.13 with tkinter.")


def detect_tcl_tk_resources() -> list[str]:
    resources: list[str] = []
    try:
        tcl_lib = Path(tkinter.Tcl().eval("info library")).resolve()
        tk_lib = tcl_lib.parent / f"tk{tkinter.TkVersion:.1f}"
        if tcl_lib.exists():
            resources.append(str(tcl_lib))
        if tk_lib.exists():
            resources.append(str(tk_lib))
    except Exception:
        pass
    return resources


APP = ["mr_t_talker.py"]
DATA_FILES = [
    "ICON.png",
    "MRT_mouth_closed.png",
    "MRT_mouth_open.png",
    "MRT_mouth_A_face.png",
    "MRT_mouth_o_face.png",
    "MRT_mouth_end_1.png",
]
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "TalkingT.icns",
    "resources": detect_tcl_tk_resources(),
    "plist": {
        "CFBundleName": "Talking T",
        "CFBundleDisplayName": "Talking T",
        "CFBundleIdentifier": "com.loopymonkey.talkingt",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "1",
        "LSMinimumSystemVersion": "12.0",
    },
    "packages": [],
}

setup(
    app=APP,
    name="Talking T",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
)
