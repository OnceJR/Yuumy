"""Application entry point for the multistream recorder.

This module configures logging, loads configuration, initialises the database
and kicks off the Qt application.  At startup the user is presented with a
simple consent dialog reminding them to respect terms of service and only
record streams for which they have permission.  If the user does not accept
the terms the application will exit gracefully.

This file intentionally contains only minimal boilerplate to bootstrap
the PySide6 UI.  Most of the logic lives in the packages under
``multirec`` (see ``ui``, ``recorder``, ``scheduler`` and so on).

Run this module directly to start the application:

    python -m multirec.app
"""

import asyncio
import sys
from typing import Optional

from PySide6.QtWidgets import QApplication

from .config.config import Config, load_config
from .db.database import Database
from .ui.main_window import MainWindow
from .utils.logger import configure_logging


async def main_async(config: Config) -> None:
    """Initialises asynchronous services and starts the Qt event loop.

    Args:
        config: Loaded application configuration.
    """
    # Set up the database (create tables if necessary)
    db = Database(config.db_path)
    await db.initialise()

    app = QApplication(sys.argv)
    window = MainWindow(config=config, db=db)
    window.show()

    # Start Qt event loop.  Note that Qt uses its own loop so we run
    # it in a separate thread and integrate it with asyncio.
    loop = asyncio.get_running_loop()
    # Use asyncio to wait until the Qt application quits
    await loop.run_in_executor(None, app.exec)


def main(config_path: Optional[str] = None) -> None:
    """Synchronously loads configuration and starts the event loop."""
    config, _ = load_config(config_path)
    configure_logging(config)
    try:
        asyncio.run(main_async(config))
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        pass


if __name__ == "__main__":
    main()