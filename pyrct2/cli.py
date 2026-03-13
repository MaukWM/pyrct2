"""CLI entry point for pyrct2."""

import urllib.request
from pathlib import Path

import click

from pyrct2.paths import get_plugin_dir

BRIDGE_VERSION = "v1.0.0"
BRIDGE_FILENAME = "openrct2-bridge.js"
BRIDGE_DOWNLOAD_URL = (
    f"https://github.com/MaukWM/openrct2-bridge/releases/download/{BRIDGE_VERSION}/{BRIDGE_FILENAME}"
)


@click.group()
def main() -> None:
    """pyrct2 — Python client for OpenRCT2."""


@main.command()
def setup() -> None:
    """Download and install the openrct2-bridge plugin."""
    plugin_dir = get_plugin_dir()
    plugin_dir.mkdir(parents=True, exist_ok=True)
    dest = plugin_dir / BRIDGE_FILENAME

    click.echo(f"Downloading {BRIDGE_FILENAME} {BRIDGE_VERSION}...")
    urllib.request.urlretrieve(BRIDGE_DOWNLOAD_URL, dest)
    click.echo(f"Installed to {dest}")
