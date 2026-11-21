"""Opt-in macOS in-place update; keeps a rollback copy of the old app."""
from __future__ import annotations

import os
import platform
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile


def installed_macos_app() -> Path | None:
    """Return the existing .app only when running as a packaged macOS app."""
    if platform.system() != "Darwin" or not getattr(sys, "frozen", False):
        return None
    executable = Path(sys.executable).resolve()
    for candidate in executable.parents:
        if candidate.suffix == ".app" and (candidate / "Contents" / "Info.plist").is_file():
            return candidate
    return None


def stage_macos_update(archive: Path) -> Path:
    """Prepare a one-shot external installer which runs after this process exits.

    Never overwrite the currently running binary. The installer copies the new
    bundle beside the old one, swaps them, retains a backup and relaunches.
    """
    app = installed_macos_app()
    if app is None:
        raise RuntimeError("Installation intégrée réservée à l'application macOS .app.")
    if not os.access(app.parent, os.W_OK):
        raise RuntimeError("Le dossier de l'application n'est pas modifiable.")
    if not archive.is_file():
        raise FileNotFoundError(str(archive))
    with ZipFile(archive) as zf:
        names = zf.namelist()
        if not names or any(
            name.startswith("/") or "\\" in name or ".." in Path(name).parts
            for name in names
        ):
            raise ValueError("Archive invalide.")
        bundles = {part for name in names for part in name.split("/")
                   if part.endswith(".app")}
        if bundles != {app.name}:
            raise ValueError("L'archive ne contient pas l'application attendue.")
        if not any(name.startswith(app.name + "/Contents/") for name in names):
            raise ValueError("Application macOS incomplète.")

    work = Path(tempfile.mkdtemp(prefix="wakfu-update-"))
    extracted = work / "extracted"
    extracted.mkdir()
    subprocess.run(["/usr/bin/ditto", "-x", "-k", str(archive), str(extracted)],
                   check=True, capture_output=True, text=True)
    source = extracted / app.name
    if not (source / "Contents" / "Info.plist").is_file():
        raise ValueError("Archive macOS sans application valide.")

    # The shell script is independent of the app, which must first terminate.
    pending = app.parent / (app.name + ".incoming")
    backup = app.parent / (app.name + ".previous")
    script = work / "install.sh"
    q = shlex.quote
    script.write_text(
        "#!/bin/sh\n"
        "set -eu\n"
        f"pid={os.getpid()}\n"
        "count=0\n"
        'while kill -0 "$pid" 2>/dev/null && [ "$count" -lt 60 ]; do\n'
        '  sleep 1\n'
        '  count=$((count + 1))\n'
        'done\n'
        'if kill -0 "$pid" 2>/dev/null; then exit 1; fi\n'
        f"rm -rf {q(str(pending))}\n"
        f"/usr/bin/ditto {q(str(source))} {q(str(pending))}\n"
        f"rm -rf {q(str(backup))}\n"
        f"mv {q(str(app))} {q(str(backup))}\n"
        f"if mv {q(str(pending))} {q(str(app))}; then\n"
        f"  /usr/bin/open {q(str(app))}\n"
        "else\n"
        f"  mv {q(str(backup))} {q(str(app))}\n"
        "  exit 1\n"
        "fi\n",
        encoding="utf-8",
    )
    script.chmod(0o700)
    subprocess.Popen(["/bin/sh", str(script)], start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True)
    return script
