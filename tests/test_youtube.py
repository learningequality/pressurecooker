from pressurecooker import youtube

def test_get_youtube_info():

    tree = youtube.get_youtube_info('https://www.youtube.com/playlist?list=PLHSER0n5wjJybb22EtsajzufpozEo5vLE')
    assert tree['title']
    assert tree['kind']
    assert len(tree['children']) == 22
