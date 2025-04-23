import asyncio
from datetime import datetime
import logging
import os
from pathlib import Path
import psutil
import threading
from discord_rp import RPC
from currently_playing import Song
from tray import TrayIcon
from logging.handlers import TimedRotatingFileHandler

def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    file_handler = TimedRotatingFileHandler(PATH, when='midnight')
    file_handler.setFormatter(FORMATTER)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger

def is_process_running(process_name: str) -> bool:
    """
    Check if a process with the given name is currently running.

    Args:
        process_name: The name of the process to check for

    Returns:
        True if the process is running, False otherwise
    """
    logs.debug(f"Checking if process '{process_name}' is running")
    try:
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] == process_name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        logs.error(f"Error checking processes: {e}")
    return False

async def main(stop_event: threading.Event) -> None:
    """
    Main application function that manages the Discord Rich Presence for Apple Music.

    This function initializes the application, monitors Apple Music's playback status,
    and updates Discord Rich Presence accordingly. It runs in an infinite loop,
    periodically checking for changes in the currently playing song.

    Returns:
        None
    """
    logs.info("Starting Apple Music Rich Presence application")

    # Initial Constants
    REFRESH_INTERVAL = 5
    alive = is_process_running('AppleMusic.exe')
    changed = False

    # Define song object
    logs.info("Initializing song tracking")
    active_song = Song()

    # Start tray icon
    logs.info("Setting up system tray icon")
    icon = TrayIcon(stop_event)
    icon.run()

    # If Apple Music is running, get the info from it
    if alive:
        logs.info("Apple Music is running, fetching initial song information")
        await active_song.get_info(changed)
        await active_song.convert_thumbnail()
    known = active_song.listview()
    logs.debug(f"Initial song state: {known}")

    while not stop_event.is_set():
        logs.debug("Starting new refresh cycle")
        changed = False

        # Check if Apple Music is still running. If it is, refresh song's info
        alive = is_process_running('AppleMusic.exe')
        if alive:
            logs.debug("Apple Music is running, refreshing song info")
            await active_song.get_info(changed)
        else:
            logs.debug("Apple Music is not running")

        # Refresh for latest info
        new = active_song.listview()

        # Check for changes
        changed = not (known == new)
        if changed:
            logs.debug(f"Song state changed (title, author, album, playing): {known} -> {new}")
        else:
            logs.debug(f"Song state unchanged (title, author, album, playing): {known}")

        if changed or not alive or None in new:
            # Case 1: Client exited, AM not running, or nothing playing => RPC reset
            if None in new or not alive:
                logs.info('Case 1: Client exited, AM not running, or nothing playing')
                try:
                    active_song.pause()
                    discord.rpc.disconnect()
                    active_song.reset()
                    del discord
                    logs.info('Disconnected from Discord and reset RPC')
                except NameError:
                    logs.info('RPC already reset (not connected)')
                except SystemExit:
                    logs.info('Caught SystemExit from rpc.disconnect(), cleaning up')
                    del discord
                    active_song.reset()
                    logging.info('RPC reset completed')

            # Case 2: User paused the song (same song, different state)
            elif known[0] == new[0] and known[1] == new[1] and known[2] == new[2]:
                logs.info('Case 2: Song paused/unpaused')
                try:
                    active_song.pause()
                    logs.debug('Updating Discord activity with paused state')
                    discord.update_activity(active_song)
                except NameError:
                    logs.info('Creating new Discord RPC connection')
                    discord = RPC()
                    discord.update_activity(active_song)

            # Case 3: New song
            else:
                logs.info('Case 3: New song detected')
                active_song.play()
                # Refresh info to get the hash in case it wasn't grabbed
                logs.debug('Refreshing song info and thumbnail')
                await active_song.get_info(changed)
                await active_song.convert_thumbnail()
                try:
                    logs.debug('Updating Discord activity with new song')
                    discord.update_activity(active_song)
                except NameError:
                    logs.info('Creating new Discord RPC connection')
                    discord = RPC()
                    discord.update_activity(active_song)

        # If nothing changed, handle these cases
        else:
            # Case 4: Same state persisted
            if alive:
                logs.info('Case 4: Same song/state persisted')
                if not new[3]:
                    logs.debug('Maintaining paused state')
                    active_song.pause()
                else:
                    logs.debug('Maintaining playing state')
                    active_song.play()
                try:
                    logs.debug('Refreshing Discord activity')
                    discord.update_activity(active_song)
                except NameError:
                    logs.info('Creating new Discord RPC connection')
                    discord = RPC()
                    discord.update_activity(active_song)

            # Case 5: Apple Music stays closed or nothing is playing
            else:
                logs.info('Case 5: Apple Music remained closed')
                try:
                    active_song.pause()
                    discord.rpc.disconnect()
                    active_song.reset()
                    del discord
                    logs.info('Disconnected from Discord and reset RPC')
                except NameError:
                    logs.debug('RPC already reset (not connected)')
                except SystemExit:
                    logs.info('Caught SystemExit from rpc.disconnect(), cleaning up')
                    del discord
                    active_song.reset()
                    logs.debug('RPC reset completed')

        # Refresh variables
        known = new
        await asyncio.sleep(REFRESH_INTERVAL)

    logs.info("Stopped using Tray option - Gracefully quitting")
    try:
        logs.debug('Attempting to quit tray icon')
        icon.quit()
        logs.debug('Tray icon quit successfully')
    except NameError:
        logs.info('Tray icon not active or already quit, skipping')
    except Exception as e:
        logs.error(f'Error quitting tray icon: {e}')

if __name__ == '__main__':

    # Configure logging
    FORMATTER = logging.Formatter("%(asctime)s :: [%(levelname)s] :: %(message)s")

    app_name = "amrp-py"
    local_appdata = os.getenv('LOCALAPPDATA')
    logs_dir = Path(local_appdata) / app_name / "Logs"

    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    PATH = logs_dir / f"{timestamp}.log"

    logs = get_logger(__name__)

    stop_event = threading.Event()
    try:
        # Run main script
        logs.info("Starting application")
        asyncio.run(main(stop_event))

    except KeyboardInterrupt:
        logs.info('Shutting down - keyboard interrupt detected')

        try:
            logs.debug('Attempting to quit tray icon')
            icon.quit()
            logs.debug('Tray icon quit successfully')
        except NameError:
            logs.info('Tray icon not active or already quit, skipping')
        except Exception as e:
            logs.error(f'Error quitting tray icon: {e}')

        try:
            logs.debug('Attempting to disconnect from Discord')
            discord.rpc.disconnect()
            logs.debug('Discord disconnected successfully')
        except NameError:
            logs.info('Discord RPC not active or already disconnected, skipping')
        except Exception as e:
            logs.error(f'Error disconnecting from Discord: {e}')

        logs.info('Application shutdown complete')

    except SystemExit:
        logs.info('Shutting down - system exit detected')

        try:
            logs.debug('Attempting to quit tray icon')
            icon.quit()
            logs.debug('Tray icon quit successfully')
        except NameError:
            logs.info('Tray icon not active or already quit, skipping')
        except Exception as e:
            logs.error(f'Error quitting tray icon: {e}')

        try:
            logs.debug('Attempting to disconnect from Discord')
            discord.rpc.disconnect()
            logs.debug('Discord disconnected successfully')
        except NameError:
            logs.info('Discord RPC not active or already disconnected, skipping')
        except Exception as e:
            logs.error(f'Error disconnecting from Discord: {e}')

        logs.info('Application shutdown complete')
