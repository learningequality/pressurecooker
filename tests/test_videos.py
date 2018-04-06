from __future__ import print_function
import pytest
import requests
import requests_cache
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


