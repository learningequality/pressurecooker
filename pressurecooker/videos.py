import re
import subprocess
import tempfile

from ffmpy import FFmpeg
from le_utils.constants import format_presets


def guess_video_preset_by_resolution(videopath):
    result = subprocess.check_output(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_entries',
                                      'stream=width,height', '-of', 'default=noprint_wrappers=1', str(videopath)])
    pattern = re.compile('width=([0-9]*)[^height]+height=([0-9]*)')
    resolution = pattern.search(str(result))
    if resolution and int(resolution.group(2)) >= 720:
        return format_presets.VIDEO_HIGH_RES
    else:
        return format_presets.VIDEO_LOW_RES


def extract_thumbnail_from_video(fpath_in, fpath_out, overwrite=False):
    """
    Extract a thumbnail from the video given through the fobj_in file object. The thumbnail image
    will be written in the file object given in fobj_out.
    """
    command = ["ffmpeg", "-y" if overwrite else "-n", "-i", str(fpath_in), "-vf", "select=gt(scene\,0.4)",
               "-frames:v", "5", "-vsync", "vfr", "-vcodec", "png", "-nostats", "-loglevel", "0", "-an",
               "-f", "rawvideo", str(fpath_out)]

    subprocess.call(command)


def compress_video(source_file_path, target_file, overwrite=False, **kwargs):
    # Construct command for compressing video
    scale = "'{}:-1'".format(kwargs['max_width']) if 'max_width' in kwargs else "'trunc(oh*a/2)*2:min(ih,480)'"
    crf = kwargs['crf'] if 'crf' in kwargs else 32
    command = ["ffmpeg", "-y" if overwrite else "-n", "-i", source_file_path, "-profile:v", "baseline",
               "-level", "3.0", "-b:a", "32k", "-ac", "1", "-vf", "scale={}".format(scale),
               "-crf", str(crf), "-preset", "slow", "-strict", "-2", "-v", "quiet", "-stats", target_file]

    subprocess.call(command)