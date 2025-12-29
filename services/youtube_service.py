import yt_dlp
import os
import glob
import base64
from models import SongMetadata, YouTubeSearchResult
from fastapi import HTTPException

class YouTubeService:
    def __init__(self):
        self.output_dir = "/tmp/downloads"
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

    def download_to_base64(self, video_url: str) -> tuple[str, str]:
        """
        Downloads the video as MP3 and returns (filename, base64_string).
        """
        # Clean up old files in tmp
        self._cleanup_tmp()

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.output_dir}/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'keepvideo': False,  # Ensure we don't keep the original webm/m4a
            'quiet': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(video_url, download=True)
                video_id = info['id']
                # yt-dlp converts to mp3, so extension changes
                filename = f"{video_id}.mp3"
                filepath = os.path.join(self.output_dir, filename)
                
                if not os.path.exists(filepath):
                    raise Exception("File not found after download")

                # Read and Encode
                with open(filepath, "rb") as f:
                    encoded_string = base64.b64encode(f.read()).decode('utf-8')
                
                # Cleanup immediate file
                os.remove(filepath)
                
                return filename, encoded_string
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

    def _cleanup_tmp(self):
        files = glob.glob(f"{self.output_dir}/*")
        for f in files:
            try:
                os.remove(f)
            except:
                pass
