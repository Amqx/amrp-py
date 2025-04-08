from winsdk.windows.storage.streams import IRandomAccessStreamReference
from discord_rp import RPC
from currently_playing import Song
import asyncio
import time
import psutil

def is_process_running(process_name):
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

    # If Apple Music is running, get the info from it
    if alive:
        asyncio.run(active_song.get_info(changed))
        active_song.convert_thumbnail()
    known = active_song.listview()
    print(active_song)

    print("Initial setup done!")
    print("-" * 30 + '\n')
    while True:

        print("Loop started!")
        changed = False

        # Check if AM is still running, if it is refresh song's info

        alive = is_process_running('AppleMusic.exe')
        if alive:
            asyncio.run(active_song.get_info(changed))


        print(active_song)

        print('\n')
        print("Alive", alive)
        # Refresh for latest info
        new = active_song.listview()

        # Check for changes
        changed = not (known == new)
        print("Changed", changed)

        # 2 cases: Same song or something changed
        if changed or not alive or None in new:

            # If something changed, 3 cases

            # Case 1: Client exited or AM not running or nothing is playing
            if None in new or not alive:    # playing to exited client or none in info
                print("Case 1: AM not running")
                try:
                    active_song.pause()
                    discord.rpc.disconnect()   # kill discord
                    print("Killed RPC!")
                    active_song.reset()
                    del discord
                except NameError:
                    print("RPC not active! Skipped killing RPC")
                except SystemExit:
                    print("RPC tried to kill the script! Continuing loop")
                    del discord
                    active_song.reset()

            # Case 2: User paused the song
            elif known[0] == new[0] and known[1] == new[1] and known[2] == new[2]:
                print("Case 2: paused")
                try:
                    active_song.pause()
                    discord.update_activity(active_song)
                except NameError:
                    discord = RPC()
                    discord.update_activity(active_song)

            # Case 3: New song
            else:
                print("Case 3: new song")
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
                print("Case 4: same state persisted")
                if not new[3]:
                    active_song.pause()
                else:
                    active_song.play()
                try:
                    discord.update_activity(active_song)
                except NameError:
                    discord = RPC()
                    discord.update_activity(active_song)


            # AM stays closed or nothing is playing
            else:
                print("Case 5: AM stayed closed")
                try:
                    discord.rpc.disconnect()
                    print("Killed RPC!")
                    active_song.reset()
                    del discord
                except NameError:
                    print("RPC not active! Skipped killing RPC")
                except SystemExit:
                    print("RPC tried to kill the script! Continuing loop")
                    del discord
                    active_song.reset()

        # Refresh variables
        print('\n')
        print(active_song)
        known = new
        time.sleep(REFRESH_INTERVAL)
        print("-" * 30 + '\n')

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("-" * 30 + '\n')
        print("Shutting down")
        try:
            discord.rpc.disconnect()
        except NameError:
            print("RPC not active! Skipped stopping RPC")
    except SystemExit:
        print("-" * 30 + '\n')
        print("Shutting down")
        try:
            discord.rpc.disconnect()
        except NameError:
            print("RPC not active! Skipped stopping RPC")

