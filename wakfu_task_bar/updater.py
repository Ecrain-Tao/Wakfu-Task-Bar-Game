"""Public GitHub Releases update discovery and safe download (no code execution)."""
from __future__ import annotations

import json
import platform
import re
import ssl
import urllib.request

import certifi
from pathlib import Path

# Releases embed the user-selected version before PyInstaller packages the app.
# Source checkouts retain this fallback for local development.
try:
    from ._build_version import VERSION
except ModuleNotFoundError as exc:
    if exc.name != __package__ + "._build_version":
        raise
    VERSION = "0.3.0-alpha"
RELEASES_ROOT = "https://api.github.com/repos/Ecrain-Tao/Wakfu-Task-Bar-Game-Releases/releases"
RELEASES_API = RELEASES_ROOT + "/latest"
USER_AGENT = "Wakfu-Task-Bar-Game/" + VERSION


def version_parts(version: str) -> tuple[int, int, int, int]:
    """Comparable release tuple: prerelease sorts before the same stable version."""
    clean = version.strip().removeprefix("v")
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:-(alpha|beta|rc)(?:\.(\d+))?)?", clean)
    if not match:
        raise ValueError("Numéro de version invalide")
    major, minor, patch, stage, number = match.groups()
    order = {"alpha": 0, "beta": 1, "rc": 2, None: 3}
    return int(major), int(minor), int(patch), order[stage] * 100000 + int(number or 0)


def tls_context():
    """Verify HTTPS with a bundled, maintained CA trust bundle."""
    return ssl.create_default_context(cafile=certifi.where())


def check_latest(channel: str = "stable") -> dict:
    """Stable uses GitHub latest; experimental includes prereleases, never drafts."""
    if channel not in ("stable", "experimental"):
        raise ValueError("Canal de mise à jour invalide")
    endpoint = RELEASES_API if channel == "stable" else RELEASES_ROOT + "?per_page=100"
    request = urllib.request.Request(
        endpoint, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    )
    with urllib.request.urlopen(request, timeout=12, context=tls_context()) as response:
        data = json.load(response)
    releases = data if isinstance(data, list) else [data]
    candidates = []
    for release in releases:
        if release.get("draft") or (channel == "stable" and release.get("prerelease")):
            continue
        try:
            key = version_parts(release.get("tag_name", ""))
        except ValueError:
            continue
        candidates.append((key, release))
    if not candidates:
        raise RuntimeError("Aucune version disponible pour ce canal.")
    _, selected = max(candidates, key=lambda item: item[0])
    tag = selected["tag_name"]
    system = platform.system()
    suffix = "-Windows.zip" if system == "Windows" else "-macOS-Intel.zip" if system == "Darwin" else None
    if suffix is None:
        raise RuntimeError("Les mises à jour ne sont disponibles que sur macOS et Windows.")
    asset = next((a for a in selected.get("assets", []) if a.get("name", "").endswith(suffix)), None)
    return {
        "tag": tag, "newer": version_parts(tag) > version_parts(VERSION),
        "asset": asset, "page": selected.get("html_url", ""),
        "notes": selected.get("body", ""), "channel": channel,
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
        with urllib.request.urlopen(request, timeout=30, context=tls_context()) as response, partial.open("wb") as stream:
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
