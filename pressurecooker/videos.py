import re
import subprocess
import tempfile

from ffmpy import FFmpeg
from le_utils.constants import format_presets


def check_video_resolution(videopath):
    result = subprocess.check_output(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_entries',
                                      'stream=width,height', '-of', 'default=noprint_wrappers=1', str(videopath)])
    pattern = re.compile('width=([0-9]*)[^height]+height=([0-9]*)')
    resolution = pattern.search(result)
    if resolution and int(resolution.group(2)) >= 720:
        return format_presets.VIDEO_HIGH_RES
    else:
        return format_presets.VIDEO_LOW_RES


def extract_thumbnail_from_video(fpath_in, fpath_out):
    """
    Extract a thumbnail from the video given through the fobj_in file object. The thumbnail image
    will be written in the file object given in fobj_out.
    """

    ff = FFmpeg(
        inputs={str(fpath_in): None},
        outputs={fpath_out: "-vcodec png -ss 10 -vframes 1 -an -f rawvideo -y"}
    )
    ff.run()
