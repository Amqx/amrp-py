# Apple Music Discord Rich Presence

Discord Rich Presence for Apple Music using WinRT APIs.

## Features

- Displays track title, artist, and album
- Shows album art via Imgur uploads
- Progress bar
- Probably works with other clients as well (I haven't tested)

## Requirements

- Windows 10 or later
- Apple Music (Windows) or anything supported by [GlobalSystemMediaTransportControlsSession](https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssession?view=winrt-26100)
- Python 3
- Discord Developer App
- Imgur API Client ID

## Setup

1. **Clone the repository**
    ```bash
    git clone https://github.com/Amqx/amrp-py
    cd amrp-py
    ```

2. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3. **Create a `.env`**
    ```
    DISCORD_CLIENT_ID=your_discord_app_client_id
    IMGUR_CLIENT_ID=your_imgur_client_id
    ```

4. **Run the script**
    ```bash
    python main.py
    ```

##  How it works

Utilize's Windows Runtime APIs to get what is currently playing, specifically [GlobalSystemMediaTransportControlsSession](https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssession?view=winrt-26100). This gives us access to:

- Title, Arist, Album
- Status (Playing, Timestamps)
- Images (as IRandomAccessStreamReference)

We then extract that info, as well as convert the images into a usable type. Because the images are available locally and I don't have any other ideas for images (other than searching applemusic.com), nor do I see a way to extract it from the client, I opted for it to upload the image to Imgur using their API, which returns a usable link for us to put into our rich presence. 
