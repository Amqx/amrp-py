import threading
from pystray import Icon, MenuItem, Menu
from PIL import Image

class TrayIcon:
    """
    Class to manage TrayIcon behaviour
    """
    def __init__(self):
        self.thread = None
        self.image = Image.open("assets/app-icon.png")
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
        Starts the tray icon on a separate thread

        :return: None
        """
        self.thread = threading.Thread(target=self.icon.run)
        self.thread.daemon = True
        self.thread.start()

    def quit(self) -> None:
        """
        Quit tray icon using pystray quit method
        :return: None
        """
        self.icon.stop()