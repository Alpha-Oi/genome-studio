"""Точка входа Genome Studio backend."""

from __future__ import annotations

import sys

import typer
from rich.console import Console

from genome_studio import __version__
from genome_studio.build_resolver import resolve_build
from genome_studio.config import get_settings

app = typer.Typer(
    name="genome-studio",
    help="Genome Studio backend CLI",
    no_args_is_help=True,
)

console = Console()


@app.command()
def version() -> None:
    """Показать версию и режим сборки."""
    info = resolve_build()
    console.print(f"[bold]Genome Studio[/] v{__version__}")
    console.print(f"Build mode: [cyan]{info.mode.value}[/]")
    console.print(f"Dev override available: {info.dev_override_available}")
    console.print(f"Signing key present: {info.signing_key_present}")
    console.print(f"Isolated environment: {info.isolated_environment}")
    if info.reasons:
        console.print("Reasons:")
        for r in info.reasons:
            console.print(f"  - {r}")


@app.command()
def info() -> None:
    """Показать конфигурацию."""
    settings = get_settings()
    console.print(f"App: {settings.app_name}")
    console.print(f"Debug: {settings.debug}")
    console.print(f"Build mode: {settings.build_mode.value}")
    console.print(f"Data dir: {settings.data_dir}")
    console.print(f"Log dir: {settings.log_dir}")


@app.command()
def serve(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False,
) -> None:
    """Запустить API-сервер."""
    import uvicorn

    uvicorn.run(
        "genome_studio.api.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


def main() -> None:
    """Точка входа."""
    try:
        app()
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
