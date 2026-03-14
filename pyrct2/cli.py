"""CLI entry point for pyrct2."""

import urllib.request

import click

from pyrct2.paths import (
    find_openrct2_binary,
    get_plugin_dir,
    save_config,
    validate_openrct2_binary,
)

BRIDGE_VERSION = "v1.0.1"
BRIDGE_FILENAME = "openrct2-bridge.js"
BRIDGE_DOWNLOAD_URL = f"https://github.com/MaukWM/openrct2-bridge/releases/download/{BRIDGE_VERSION}/{BRIDGE_FILENAME}"


@click.group()
def main() -> None:
    """pyrct2 — Python client for OpenRCT2."""


@main.command()
def setup() -> None:
    """Download and install the openrct2-bridge plugin."""
    # Find and validate OpenRCT2 binary
    click.echo("Searching for OpenRCT2...")
    binary = find_openrct2_binary()
    if binary is None:
        click.echo("Could not find OpenRCT2. Please install it or set PYRCT2_OPENRCT2_PATH.")
        return

    version = validate_openrct2_binary(binary)
    save_config({"openrct2_path": str(binary)})
    click.echo(f"Found {version} at {binary}")

    # Install bridge plugin
    plugin_dir = get_plugin_dir()
    plugin_dir.mkdir(parents=True, exist_ok=True)
    dest = plugin_dir / BRIDGE_FILENAME

    click.echo(f"Downloading {BRIDGE_FILENAME} {BRIDGE_VERSION}...")
    urllib.request.urlretrieve(BRIDGE_DOWNLOAD_URL, dest)
    click.echo(f"Installed to {dest}")
