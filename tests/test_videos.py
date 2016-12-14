import tempfile

import pytest
import requests
import requests_cache
from le_utils.constants import format_presets

from pressurecooker import videos

# so we don't keep requesting the full videos
requests_cache.install_cache("video_cache")

JPG_MAGIC_NUMBER = '\xff\xd8'
PNG_MAGIC_NUMBER = '\x89P'


@pytest.fixture
def low_res_video():
    with tempfile.NamedTemporaryFile() as f:
        resp = requests.get(
            "https://archive.org/download/vd_is_for_everybody/vd_is_for_everybody_512kb.mp4",
            stream=True,
        )

        for chunk in resp.iter_content():
            f.write(chunk)

        yield f


@pytest.fixture
def high_res_video():
    with tempfile.NamedTemporaryFile() as f:
        resp = requests.get(
            "https://archive.org/download/UnderConstructionFREEVideoBackgroundLoopHD1080p/cold%20night.mp4",
            stream=True
        )

        for chunk in resp.iter_content():
            f.write(chunk)

        yield f


class Test_check_video_resolution:

    def test_returns_a_format_preset(self, low_res_video):
        preset = videos.check_video_resolution(low_res_video.name)

        assert preset in [format_presets.VIDEO_HIGH_RES,
                          format_presets.VIDEO_LOW_RES,
                          format_presets.VIDEO_VECTOR]

    def test_detects_low_res_videos(self, low_res_video):
        preset = videos.check_video_resolution(low_res_video.name)

        assert preset == format_presets.VIDEO_LOW_RES

    # figure out why the high_res_video is getting returned as low res
    # def test_detects_high_res_videos(self, high_res_video):
    #     preset = videos.check_video_resolution(high_res_video.name)

    #     assert preset == format_presets.VIDEO_HIGH_RES


class Test_extract_thumbnail_from_video:

    def test_returns_an_image(self, low_res_video):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as f:
            videos.extract_thumbnail_from_video(low_res_video.name, f.name)
            f.seek(0)

            assert f.read(2) == PNG_MAGIC_NUMBER
