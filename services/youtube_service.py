import yt_dlp
import os
import glob
import base64
from models import SongMetadata, YouTubeSearchResult
from fastapi import HTTPException

class YouTubeService:
    def __init__(self):
        self.output_dir = "/app/downloads"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

    def search_video(self, query: str) -> YouTubeSearchResult:
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch1'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(query, download=False)
                if 'entries' in info:
                    video = info['entries'][0]
                else:
                    video = info

                return YouTubeSearchResult(
                    video_id=video['id'],
                    video_url=video['webpage_url'],
                    title=video['title'],
                    duration=video.get('duration', 0)
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"YouTube search failed: {str(e)}")

    def download_file(self, video_url: str, filename_base: str) -> str:
        """
        Downloads the video as MP3 to /app/downloads/filename.mp3
        Returns the filename.
        """
        # Sanitize filename (basic)
        safe_filename = "".join([c for c in filename_base if c.isalpha() or c.isdigit() or c in " .-_()"]).strip()
        filename = f"{safe_filename}.mp3"
        filepath = os.path.join(self.output_dir, filename)

        # Check if exists to avoid redownload (optional, but good for speed)
        if os.path.exists(filepath):
            return filename

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.output_dir}/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'keepvideo': False, 
            'quiet': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(video_url, download=True)
                video_id = info['id']
                temp_filename = f"{video_id}.mp3"
                temp_filepath = os.path.join(self.output_dir, temp_filename)
                
                if not os.path.exists(temp_filepath):
                    raise Exception("File not found after download")

                # Rename to desired filename
                if os.path.exists(filepath):
                    os.remove(filepath)
                os.rename(temp_filepath, filepath)
                
                return filename
                
            except Exception as e:
                # Cleanup if something failed
                if 'temp_filepath' in locals() and os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
                raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

    def _cleanup_tmp(self):
        files = glob.glob(f"{self.output_dir}/*")
        for f in files:
            try:
                os.remove(f)
            except:
                pass
