#!/usr/bin/env python3
"""Play an existing audio file with an available platform command."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def player_command(path: Path) -> list[str] | None:
    system = platform.system()
    if system == "Darwin" and shutil.which("afplay"):
        return ["afplay", str(path)]
    if system == "Linux":
        candidates = (
            ("ffplay", ["ffplay", "-nodisp", "-autoexit", str(path)]),
            ("mpv", ["mpv", "--no-video", str(path)]),
            ("xdg-open", ["xdg-open", str(path)]),
        )
        for executable, command in candidates:
            if shutil.which(executable):
                return command
    if system == "Windows":
        powershell = shutil.which("powershell") or shutil.which("pwsh")
        if powershell:
            return [powershell, "-NoProfile", "-Command", "Start-Process", str(path)]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path, help="Audio file to play")
    args = parser.parse_args()

    path = args.audio.expanduser().resolve()
    if not path.is_file():
        parser.error(f"audio file does not exist: {path}")
    if path.stat().st_size == 0:
        parser.error(f"audio file is empty: {path}")

    if platform.system() == "Windows" and hasattr(os, "startfile"):
        os.startfile(path)  # type: ignore[attr-defined]
        print(f"Playback started: {path}")
        return 0

    command = player_command(path)
    if command is None:
        print(
            f"No supported audio player found. Audio remains available at: {path}",
            file=sys.stderr,
        )
        return 1

    try:
        completed = subprocess.run(command, check=False)
    except OSError as exc:
        print(f"Unable to start audio player: {exc}", file=sys.stderr)
        return 1
    if completed.returncode != 0:
        print(
            f"Audio player exited with status {completed.returncode}. Audio remains at: {path}",
            file=sys.stderr,
        )
        return 1

    print(f"Playback completed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
