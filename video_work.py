import ffmpeg


def extract_subtitle(filepath, output_file):
    video = ffmpeg.input(filepath, loglevel=16)
    video = ffmpeg.output(video, output_file, map="0:s:0")
    print(video.get_args())
    video.run()
    return output_file

def extract_thumbnail(filepath, output_file):
    # ffmpeg -i input.mp4 -vf "thumbnail" -frames:v 1 thumbnail.png
    input = ffmpeg.input(filepath, loglevel=16).filter("select","gt(scene,0.6)").output(output_file, frames=1).overwrite_output()
    print(input.get_args())
    input.run()
    return output_file

def hardcode_ass_subtitle_hevc(input_file, subtitle, output_file):
    input = ffmpeg.input(input_file)
    video = ffmpeg.filter(input.video, "ass", subtitle)
        
    input = ffmpeg.output(video, input.audio, output_file, format="mp4", vcodec="libx265", crf="25", bf=6).overwrite_output()
    print(input.get_args())
    try:
        out, err = input.run()
    except ffmpeg.Error as e:
        if e.stdout:
            print('stdout:', e.stdout.decode('utf8'))
        if e.stderr:
            print('stderr:', e.stderr.decode('utf8'))
        raise e

    return out, err

def hardcode_ass_subtitle_x264(input_file, subtitle, output_file):
    input = ffmpeg.input(input_file)
    video = ffmpeg.filter(input.video, "ass", subtitle)

    input = ffmpeg.output(video, input.audio, output_file, format="mp4", vcodec="libx264", crf="22", bf=4, preset='veryfast', tune='animation', profile='high10', **{"aq-mode": 3}).overwrite_output()
    print(input.get_args())
    try:
        out, err = input.run()
    except ffmpeg.Error as e:
        if e.stdout:
            print('stdout:', e.stdout.decode('utf8'))
        if e.stderr:
            print('stderr:', e.stderr.decode('utf8'))
        raise e

    return out, err
