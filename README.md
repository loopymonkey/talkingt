# Talking T (v2 prototype)

A minimal macOS desktop prototype inspired by Talking Moose behavior.

## Behavior

- No permanent window UI.
- Controls are in the app menu bar (`Talking T` menu).
- A `200x200` Mr. T image appears in the upper-right while speaking.
- After speaking, the image hides again.

## Run (dev mode)

```bash
cd /Users/rossj/Documents/DEVELOPMENT/ChatGMRT
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

```bash
cd /Users/rossj/Documents/DEVELOPMENT/ChatGMRT
python3 -m pip install --upgrade pip setuptools py2app
python3 setup.py py2app
```

Result:

- App bundle at: `dist/Talking T.app`

You can then launch it from Finder or keep it in Applications.
