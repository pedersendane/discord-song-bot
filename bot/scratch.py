import json
import yt_dlp

#URL Search
# URL = 'https://www.youtube.com/watch?v=BaW_jenozKc'
# # ℹ️ See help(yt_dlp.YoutubeDL) for a list of available options and public functions
# ydl_opts = {}
# with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#     info = ydl.extract_info(URL, download=False)
#     # ℹ️ ydl.sanitize_info makes the info json-serializable
#     print(json.dumps(ydl.sanitize_info(info)))

#Word Search 
search_word = 'footprint boldy james'
ydl_opts = {'format': 'bestaudio', 'noplaylist': 'True'}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(f"ytsearch:{search_word}", download=False)
    # ℹ️ ydl.sanitize_info makes the info json-serializable
    sanitized = ydl.sanitize_info(info)
    entries = sanitized['entries'][0]
    id = entries['id']
    title = entries['title']
    thumbnail = entries['thumbnail']
    url = entries['url']
    print(json.dumps(entries, indent=4))




    

