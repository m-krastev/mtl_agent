# MTL Agent for Media Processing

This repository contains the code for a Machine Translation (MTL) agent that can perform automatic translation, subtitle extraction, video encoding, and thumbnail generation.
Contrary to its name, it does not contain formal code for MTL (yet), it only interacts with API services to perform the translation.

## Features

- **Automatic Translation**: Translates text from one language (usually English) to another (Bulgarian).
- **Subtitle Extraction**: Uses FFmpeg to extract subtitles from video files.
- **Video Encoding**: Encodes videos in different formats.
- **Thumbnail Generation**: Automatically generates thumbnails from videos.
- **Video upload**: Uploads videos to Vbox7 currently.
- **Full pipeline**: All of the above features can be used in a single pipeline.

To get a feel for it, run `mtl_agent --help`

Currently a hobby project that combines most of my post-translation workflow into a single tool that
automates away encode and upload!

## Installation

To install the package, run:
```
pip install mtl_agent
```

Additionally, if the upload functionality is to be used, you must install the playwright browser:
```
playwright install
```

## Configuration

The agent is configurable and may need credentials.
Those are stored by default under the user's home directory at `~/.config/mtl_agent`, but can be adjusted using the `--root` flag before all options.
If you opt to use DeepL's API, you must provide an API key, which can be obtained from their website. The key can be provided as a field inside the `secrets.json` file located at the project settings/root directory. The file should look like this:
```
{
    "deepl_api_key": "YOUR_API_KEY"
}
```
If Google's translation service is used, your `secrets.json` file should include the `project_id` field. 

> [!TIP]
> The file can contain both.

----------------

For automatic upload to the available websites, Playwright is used to orchestrate the uploading functionality. 

The program will look for a `profile_default.json` file at the configuration root. You **must** manually copy the cookies from your browser into the file. The cookies are used to authenticate the user and allow the program to upload videos to the services.

The file (currently) should look like the following:
```
{
    "vbox7remember": "VBOX7REMEMBER_COOKIE,
    "larabox_session": "LARABOX_SESSION_COOKIE",
    "ukey": "ANIMES_PORTAL_UKEY",
}
```

> [!NOTE]
> The available websites to upload to are currently limited, but more eager contributors are welcome to add more!

> [!CAUTION]
> Be very careful if you are storing your credentials in a public repository/dotfiles store. 


----------------
As a hobby project, this is not actively maintained, and extensive instructions might not be available. If you have any questions on how to get started or how to contribute, feel free to open a PR, or simply reach out.