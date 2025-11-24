# test_ffmpeg.py
import subprocess
import shutil

ffmpeg = shutil.which("ffmpeg")
print(f"FFmpeg found at: {ffmpeg}")

if ffmpeg:
    result = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True)
    print(result.stdout)
else:
    print("FFmpeg NOT found in PATH")
