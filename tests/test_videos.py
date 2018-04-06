from __future__ import print_function
import pytest
import re
import requests
import requests_cache
import subprocess
import sys
import tempfile

from le_utils.constants import format_presets

# SUT
from pressurecooker import videos


# cache, so we don't keep requesting the full videos
if sys.version_info[0] == 3:
    requests_cache.install_cache("video_cache_py3")
else:
    requests_cache.install_cache("video_cache")




@pytest.fixture
def low_res_video():
    with tempfile.NamedTemporaryFile(suffix='.mp4') as f:
        resp = requests.get(
            "https://archive.org/download/vd_is_for_everybody/vd_is_for_everybody_512kb.mp4",
            stream=True,
        )
        for chunk in resp.iter_content(chunk_size=1048576):
            f.write(chunk)
        f.flush()
        yield f


@pytest.fixture
def high_res_video():
    with tempfile.NamedTemporaryFile(suffix='.mp4') as f:
        resp = requests.get(
            "https://ia800201.us.archive.org/7/items/"
            "UnderConstructionFREEVideoBackgroundLoopHD1080p/"
            "UnderConstruction%20-%20FREE%20Video%20Background%20Loop%20HD%201080p.mp4",
            stream=True
        )
        for chunk in resp.iter_content(chunk_size=1048576):
            f.write(chunk)
        f.flush()
        yield f

@pytest.fixture
def bad_video():
    with tempfile.NamedTemporaryFile(suffix='.mp4') as f:
        f.write(b'novideohere. ffmpeg soshould error')
        f.flush()
        yield f


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

    def test_returns_an_image(self, low_res_video):
        with tempfile.NamedTemporaryFile(suffix=".png") as pngf:
            videos.extract_thumbnail_from_video(low_res_video.name, pngf.name, overwrite=True)
            pngf.seek(0)
            assert pngf.read(2) == PNG_MAGIC_NUMBER





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
        with tempfile.NamedTemporaryFile(suffix=".mp4") as vout:
            videos.compress_video(high_res_video.name, vout.name, overwrite=True)
            width, height = get_resolution(vout.name)
            assert height == 480, 'should compress to 480 v resolution by defualt'

    def test_compression_max_width(self, high_res_video):
        with tempfile.NamedTemporaryFile(suffix=".mp4") as vout:
            videos.compress_video(high_res_video.name, vout.name, overwrite=True, max_width=120)
            width, height = get_resolution(vout.name)
            assert width == 120, 'should be 120 h resolution since max_width set'

    def test_compression_max_width_odd(self, high_res_video):
        """
        regression test for: https://github.com/learningequality/pressurecooker/issues/11
        """
        with tempfile.NamedTemporaryFile(suffix=".mp4") as vout:
            videos.compress_video(high_res_video.name, vout.name, overwrite=True, max_width=121)
            width, height = get_resolution(vout.name)
            assert width == 120, 'should round down to 120 h resolution when max_width=121 set'

    def test_compression_max_height(self, high_res_video):
        with tempfile.NamedTemporaryFile(suffix=".mp4") as vout:
            videos.compress_video(high_res_video.name, vout.name, overwrite=True, max_height=140)
            width, height = get_resolution(vout.name)
            assert height == 140, 'should be 140 v resolution since max_height set'

    def test_raises_for_bad_file(self, bad_video):
        with tempfile.NamedTemporaryFile(suffix=".mp4") as vout:
            with pytest.raises(videos.VideoCompressionError):
                videos.compress_video(bad_video.name, vout.name, overwrite=True)

