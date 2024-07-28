from datetime import datetime
import os
import subprocess
import json
import imgkit
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from database import add_video

def get_video_duration(video_path):
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=duration", "-of", "json", video_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        info = json.loads(result.stdout)
        duration = float(info['streams'][0]['duration'])
        return round(duration, 2)
    except Exception as e:
        print(f"Error getting duration for {video_path}: {e}")
        return None
    
def render_text(top, bottom, font_path, font_family_name, shadow_offset, shadow_color, shadow_blur, text_color, output_file):
    absolute_font_path = os.path.abspath(font_path)
    html_content = f'''
    <html>
    <head>
        <style>
            @font-face {{
                font-family: '{font_family_name}';
                src: url('file://{absolute_font_path}') format('opentype');
            }}
            body, html {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }}
            .text {{
                font-family: '{font_family_name}';
                color: {text_color};
                text-shadow: {shadow_offset[0]}px {shadow_offset[1]}px {shadow_blur}px {shadow_color};
                position: relative;
                text-align: center;
                padding: 0;
            }}
            .top-text {{
                font-size: {top["size"]}px;
                top: 34%;
            }}
            .bottom-text {{
                font-size: {bottom["size"]}px;
                top: 27.7%;
            }}
        </style>
    </head>
    <body>
        <div class="text top-text">{top["text"]}</div>
        <div class="text bottom-text">{bottom["text"]}</div>
    </body>
    </html>
    '''
    
    options = {
        'format': 'png',
        'width': 1920,
        'height': 1080,
        'transparent': ''
    }
    
    imgkit.from_string(html_content, output_file, options=options)
    
def text_pre_processing(player, n_replays):
    texts = [
        {
            "top":{
                "text": f"GAME {i}",
                "size": 150
            },
            "bottom": {
                "text": f"{player.upper()} POV",
                "size": 100
            }
        } for i in range(1, n_replays+1)
    ]

    font_path = "./fonts/Mont-HeavyDEMO.otf"
    font_family_name = "Mont Heavy DEMO"
    text_color = "rgb(255, 255, 255)"
    shadow_color = "rgba(0, 0, 0, 0.9)"
    shadow_offset = (5, 5)
    shadow_blur = 20

    images = []
    for i, text_obj in enumerate(texts):
        result_file = f"./text_images/text_{i}.png"
        render_text(text_obj["top"], text_obj["bottom"], font_path, font_family_name, shadow_offset, shadow_color, shadow_blur, text_color, result_file)
        images.append(result_file)

    return images

def edit_videos(files, output_file, player, video_title, video_id):
    durations = { file: get_video_duration(file) for file in files }

    images = text_pre_processing(player, len(files))

    xfades = {}
    text_starts = {}
    curr_len = 0
    for i, (file, duration) in enumerate(durations.items()):
        text_starts[file] = curr_len
        xfades[file] = curr_len - 0.5
        curr_len += duration-0.5
    
    TEXT_DUR = 4
    FADE_IN_TIME=0.5
    FADE_IN_DURATION=0.2
    FADE_OUT_DURATION=0.5

    complex = """[0:v]trim=start=0.5,setpts=PTS-STARTPTS[vx0];
        """
    trim_fmt = """[{text_num}:v]fade=in:st={fade_in}:d={fade_in_duration}:alpha=1,fade=out:st={fade_out}:d={fade_out_duration}:alpha=1[v{v_num}ov];
                [vx{v_num}][v{v_num}ov]overlay=shortest=1:x=0:y=0:format=auto[v{v_num}text];
        """
    setpts_fmt = """[{v_num}:v]setpts=PTS-STARTPTS[v{v_num}];
        """
    xfade_fmt = """[v{v_num}text][v{game_num}]xfade=transition=fade:duration=0.5:offset={fade_offset}[vx{game_num}];
        """
    for i, file in enumerate(files):
        if i > 0:
            complex += setpts_fmt.format(v_num=i*2)
            complex += xfade_fmt.format(v_num=i*2-1, game_num=i*2, fade_offset=xfades[file])
        complex += trim_fmt.format(
            v_num=i*2, 
            text_num=i*2+1,
            fade_in=text_starts[file]+FADE_IN_TIME,
            fade_in_duration=FADE_IN_DURATION,
            faded_in_end=text_starts[file]+FADE_IN_TIME+FADE_IN_DURATION,
            fade_out=text_starts[file]+TEXT_DUR+FADE_IN_TIME+FADE_IN_DURATION,
            fade_out_duration=FADE_OUT_DURATION,
            fade_out_end=text_starts[file]+TEXT_DUR+FADE_IN_TIME+FADE_IN_DURATION+FADE_OUT_DURATION
        )
            
    
    complex += "[v{game_num}text]fade=t=out:st={fade_out_start}:d=1".format(game_num=len(files)-1, fade_out_start=sum(durations.values())-(0.5*(len(files)-1)))

    ffmpeg_command = [
        "ffmpeg"
    ]

    for i, file in enumerate(files):
        ffmpeg_command.extend(["-i", file])
        ffmpeg_command.extend(["-loop", "1"])
        ffmpeg_command.extend(["-i", images[i]])
    
    ffmpeg_command.extend([
        "-filter_complex", complex,
        "-c:v", "libx264",
        "-y", output_file
    ])

    try:
        subprocess.run(ffmpeg_command, check=True)
        print("Video processing completed successfully.")
        video = {
            "edited_date": datetime.today().isoformat(),
            "id": video_id,
            "player": player,
            "title": video_title
        }
        add_video(video)
        return "Success"
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during video processing: {e}")
        return "Error"

if __name__ == "__main__":
    edit_videos(["./recordings/Zen/2024-07-25_Zen Game 1.mp4"], 
                "./edits/Zen.mp4",
                "Zen",
                "Test title",
                "test_id")