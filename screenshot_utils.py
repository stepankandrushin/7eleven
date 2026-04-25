"""Capture phone screenshots into a dated, timestamped path."""

import subprocess
from datetime import datetime
from pathlib import Path


def take_screenshot() -> Path:
    """Pull a screenshot from the device and return the local path.

    Saves to screenshots/YYYY-mm-dd/screen-YYYY-mm-dd-HH-mm-ss-msc.png.
    Uses a per-call filename on /sdcard so concurrent runs don't race.
    """
    now = datetime.now()
    day = now.strftime("%Y-%m-%d")
    ts = now.strftime("%Y-%m-%d-%H-%M-%S-") + f"{now.microsecond // 1000:03d}"
    shot_dir = Path("screenshots") / day
    shot_dir.mkdir(parents=True, exist_ok=True)
    shot_path = shot_dir / f"screen-{ts}.png"

    device_path = f"/sdcard/screen-{ts}.png"
    try:
        subprocess.run(["adb", "shell", "screencap", "-p", device_path], check=True)
        subprocess.run(["adb", "pull", device_path, str(shot_path)], check=True)
    finally:
        subprocess.run(["adb", "shell", "rm", "-f", device_path], check=False)
    return shot_path
