import youtube_dl


def get_youtube_info(youtube_url):
    """
    This function takes a link to a YouTube URL, then returns a dictionary object with info about the video.

    :param youtube_url: URL of a YouTube video, channel or playlist to retrieve information on.
    :return: A dictionary object containing information about the channel, playlist or video.
    """

    client = youtube_dl.YoutubeDL(dict(verbose=True, no_warnings=True))
    results = client.extract_info(youtube_url, download=False, process=True)

    def add_to_tree(results):
        leaf = {}

        # dict mapping of field name and default value when not found.
        extracted_fields = {
            'title': '',
            'description': '',
            'webpage_url': '',
            'tags': [],
            'subtitles': {},
            'requested_subtitles': '',
            'artist': '',
            'license': '',
            '_type': 'video'
        }

        for field_name in extracted_fields:
            info_name = field_name
            if info_name == '_type':
                info_name = 'kind'
            elif info_name == 'webpage_url':
                info_name = 'source_url'
            if field_name in results:
                leaf[info_name] = results[field_name]
            else:
                leaf[info_name] = extracted_fields[field_name]

        # print("Results = {}".format(results))
        if 'entries' in results:
            leaf['children'] = []
            for entry in results['entries']:
                if entry is not None:
                    leaf['children'].append(add_to_tree(entry))

        return leaf

    keys = list(results.keys())
    keys.sort()
    tree = add_to_tree(results)

    return tree
