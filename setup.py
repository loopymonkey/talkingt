from setuptools import setup

APP = ["mr_t_talker.py"]
DATA_FILES = [
    "MRT_mouth_closed.png",
    "MRT_mouth_open.png",
    "MRT_mouth_A_face.png",
    "MRT_mouth_o_face.png",
    "MRT_mouth_end_1.png",
]
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "TalkingT.icns",
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
    setup_requires=["py2app"],
)
