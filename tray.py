import threading
import logging
from pystray import Icon, MenuItem, Menu
from PIL import Image

class TrayIcon:
    """
    Class to manage system tray icon behavior.

    This class creates and manages a system tray icon that displays the application
    status and provides a menu for basic actions like quitting the application.
    """
    def __init__(self, stop_event: threading.Event) -> None:
        """
        Initialize the tray icon with default settings.

        Creates a new tray icon with the application icon and a simple menu.
        """
        logging.info("Initializing system tray icon")
        self.thread = None
        self.stop_event = stop_event
        try:
            self.image = Image.open("assets/app-icon.png")
            logging.debug("Loaded tray icon image")
        except Exception as e:
            logging.error(f"Failed to load tray icon image: {e}")
            raise

        self.name = "amrp-py"
        self.icon = Icon(
            self.name,
            icon=self.image,
            title=self.name,
            menu=[
                MenuItem('amrp-py — Running', lambda: None, enabled=False),
                Menu.SEPARATOR,
                MenuItem("Quit", self.quit)
            ]
        )

    def run(self) -> None:
        """
        Start the tray icon on a separate daemon thread.

        This method starts the tray icon in a background thread so it doesn't
        block the main application.

        Returns:
            None
        """
        logging.info("Starting tray icon in background thread")
        self.thread = threading.Thread(target=self.icon.run)
        self.thread.daemon = True
        self.thread.start()
        logging.debug("Tray icon thread started")

    def quit(self) -> None:
        """
        Quit the application by stopping the tray icon.

        This method is called when the user selects "Quit" from the tray menu.

        Returns:
            None
        """
        logging.info("Quitting application from tray icon")
        self.icon.stop()
        self.stop_event.set()
