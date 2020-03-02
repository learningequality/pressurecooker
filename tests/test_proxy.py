import os
import shutil
import sys
import tempfile

import pytest

from pressurecooker import proxy
from pressurecooker.youtube import YouTubeResource


# This test takes a few minutes, but is very useful for checking that the proxy is not being ignored,
# so mark it to run when the PYTEST_RUN_SLOW env var is set.
@pytest.mark.skipif(not 'PYTEST_RUN_SLOW' in os.environ, reason="This test takes several minutes to complete.")
def test_bad_proxies_get_banned():
    # create some fake proxies, then check that they get banned.
    proxy.PROXY_LIST = [
        '123.123.123.123:1234',
        '142.123.432.234:123345',
        '156.245.233.321:1232342',
        '444.444.444.444:445565',
        '555.555.555.555:5454'
    ]

    temp_dir = tempfile.mkdtemp()
    video = YouTubeResource('https://www.youtube.com/watch?v=DLzxrzFCyOs')
    video.download(temp_dir)

    temp_files = os.listdir(temp_dir)
    shutil.rmtree(temp_dir)
    # if the file downloaded, that's a sign the proxies weren't used.
    assert temp_files == ['Watch']
    assert sorted(proxy.BROKEN_PROXIES) == sorted(proxy.PROXY_LIST)


@pytest.mark.skipif(not 'PYTEST_RUN_SLOW' in os.environ, reason="This test can take several minutes to complete.")
def test_proxy_download():
    proxy.get_proxies(refresh=True)
    assert len(proxy.PROXY_LIST) > 1

    temp_dir = tempfile.mkdtemp()
    video = YouTubeResource('https://www.youtube.com/watch?v=DLzxrzFCyOs')
    video.download(temp_dir)

    temp_files = os.listdir(os.path.join(temp_dir, 'Watch'))
    shutil.rmtree(temp_dir)
    # if the file downloaded, that's a sign the proxies weren't used.
    has_video = False
    for afile in temp_files:
        if afile.endswith('.mp4'):
            has_video = True

    assert has_video
