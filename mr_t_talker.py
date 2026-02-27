#!/usr/bin/env python3
"""Talking T scheduled talker (macOS prototype).

Behavior:
- No permanent UI window.
- 200x200 talking image appears at upper-right only while speaking.
- Controls live in the app menu bar.
- Speech engine prefers Piper if configured; otherwise falls back to macOS `say`.
"""

from __future__ import annotations

import datetime as dt
import os
import random
import shutil
import subprocess
import tempfile
import threading
import time
import tkinter as tk
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
CLOSED_IMAGE = APP_DIR / "MRT_mouth_closed.png"
OPEN_IMAGE = APP_DIR / "MRT_mouth_open.png"
END_IMAGE = APP_DIR / "MRT_mouth_end_1.png"
APP_ICON = APP_DIR / "MRT_mouth_end_1.png"
EXTRA_FRAME_GLOBS = [
    "MRT_mouth_A_face.png",
    "MRT_mouth_o_face.png",
]

PHRASES = [
    "I pity the fool who doesn't believe in themselves.",
    "Treat your mother right.",
    "Be somebody, or be somebody's fool.",
    "Discipline is doing what needs to be done, even when you don't feel like it.",
    "Respect is earned by how you treat people, not how loud you talk.",
    "Strength means protecting people who need help.",
    "Don't wait for perfect. Start now and improve as you go.",
    "Character is what you do when nobody is watching.",
    "You don't need luck when you've got preparation.",
    "Train your mind, and your body will follow.",
    "Kindness and toughness are not opposites.",
    "Small progress every day beats big plans someday.",
]

SAY_VOICE = "Ralph"
SAY_SPEECH_RATE = "150"
IMAGE_SIZE = 200
WINDOW_MARGIN = 20
MOUTH_FLIP_MS = 120
END_POSE_PROBABILITY = 0.16
END_POSE_HOLD_MS = 240

MODES = {
    "Every minute": "minute",
    "Every 10 minutes": "ten_minutes",
    "Hourly on the hour": "hourly",
}


class SpeechEngine:
    def __init__(self) -> None:
        self.say_voice = SAY_VOICE
        self.piper_bin = shutil.which("piper")
        self.piper_model = os.environ.get("PIPER_MODEL_PATH", "").strip()
        self.piper_config = os.environ.get("PIPER_CONFIG_PATH", "").strip()

    def description(self) -> str:
        if self._piper_ready():
            model_name = Path(self.piper_model).name
            return f"Piper ({model_name})"
        return f"say ({self.say_voice})"

    def speak(self, phrase: str) -> None:
        if self._piper_ready():
            self._speak_piper(phrase)
            return
        self._speak_say(phrase)

    def _piper_ready(self) -> bool:
        if not self.piper_bin:
            return False
        if not self.piper_model:
            return False
        return Path(self.piper_model).exists()

    def _speak_say(self, phrase: str) -> None:
        proc = subprocess.Popen(
            ["/usr/bin/say", "-v", self.say_voice, "-r", SAY_SPEECH_RATE, phrase],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        proc.wait()

    def _speak_piper(self, phrase: str) -> None:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name

        try:
            cmd = [self.piper_bin, "--model", self.piper_model, "--output_file", wav_path]
            if self.piper_config and Path(self.piper_config).exists():
                cmd.extend(["--config", self.piper_config])

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            proc.communicate(phrase)

            if proc.returncode != 0:
                self._speak_say(phrase)
                return

            subprocess.run(["afplay", wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        finally:
            try:
                os.remove(wav_path)
            except OSError:
                pass


class MrTTalker:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Talking T")
        self.root.withdraw()  # no permanent app window

        self.is_speaking = False
        self.animation_job: str | None = None
        self.speech_thread: threading.Thread | None = None
        self.selected_mode = tk.StringVar(value="Every 10 minutes")
        self.next_fire: dt.datetime | None = None
        self.engine = SpeechEngine()

        self.closed_img = self._load_scaled_image(CLOSED_IMAGE)
        self.open_img = self._load_scaled_image(OPEN_IMAGE)
        self.end_img = self._load_scaled_image(END_IMAGE) if END_IMAGE.exists() else None
        self.talk_frames = self._load_talk_frames()
        self.frame_index = 0

        self._build_menu()
        self._build_avatar_window()
        self._reset_schedule()
        self._scheduler_tick()

    def _load_scaled_image(self, path: Path) -> tk.PhotoImage:
        raw = tk.PhotoImage(file=str(path))
        # 1024 -> approx 200 using integer subsample.
        factor = max(1, round(raw.width() / IMAGE_SIZE))
        return raw.subsample(factor, factor)

    def _load_talk_frames(self) -> list[tk.PhotoImage]:
        frames: list[tk.PhotoImage] = [self.open_img]
        for filename in EXTRA_FRAME_GLOBS:
            frame_path = APP_DIR / filename
            if frame_path.exists():
                frames.append(self._load_scaled_image(frame_path))
        return frames

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        app_menu = tk.Menu(menubar, tearoff=0)
        app_menu.add_command(label="Speak now", command=self.speak_now)
        app_menu.add_separator()

        schedule_menu = tk.Menu(app_menu, tearoff=0)
        for label in MODES:
            schedule_menu.add_radiobutton(
                label=label,
                variable=self.selected_mode,
                value=label,
                command=self._on_mode_change,
            )
        app_menu.add_cascade(label="Schedule", menu=schedule_menu)

        app_menu.add_separator()
        app_menu.add_command(label="Quit", command=self.root.quit)

        menubar.add_cascade(label="Talking T", menu=app_menu)
        self.root.config(menu=menubar)

    def _build_avatar_window(self) -> None:
        self.avatar = tk.Toplevel(self.root)
        self.avatar.withdraw()
        self.avatar.overrideredirect(True)
        self.avatar.configure(bg="#e8e8e8")
        self.avatar.attributes("-topmost", True)

        self.face_label = tk.Label(self.avatar, image=self.closed_img, bd=0, bg="#e8e8e8")
        self.face_label.pack()

    def _place_avatar_upper_right(self) -> None:
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        x = max(0, screen_w - IMAGE_SIZE - WINDOW_MARGIN)
        y = WINDOW_MARGIN
        self.avatar.geometry(f"{IMAGE_SIZE}x{IMAGE_SIZE}+{x}+{y}")

    def _compute_next_fire(self, now: dt.datetime) -> dt.datetime:
        mode_key = MODES[self.selected_mode.get()]
        base = now.replace(second=0, microsecond=0)

        if mode_key == "minute":
            return base + dt.timedelta(minutes=1)

        if mode_key == "hourly":
            return (base + dt.timedelta(hours=1)).replace(minute=0)

        minute_bucket = (base.minute // 10) * 10
        candidate = base.replace(minute=minute_bucket)
        if candidate <= now:
            candidate += dt.timedelta(minutes=10)
        return candidate

    def _reset_schedule(self) -> None:
        now = dt.datetime.now()
        self.next_fire = self._compute_next_fire(now)

    def _on_mode_change(self) -> None:
        self._reset_schedule()

    def _scheduler_tick(self) -> None:
        now = dt.datetime.now()
        if self.next_fire and now >= self.next_fire and not self.is_speaking:
            self.speak_now()
            self.next_fire = self._compute_next_fire(dt.datetime.now())

        self.root.after(500, self._scheduler_tick)

    def _show_avatar(self) -> None:
        self._place_avatar_upper_right()
        self.avatar.deiconify()
        self.avatar.lift()
        self.avatar.attributes("-topmost", True)

    def _hide_avatar(self) -> None:
        self.avatar.withdraw()

    def _start_animation(self) -> None:
        self.is_speaking = True
        self.frame_index = 0
        self._show_avatar()
        self._animate_mouth()

    def _animate_mouth(self) -> None:
        if not self.is_speaking:
            self.face_label.config(image=self.closed_img)
            return

        frame = self.talk_frames[self.frame_index % len(self.talk_frames)]
        self.face_label.config(image=frame)
        self.frame_index += 1
        self.animation_job = self.root.after(MOUTH_FLIP_MS, self._animate_mouth)

    def _stop_animation(self) -> None:
        self.is_speaking = False
        if self.animation_job:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None
        if self.end_img and random.random() < END_POSE_PROBABILITY:
            self.face_label.config(image=self.end_img)
            self.root.after(END_POSE_HOLD_MS, self._hide_avatar)
            return

        self.face_label.config(image=self.closed_img)
        self._hide_avatar()

    def speak_now(self) -> None:
        if self.is_speaking:
            return

        phrase = random.choice(PHRASES)
        self._start_animation()

        def _run() -> None:
            try:
                self.engine.speak(phrase)
            finally:
                self.root.after(0, self._stop_animation)

        self.speech_thread = threading.Thread(target=_run, daemon=True)
        self.speech_thread.start()


def main() -> None:
    if not CLOSED_IMAGE.exists() or not OPEN_IMAGE.exists():
        missing = []
        if not CLOSED_IMAGE.exists():
            missing.append(CLOSED_IMAGE.name)
        if not OPEN_IMAGE.exists():
            missing.append(OPEN_IMAGE.name)
        raise SystemExit(f"Missing image file(s): {', '.join(missing)}")

    root = tk.Tk()
    if APP_ICON.exists():
        try:
            root.iconphoto(True, tk.PhotoImage(file=str(APP_ICON)))
        except Exception:
            pass
    MrTTalker(root)
    root.mainloop()


if __name__ == "__main__":
    main()
