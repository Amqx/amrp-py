from discord_rp import RPC
from currently_playing import Song
from tray import TrayIcon
import asyncio
import time
import psutil
import logging

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_process_running(process_name: str) -> bool:
    """
    Returns true if process_name is running
    :param process_name: Process name
    :return: True if running, False otherwise
    """
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            return True
    return False

def main():

    # Initial Constants
    REFRESH_INTERVAL = 5
    alive = is_process_running('AppleMusic.exe')
    changed = False

    # Define song object
    active_song = Song()

    # Start tray icon
    icon = TrayIcon()
    icon.run()

    # If Apple Music is running, get the info from it
    if alive:
        asyncio.run(active_song.get_info(changed))
        active_song.convert_thumbnail()
    known = active_song.listview()

    while True:

        changed = False

        # Check if AM is still running, if it is refresh song's info

        alive = is_process_running('AppleMusic.exe')
        if alive:
            asyncio.run(active_song.get_info(changed))

        # Refresh for latest info
        new = active_song.listview()

        # Check for changes
        changed = not (known == new)

        if changed or not alive or None in new:
            # Case 1: Client exited/ AM not running/ Nothing playing => No RPC
            if None in new or not alive:
                logging.info('Case 1: Client exited/ AM not running/ Nothing playing => No RPC')
                try:
                    active_song.pause()
                    discord.rpc.disconnect()
                    active_song.reset()
                    del discord
                    logging.info('Killed and reset RPC')
                except NameError:
                    logging.info('RPC already reset')
                except SystemExit:
                    del discord
                    active_song.reset()
                    logging.info('Caught rpc.disconnect(), RPC resetted')

            # Case 2: User paused the song
            elif known[0] == new[0] and known[1] == new[1] and known[2] == new[2]:
                logging.info('Case 2: Song paused/ unpaused')
                try:
                    active_song.pause()
                    discord.update_activity(active_song)
                except NameError:
                    discord = RPC()
                    discord.update_activity(active_song)

            # Case 3: New song
            else:
                logging.info('Case 3: New song')
                active_song.play()
                asyncio.run(active_song.get_info(changed))   # refresh info to get the hash in case it wasn't grabbed
                active_song.convert_thumbnail()
                try:
                    discord.update_activity(active_song)
                except NameError:
                    discord = RPC()
                    discord.update_activity(active_song)

        # If nothing changed, 2 cases

        else:

            # Same state persisted
            if alive:
                logging.info('Case 4: Same song/ state persisted')
                if not new[3]:
                    logging.info('Retained paused state')
                    active_song.pause()
                else:
                    logging.info('Retained unpaused state')
                    active_song.play()
                try:
                    discord.update_activity(active_song)
                except NameError:
                    discord = RPC()
                    discord.update_activity(active_song)


            # AM stays closed or nothing is playing
            else:
                logging.info('Case 5: Apple Music stayed closed')
                try:
                    active_song.pause()
                    discord.rpc.disconnect()
                    active_song.reset()
                    del discord
                    logging.info('Killed and reset RPC')
                except NameError:
                    logging.info('RPC already reset')
                except SystemExit:
                    del discord
                    active_song.reset()
                    logging.info('Caught rpc.disconnect(), RPC resetted')

        # Refresh variables
        known = new
        time.sleep(REFRESH_INTERVAL)

if __name__ == '__main__':
    try:
        # Run main script
        asyncio.run(main())

    except KeyboardInterrupt:
        logging.info('Shutting down - keyboard interrupt')

        try:
            icon.quit()
        except NameError:
            logging.info('Icon already inactive, skipped')

        try:
            discord.rpc.disconnect()
        except NameError:
            logging.info('RPC already inactive, skipped')

    except SystemExit:
        logging.info('Shutting down - system exit')

        try:
            icon.quit()
        except NameError:
            logging.info('Icon already inactive, skipped')

        try:
            discord.rpc.disconnect()
        except NameError:
            logging.info('RPC already inactive, skipped')