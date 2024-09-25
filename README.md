Created by externo6. v1.0a

By design this is a basic discord music bot that plays from youtube. I built this for my friends as the bot we used to use stopped functioning due to youtube blocking IP's without login, plus its a nice little project for myself.
A small note, I do not plan to provide any support for this, you use this at your own risk.
Another note, my error catching is pretty basic/meh. In reality, I dont really care what the error is just print it and continue. If there is an error its most likely due to a service error or something I f'ed up.

While basic, it can auth via oauth2 to get around youtubes login requirements however this may break TOS so use that feature at your own risk (configurable via config)

Features include: 
* Playing music from Youtube
* Queue system with skipping etc
* 'ish' lyric searching (though in my very minimal testing it wasnt very accurate / gave no results?)
* Supports been in multiple guilds with the same bot.

There are no planned updates. Updates will most likely come when my friends request somethign, or it stops working for whatever reason.

Recommended to use docker though cant see why it cant be used on baremetal (not tested baremetal), check out the Dockerfile for pip packages / system packages required.
If using oauth2 I suggest either using a host mount or perm docker volume for storage as the yt-dlp_cache holds the oauth data, if you dont then you'll need to re-auth everytime the container starts.
In the docker-compose file I use a host mount. If you dont plan to use oauth then ignore this.

Build the compose: docker compose build
Run the compose: docker compose run
This should generate a config.ini in the root of the app. Fill that in with your perfered prefix and docker token, then re-run the bot - If all is well you should have a working basic bot! :)


When using oauth2:
If the yt-dlp_cache does not have the oauth2 token the bot will pause and ask you to login with a link. You should only need to do this once as long as the cache is persistant. 
(I only experienced it asking me to login via oauth2 IF youtube was forcing a login, if not then it just played the music without issue.)