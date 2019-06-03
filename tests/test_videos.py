from __future__ import print_function
import atexit
import os
import pytest
import re
import requests
import requests_cache
import subprocess
import sys
import tempfile
import PIL

from le_utils.constants import format_presets
from pressurecooker import videos


# cache, so we don't keep requesting the full videos
if sys.version_info[0] == 3:
    requests_cache.install_cache("video_cache_py3")
else:
    requests_cache.install_cache("video_cache")



@pytest.fixture
def low_res_video():
    with TempFile(suffix='.mp4') as f:
        resp = requests.get(
            "https://archive.org/download/vd_is_for_everybody/vd_is_for_everybody_512kb.mp4",
            stream=True,
        )
        for chunk in resp.iter_content(chunk_size=1048576):
            f.write(chunk)
        f.flush()
    return f            # returns a temporary file with a closed file descriptor


@pytest.fixture
def high_res_video():
    with TempFile(suffix='.mp4') as f:
        resp = requests.get(
            "https://ia800201.us.archive.org/7/items/"
            "UnderConstructionFREEVideoBackgroundLoopHD1080p/"
            "UnderConstruction%20-%20FREE%20Video%20Background%20Loop%20HD%201080p.mp4",
            stream=True
        )
        for chunk in resp.iter_content(chunk_size=1048576):
            f.write(chunk)
        f.flush()
    return f            # returns a temporary file with a closed file descriptor


@pytest.fixture
def low_res_ogv_video():
    with TempFile(suffix='.ogv') as f:
        resp = requests.get(
            "https://archive.org/download/"
            "UnderConstructionFREEVideoBackgroundLoopHD1080p/"
            "UnderConstruction%20-%20FREE%20Video%20Background%20Loop%20HD%201080p.ogv",
            stream=True
        )
        for chunk in resp.iter_content(chunk_size=1048576):
            f.write(chunk)
        f.flush()
    return f            # returns a temporary file with a closed file descriptor

@pytest.fixture
def high_res_mov_video():
    with TempFile(suffix='.mov') as f:
        resp = requests.get(
            "https://ia800201.us.archive.org/7/items/"
            "UnderConstructionFREEVideoBackgroundLoopHD1080p/"
            "cold%20night.mov",
            stream=True
        )
        for chunk in resp.iter_content(chunk_size=1048576):
            f.write(chunk)
        f.flush()
    return f            # returns a temporary file with a closed file descriptor


@pytest.fixture
def bad_video():
    with TempFile(suffix='.mp4') as f:
        f.write(b'novideohere. ffmpeg soshould error')
        f.flush()
    return f            # returns a temporary file with a closed file descriptor



class Test_check_video_resolution:

    def test_returns_a_format_preset(self, low_res_video):
        preset = videos.guess_video_preset_by_resolution(low_res_video.name)
        assert preset in [format_presets.VIDEO_HIGH_RES,
                          format_presets.VIDEO_LOW_RES,
                          format_presets.VIDEO_VECTOR]

    def test_detects_low_res_videos(self, low_res_video):
        preset = videos.guess_video_preset_by_resolution(low_res_video.name)
        assert preset == format_presets.VIDEO_LOW_RES

    def test_detects_high_res_videos(self, high_res_video):
        preset = videos.guess_video_preset_by_resolution(high_res_video.name)
        assert preset == format_presets.VIDEO_HIGH_RES




PNG_MAGIC_NUMBER = b'\x89P'

class Test_extract_thumbnail_from_video:

    def test_returns_a_16_9_image(self, low_res_video):
        with TempFile(suffix=".png") as pngf:
            videos.extract_thumbnail_from_video(low_res_video.name, pngf.name, overwrite=True)
            with open(pngf.name, "rb") as f:
                f.seek(0)
                assert f.read(2) == PNG_MAGIC_NUMBER
            im = PIL.Image.open(pngf.name)
            width, height = im.size
            assert float(width)/float(height) == 16.0/9.0



def get_resolution(videopath):
    """Helper function to get resolution of video at videopath."""
    result = subprocess.check_output(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_entries',
                                      'stream=width,height', '-of', 'default=noprint_wrappers=1', str(videopath)])
    pattern = re.compile('width=([0-9]*)[^height]+height=([0-9]*)')
    m = pattern.search(str(result))
    width, height = int(m.group(1)), int(m.group(2))
    return width, height


class Test_compress_video:

    def test_compression_works(self, high_res_video):
        with TempFile(suffix=".mp4") as vout:
            videos.compress_video(high_res_video.name, vout.name, overwrite=True)
            width, height = get_resolution(vout.name)
            assert height == 480, 'should compress to 480 v resolution by defualt'

    def test_compression_max_width(self, high_res_video):
        with TempFile(suffix=".mp4") as vout:
            videos.compress_video(high_res_video.name, vout.name, overwrite=True, max_width=120)
            width, height = get_resolution(vout.name)
            assert width == 120, 'should be 120 h resolution since max_width set'

    def test_compression_max_width_odd(self, high_res_video):
        """
        regression test for: https://github.com/learningequality/pressurecooker/issues/11
        """
        with TempFile(suffix=".mp4") as vout:
            videos.compress_video(high_res_video.name, vout.name, overwrite=True, max_width=121)
            width, height = get_resolution(vout.name)
            assert width == 120, 'should round down to 120 h resolution when max_width=121 set'

    def test_compression_max_height(self, high_res_video):
        with TempFile(suffix=".mp4") as vout:
            videos.compress_video(high_res_video.name, vout.name, overwrite=True, max_height=140)
            width, height = get_resolution(vout.name)
            assert height == 140, 'should be 140 v resolution since max_height set'

    def test_raises_for_bad_file(self, bad_video):
        with TempFile(suffix=".mp4") as vout:
            with pytest.raises(videos.VideoCompressionError):
                videos.compress_video(bad_video.name, vout.name, overwrite=True)



class Test_convert_video:

    def test_convert_mov_works(self, high_res_mov_video):
        with TempFile(suffix=".mp4") as vout:
            videos.compress_video(high_res_mov_video.name, vout.name, overwrite=True)
            width, height = get_resolution(vout.name)
            assert height == 480, 'should convert .ogv to .mp4 and set 480 v res'

    def test_convert_and_resize_ogv_works(self, low_res_ogv_video):
        with TempFile(suffix=".mp4") as vout:
            videos.compress_video(low_res_ogv_video.name, vout.name, overwrite=True, max_height=200)
            width, height = get_resolution(vout.name)
            assert height == 200, 'should convert .ogv to .mp4 and set 200 v res'




## Helper class for cross-platform temporary files

def remove_temp_file(*args, **kwargs):
    filename = args[0]
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass
    assert not os.path.exists(filename)

class TempFile(object):
    """
    tempfile.NamedTemporaryFile deletes the file as soon as the filehandle is closed.
    This is OK on unix but on Windows the file can't be used by other commands
    (i.e. ffmpeg) unti the file is closed.
    Temporary files are instead deleted when we quit.
    """

    def __init__(self, *args, **kwargs):
        # all parameters will be passed to NamedTemporaryFile
        self.args = args
        self.kwargs = kwargs

    def __enter__(self):
        # create a temporary file as per usual, but set it up to be deleted once we're done
        self.f = tempfile.NamedTemporaryFile(*self.args, delete=False, **self.kwargs)
        atexit.register(remove_temp_file, self.f.name)
        return self.f

    def __exit__(self, _type, value, traceback):
        self.f.close()

