import os
import shutil
import tempfile

import pytest
IS_TRAVIS_TESTING = "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true"

from pressurecooker import utils
from pressurecooker import youtube

trees = {}
yt_resources = {}

cc_playlist = 'https://www.youtube.com/playlist?list=PL7m903CwFUgntbjkVMwts89fZq0INCtVS'
non_cc_playlist = 'https://www.youtube.com/playlist?list=PLBO8M-O_dTPE51ymDUgilf8DclGAEg9_A'
subtitles_video = 'https://www.youtube.com/watch?v=6uXAbJQoZlE'
subtitles_zu_video = 'https://www.youtube.com/watch?v=FN12ty5ztAs'


def get_yt_resource(url):
    global yt_resources
    if not url in yt_resources:
        yt_resources[url] = youtube.YouTubeResource(url)

    return yt_resources[url]


def test_get_youtube_info():
    yt_resource = get_yt_resource(non_cc_playlist)
    tree = yt_resource.get_resource_info()
    assert tree['id']
    assert tree['kind']
    assert tree['title']
    assert len(tree['children']) == 4

    for video in tree['children']:
        assert video['id']
        assert video['kind']
        assert video['title']


def test_warnings_no_license():
    yt_resource = get_yt_resource(non_cc_playlist)
    issues, output_info = yt_resource.check_for_content_issues()

    assert len(issues) == 4
    for issue in issues:
        assert 'no_license_specified' in issue['warnings']


def test_cc_no_warnings():
    yt_resource = get_yt_resource(cc_playlist)
    issues, output_info = yt_resource.check_for_content_issues()

    # there is one video in this playlist that is not cc-licensed
    assert len(issues) == 1
    for issue in issues:
        assert 'no_license_specified' in issue['warnings']


@pytest.mark.skipif(IS_TRAVIS_TESTING, reason="Skipping download tests on Travis.")
def test_download_youtube_video():
    download_dir = tempfile.mkdtemp()

    try:
        yt_resource = get_yt_resource(subtitles_video)
        info = yt_resource.download(base_path=download_dir)
        assert info
        if info:
            assert 'filename' in info
            assert os.path.exists(info['filename']), 'Filename {} does not exist'.format(info['filename'])

    finally:
        shutil.rmtree(download_dir)


@pytest.mark.skipif(IS_TRAVIS_TESTING, reason="Skipping download tests on Travis.")
def test_download_youtube_playlist():
    download_dir = tempfile.mkdtemp()

    try:
        yt_resource = get_yt_resource(cc_playlist)
        info = yt_resource.download(base_path=download_dir)
        assert info
        if info:
            assert not 'filename' in info
            assert 'children' in info
            for child in info['children']:
                assert 'filename' in child
                assert os.path.exists(child['filename']), 'Filename {} does not exist'.format(child['filename'])

    finally:
        shutil.rmtree(download_dir)


def test_get_subtitles():
    yt_resource = get_yt_resource(subtitles_video)
    info = yt_resource.get_resource_subtitles()
    assert len(info['subtitles']) == 1
    assert 'ru' in info['subtitles']


def test_non_youtube_url_error():
    url = 'https://vimeo.com/238190750'
    with pytest.raises(utils.VideoURLFormatError):
        youtube.YouTubeResource(url)


def test_subtitles_lang_helpers_compatible():
    """
    Usage examples functions `is_youtube_subtitle_file_supported_language` and
    `_get_language_with_alpha2_fallback` that deal with language codes.
    """
    yt_resource = get_yt_resource(subtitles_zu_video)
    info = yt_resource.get_resource_subtitles()
    all_subtitles = info['subtitles']

    # 1. filter out non-vtt subs
    vtt_subtitles = {}
    for youtube_language, subs in all_subtitles.items():
        vtt_subtitles[youtube_language] = [s for s in subs if s['ext'] == 'vtt']

    for youtube_language, sub_dict in vtt_subtitles.items():
        # 2. check compatibility with le-utils language codes (a.k.a. internal representation)
        verdict = youtube.is_youtube_subtitle_file_supported_language(youtube_language)
        assert verdict == True, 'Wrongly marked youtube_language as incompatible'
        # 3. TODO: figure out what to do for incompatible langs

        # 4. map youtube_language to le-utils language code (a.k.a. internal representation)
        language_obj = youtube.get_language_with_alpha2_fallback(youtube_language)
        assert language_obj is not None, 'Failed to find matchin language code in le-utils'
        if youtube_language == 'zu':
            assert language_obj.code == 'zul', 'Matched to wrong language code in le-utils'


def test_subtitles_lang_helpers_incompatible():
    """
    Ensure `is_youtube_subtitle_file_supported_language` rejects unknown language codes.
    """
    verdict1 = youtube.is_youtube_subtitle_file_supported_language('patapata')
    assert verdict1 == False, 'Failed to reject incompatible youtube_language'
    verdict2 = youtube.is_youtube_subtitle_file_supported_language('zzz')
    assert verdict2 == False, 'Failed to reject incompatible youtube_language'
