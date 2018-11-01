from pressurecooker import youtube

def test_get_youtube_info():

    tree = youtube.get_youtube_info('https://www.youtube.com/playlist?list=PLHSER0n5wjJybb22EtsajzufpozEo5vLE')
    assert tree['id']
    assert tree['kind']
    assert tree['title']
    assert len(tree['children']) == 22

    for video in tree['children']:
        assert tree['id']
        assert tree['kind']
        assert tree['title']
