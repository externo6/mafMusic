FROM python:3.12

# install ffmpeg
RUN apt-get update -y
RUN apt-get install -y ffmpeg

# Install Discord and related.
RUN pip install --no-cache-dir discord youtube-search-python PyNaCl azapi ffmpeg

# Install master of yt-dlp
RUN pip install --no-cache-dir https://github.com/yt-dlp/yt-dlp/archive/master.tar.gz

# Install OAuth2 plugin for yt-dlp
RUN pip install --no-cache-dir -U https://github.com/coletdjnz/yt-dlp-youtube-oauth2/archive/refs/heads/master.zip

WORKDIR /app/

# Run main.py
CMD python3 main.py