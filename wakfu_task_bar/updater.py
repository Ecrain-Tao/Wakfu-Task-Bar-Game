"""Public GitHub Releases update discovery and safe download (no code execution)."""
from __future__ import annotations

import json
import platform
import re
import urllib.request
from pathlib import Path

VERSION = "0.2.0"
RELEASES_API = "https://api.github.com/repos/Ecrain-Tao/Wakfu-Task-Bar-Game-Releases/releases/latest"
USER_AGENT = "Wakfu-Task-Bar-Game/" + VERSION


def version_parts(version: str) -> tuple[int, ...]:
    clean = version.strip().removeprefix("v")
    if not re.fullmatch(r"\d+(?:\.\d+){0,3}", clean):
        raise ValueError("Numéro de version invalide")
    return tuple(int(p) for p in clean.split("."))


def check_latest() -> dict:
    request = urllib.request.Request(
        RELEASES_API, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        data = json.load(response)
    tag = data.get("tag_name", "")
    latest = version_parts(tag)
    current = version_parts(VERSION)
    system = platform.system()
    suffix = "-Windows.zip" if system == "Windows" else "-macOS-Intel.zip" if system == "Darwin" else None
    if suffix is None:
        raise RuntimeError("Les mises à jour ne sont disponibles que sur macOS et Windows.")
    asset = next((a for a in data.get("assets", []) if a.get("name", "").endswith(suffix)), None)
    return {
        "tag": tag, "newer": latest > current, "asset": asset,
        "page": data.get("html_url", ""), "notes": data.get("body", "")
    }


def download_asset(asset: dict, destination: Path, progress=None) -> Path:
    url = asset.get("browser_download_url", "")
    name = asset.get("name", "")
    if not url.startswith("https://github.com/Ecrain-Tao/Wakfu-Task-Bar-Game-Releases/releases/download/"):
        raise ValueError("Adresse de téléchargement non autorisée")
    if not re.fullmatch(r"Wakfu-Task-Bar-Game-(?:Windows|macOS-Intel)\.zip", name):
        raise ValueError("Nom de fichier non autorisé")
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / name
    partial = destination / (name + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response, partial.open("wb") as stream:
            total = int(response.headers.get("Content-Length", "0"))
            received = 0
            while True:
                chunk = response.read(128 * 1024)
                if not chunk:
                    break
                stream.write(chunk)
                received += len(chunk)
                if progress:
                    progress(received, total)
        partial.replace(output)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return output
