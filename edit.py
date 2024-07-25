import subprocess
import os

video_files = [
    "/path/to/your/video1.mp4",
    "/path/to/your/video2.mp4",
    "/path/to/your/video3.mp4"
]

output_file = "/path/to/output/output.mp4"

font_path = "/path/to/font.ttf"

# Construct the filter complex string
filter_complex = """
    [0:v]trim=start=0:end=2,setpts=PTS-STARTPTS[head1];
    [0:v][1:v]xfade=transition=fade:duration=0.5:offset=2[xf1];
    [xf1][2:v]xfade=transition=fade:duration=0.5:offset=4.5[xf2];
    [xf2]drawtext=fontfile={font}:text='GAME 1':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,0,2)', \
    drawtext=fontfile={font}:text='GAME 2':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,2.5,4.5)', \
    drawtext=fontfile={font}:text='GAME 3':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,5,7)', \
    fade=t=out:st=7:d=0.5
""".format(font=font_path)

# Build the FFmpeg command
ffmpeg_command = [
    "ffmpeg",
    "-i", video_files[0],
    "-i", video_files[1],
    "-i", video_files[2],
    "-filter_complex", filter_complex,
    "-c:v", "libx264",
    "-y", output_file
]

# Run the FFmpeg command
try:
    subprocess.run(ffmpeg_command, check=True)
    print("Video processing completed successfully.")
except subprocess.CalledProcessError as e:
    print(f"Error occurred during video processing: {e}")
