Created by externo6. v1.1

By design this is a basic discord music bot that plays from youtube. I built this for my friends as the bot we used to use stopped functioning due to youtube blocking IP's without login, plus its a nice little project for myself.
A small note, I do not plan to provide any support for this, you use this at your own risk.
Another note, my error catching is pretty basic/meh. In reality, I dont really care what the error is just print it and continue. If there is an error its most likely due to a service error or something I f'ed up.

While basic, it can auth via cookies to get around youtubes login requirements however this may break TOS so use that feature at your own risk (configurable via config)

Features include: 
* Playing music from Youtube
* Queue system with skipping etc
* 'ish' lyric searching (though in my very minimal testing it wasnt very accurate / gave no results?)
* Supports been in multiple guilds with the same bot.

There are no planned updates. Updates will most likely come when my friends request something, or it stops working for whatever reason.

Recommended to use docker though cant see why it cant be used on baremetal (not tested baremetal), check out the Dockerfile for pip packages / system packages required.

Build the compose: docker compose build
Run the compose: docker compose run
This should generate a config.ini in the root of the app. Fill that in with your perfered prefix and docker token, then re-run the bot - If all is well you should have a working basic bot! :)


oauth2 is no longer supported due to https://github.com/yt-dlp/yt-dlp/issues/11462

When using cookie:
Cookie file is required, cookie.txt needs to be to put in /app/ (same as config.ini)
https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies