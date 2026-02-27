# Talking T (v2 prototype)

A minimal macOS desktop prototype inspired by Talking Moose behavior.

## Behavior

- No permanent window UI.
- Controls are in the app menu bar (`Talking T` menu).
- A `200x200` Mr. T image appears in the upper-right while speaking.
- After speaking, the image hides again.

## Run (dev mode)

```bash
cd /Users/rossj/Documents/DEVELOPMENT/TalkingT
python3 mr_t_talker.py
```

## Menu controls

- `Speak now`
- `Schedule`:
  - Every minute
  - Every 10 minutes (default)
  - Hourly on the hour
- `Quit`

## Voice engine

- Default: macOS `say` with hard-coded voice `Ralph`.
- Optional Piper mode: if `piper` is installed and `PIPER_MODEL_PATH` is set to a valid model file, Piper is used automatically.

Optional environment variables:

- `PIPER_MODEL_PATH=/absolute/path/to/model.onnx`
- `PIPER_CONFIG_PATH=/absolute/path/to/model.onnx.json`

## Build a clickable macOS app (.app)

`py2app` is currently not compatible with Python 3.14. Use Python 3.9-3.13 that has `tkinter` available.

Quick check:

```bash
pythonX.Y -c "import _tkinter; print('tk ok')"
```

Recommended working flow on this machine (system Python 3.9):

```bash
cd /Users/rossj/Documents/DEVELOPMENT/TalkingT
/usr/bin/python3 -m venv .venv39
source .venv39/bin/activate
python -m pip install --upgrade pip setuptools wheel py2app
rm -rf .eggs build dist
python setup.py py2app
```

Result:

- App bundle at: `dist/Talking T.app`

You can then launch it from Finder or keep it in Applications.
