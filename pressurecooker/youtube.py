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
            'license': ''
        }

        for field_name in extracted_fields:
            if field_name in results:
                leaf[field_name] = results[field_name]
            else:
                leaf[field_name] = extracted_fields[field_name]

        if 'entries' in results:
            leaf['children'] = []
            for entry in results['entries']:
                if entry is not None:
                    leaf['children'].append(add_to_tree(entry))

        return leaf

    tree = add_to_tree(results)

    return tree

def download_youtube_videos(videos, output_directory=None):
    """
    Downloads the videos specified and returns information about the downloaded videos.

    :param videos: A dictionary object with information about the video(s) to download.
    :param output_directory:
    :return:
    """

    pass