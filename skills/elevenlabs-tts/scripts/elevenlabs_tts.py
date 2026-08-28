#!/usr/bin/env python3
"""Generate and validate an MP3 through the ElevenLabs text-to-speech API."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote, urlparse

MINIMUM_CURL = (7, 76, 0)
DEFAULT_BASE_URL = "https://api.elevenlabs.io/v1/text-to-speech"
# Neutral narration baseline; callers can tune these documented 0..1 controls.
DEFAULT_STABILITY = 0.5
# Moderately strong voice matching without forcing maximum similarity.
DEFAULT_SIMILARITY_BOOST = 0.75


def fail(message: str, exit_code: int = 2) -> "NoReturn":
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def curl_version() -> tuple[int, int, int]:
    executable = shutil.which("curl")
    if not executable:
        fail("curl is not installed")
    completed = subprocess.run(
        [executable, "--version"], capture_output=True, text=True, check=False
    )
    match = re.search(r"\bcurl\s+(\d+)\.(\d+)\.(\d+)", completed.stdout)
    if completed.returncode != 0 or not match:
        fail("unable to determine curl version")
    version = tuple(int(part) for part in match.groups())
    if version < MINIMUM_CURL:
        fail("curl 7.76.0 or newer is required for --fail-with-body")
    return version


def is_loopback(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {"127.0.0.1", "localhost", "::1"}


def read_text(args: argparse.Namespace) -> str:
    if args.text is not None:
        value = args.text
    else:
        try:
            value = args.text_file.expanduser().read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            fail(f"unable to read narration file: {exc}")
    if not value.strip():
        fail("narration text is empty")
    return value


def parse_content_type(headers: str) -> str:
    matches = re.findall(r"(?im)^content-type:\s*([^;\r\n]+)", headers)
    return matches[-1].strip().lower() if matches else ""


def mp3_signature_valid(path: Path) -> bool:
    with path.open("rb") as handle:
        prefix = handle.read(3)
    return prefix == b"ID3" or (
        len(prefix) >= 2 and prefix[0] == 0xFF and (prefix[1] & 0xE0) == 0xE0
    )


def error_detail(path: Path) -> str:
    try:
        raw = path.read_text(encoding="utf-8")[:4096]
    except (OSError, UnicodeError):
        return ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw.strip()
    detail = payload.get("detail") if isinstance(payload, dict) else None
    if isinstance(detail, dict):
        return str(detail.get("message") or detail.get("status") or detail)
    return str(detail or payload)


def status_message(status: int) -> str:
    if status in {401, 403}:
        return "API key is invalid or unauthorized"
    if status in {400, 422}:
        return "voice, model, text, or request parameters are invalid"
    if status == 429:
        return "quota, rate limit, or billing limit was reached"
    if 500 <= status <= 599:
        return "ElevenLabs service failure"
    return "request failed"


def escape_curl_config(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    text_group = parser.add_mutually_exclusive_group(required=True)
    text_group.add_argument("--text", help="Short narration text")
    text_group.add_argument("--text-file", type=Path, help="UTF-8 narration file")
    parser.add_argument("--output", type=Path, required=True, help="Destination .mp3")
    parser.add_argument("--voice-id", default=os.getenv("ELEVENLABS_VOICE_ID"))
    parser.add_argument("--model-id", default="eleven_multilingual_v2")
    parser.add_argument("--stability", type=float, default=DEFAULT_STABILITY)
    parser.add_argument("--similarity-boost", type=float, default=DEFAULT_SIMILARITY_BOOST)
    parser.add_argument("--approve-paid-use", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--play", action="store_true")
    args = parser.parse_args()

    if not args.voice_id:
        fail("--voice-id or ELEVENLABS_VOICE_ID is required")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.voice_id):
        fail("voice ID contains unsupported characters")
    if not args.model_id.strip():
        fail("model ID is empty")
    if not 0 <= args.stability <= 1:
        fail("--stability must be between 0 and 1")
    if not 0 <= args.similarity_boost <= 1:
        fail("--similarity-boost must be between 0 and 1")
    if args.timeout < 1:
        fail("--timeout must be a positive integer")

    output = args.output.expanduser().resolve()
    if output.suffix.lower() != ".mp3":
        fail("output path must end in .mp3")
    if output.exists() and not args.force:
        fail(f"refusing to overwrite existing output without --force: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    loopback = is_loopback(args.base_url)
    if not loopback and not args.approve_paid_use:
        fail("live generation requires --approve-paid-use")
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        fail("ELEVENLABS_API_KEY is not set")

    text = read_text(args)
    curl_version()
    payload = {
        "text": text,
        "model_id": args.model_id,
        "voice_settings": {
            "stability": args.stability,
            "similarity_boost": args.similarity_boost,
        },
    }
    endpoint = f"{args.base_url.rstrip('/')}/{quote(args.voice_id, safe='')}"

    temporary_paths: list[Path] = []
    try:
        def temporary(suffix: str) -> Path:
            descriptor, name = tempfile.mkstemp(
                prefix=f".{output.name}.", suffix=suffix, dir=output.parent
            )
            os.close(descriptor)
            path = Path(name)
            temporary_paths.append(path)
            return path

        body_path = temporary(".json")
        header_path = temporary(".headers")
        audio_path = temporary(".response")
        config_path = temporary(".curl-config")

        body_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        config_path.write_text(
            f'header = "xi-api-key: {escape_curl_config(api_key)}"\n', encoding="utf-8"
        )
        config_path.chmod(stat.S_IRUSR | stat.S_IWUSR)

        command = [
            "curl",
            "--config",
            str(config_path),
            "--silent",
            "--show-error",
            "--fail-with-body",
            "--location",
            "--connect-timeout",
            "10",
            "--max-time",
            str(args.timeout),
            "--dump-header",
            str(header_path),
            "--output",
            str(audio_path),
            "--header",
            "Content-Type: application/json",
            "--data-binary",
            f"@{body_path}",
            "--write-out",
            "%{http_code}",
            endpoint,
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        try:
            status = int(completed.stdout[-3:])
        except (ValueError, IndexError):
            status = 0

        if completed.returncode != 0 or not 200 <= status <= 299:
            detail = error_detail(audio_path)
            reason = status_message(status) if status else "curl request failed"
            suffix = f": {detail}" if detail else ""
            fail(f"{reason} (HTTP {status or 'unknown'}; curl {completed.returncode}){suffix}", 1)

        headers = header_path.read_text(encoding="iso-8859-1")
        content_type = parse_content_type(headers)
        if not content_type.startswith("audio/"):
            detail = error_detail(audio_path)
            suffix = f": {detail}" if detail else ""
            fail(f"unexpected response content type {content_type or 'missing'}{suffix}", 1)
        if audio_path.stat().st_size == 0:
            fail("API returned an empty audio response", 1)
        if not mp3_signature_valid(audio_path):
            fail("response does not have a recognized MP3 signature", 1)

        os.replace(audio_path, output)
        temporary_paths.remove(audio_path)
        played = False
        playback_error = None
        if args.play:
            player = Path(__file__).with_name("play_audio.py")
            playback = subprocess.run([sys.executable, str(player), str(output)], check=False)
            played = playback.returncode == 0
            if not played:
                playback_error = "audio was generated, but playback was unavailable or failed"

        result = {
            "ok": True,
            "output": str(output),
            "bytes": output.stat().st_size,
            "contentType": content_type,
            "played": played,
        }
        if playback_error:
            result["playbackWarning"] = playback_error
        if args.json_output:
            print(json.dumps(result, sort_keys=True))
        else:
            print(
                f"Generated MP3: {output} ({result['bytes']} bytes; {content_type})"
            )
            if playback_error:
                print(f"WARNING: {playback_error}", file=sys.stderr)
        return 0
    finally:
        for path in temporary_paths:
            try:
                path.unlink()
            except FileNotFoundError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
