from datetime import datetime
import os
import subprocess
import json

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

def edit_videos(files, output_file, player, video_title, video_id):
    font_path = "./fonts/impact.ttf"
    durations = { file: get_video_duration(file) for file in files }

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
    trim_fmt = """[vx{v_num}]drawtext=fontfile={font}:text='GAME {game_num}':fontsize=110:fontcolor=ffffff:alpha='if(lt(t,{fade_in}),0,if(lt(t,{faded_in_end}),(t-{fade_in})/{fade_in_duration},if(lt(t,{fade_out}),1,if(lt(t,{fade_out_end}),({fade_out_duration}-(t-{fade_out}))/{fade_out_duration},0))))':x=(w-text_w)/2:y=(h-text_h)/2[v{v_num}text];
        """
    setpts_fmt = """[{v_num}:v]setpts=PTS-STARTPTS[v{v_num}];
        """
    xfade_fmt = """[v{v_num}text][v{game_num}]xfade=transition=fade:duration=0.5:offset={fade_offset}[vx{game_num}];
        """
    for i, file in enumerate(files):
        if i > 0:
            complex += setpts_fmt.format(v_num=i)
            complex += xfade_fmt.format(v_num=i-1, game_num=i, fade_offset=xfades[file])
        complex += trim_fmt.format(
            v_num=i, 
            font=font_path, 
            game_num=i+1, 
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

    for file in files:
        ffmpeg_command.extend(["-i", file])
    
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
