import sys

import youtube_dl


def get_youtube_info(youtube_url):
    """
    Convenience function for retrieving YouTube resource information. Wraps YouTubeResource.get_resource_info.

    :param youtube_url: URL of YouTube resource to get information on.

    :return: A dictionary object containing information about the YouTube resource.
    """
    resource = YouTubeResource(youtube_url)
    return resource.get_resource_info()


class YouTubeResource:
    """
    This class encapsulates functionality related to information retrieval and download of YouTube resources.
    Resources may include videos, playlists and channels.
    """
    def __init__(self, url):
        """
        Initializes the YouTube resource, and calls the get_resource_info method to retrieve resource information.

        :param url: URL of a YouTube resource. URL may point to a video, playlist or channel.
        """
        self.url = url
        self.resource_info = {}
        self.subtitles = {}

        self.get_resource_info()

    def get_resource_info(self, refresh=False):
        """
        This method checks the YouTube URL, then returns a dictionary object with info about the video(s) in it.

        :param refresh: If True, re-downloads the information if it already exists. Defaults to False.

        :return: A dictionary object containing information about the channel, playlist or video.
        """

        if len(self.resource_info) > 0 and not refresh:
            return self.resource_info

        client = youtube_dl.YoutubeDL(dict(verbose=True, no_warnings=True))
        results = client.extract_info(self.url, download=False, process=True)

        keys = list(results.keys())
        keys.sort()
        self.resource_info = self._format_for_ricecooker(results)

        return self.resource_info

    def get_resource_subtitles(self):
        """
        Retrieves the subtitles for the video(s) represented by this resource. Subtitle information will be
        contained in the 'subtitles' key of the dictionary object returned.

        :return: A dictionary object that contains information about video subtitles
        """
        client = youtube_dl.YoutubeDL(dict(verbose=True, no_warnings=True, writesubtitles=True, allsubtitles=True))
        results = client.extract_info(self.url, download=False, process=True)
        return results

    def _format_for_ricecooker(self, results):
        """
        Internal method for converting YouTube resource info into the format expected by ricecooker.

        :param results: YouTube resource dictionary object to be converted to ricecooker format.

        :return: A dictionary object in the format expected by ricecooker.
        """
        leaf = {}

        # dict mapping of field name and default value when not found.
        extracted_fields = {
            'id': '',
            'title': '',
            'description': '',
            'thumbnail': '',
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

        if 'entries' in results:
            leaf['children'] = []
            for entry in results['entries']:
                if entry is not None:
                    leaf['children'].append(self._format_for_ricecooker(entry))
                else:
                    print("Entry is none?")

        return leaf

    def check_for_content_issues(self, filter=False):
        """
        Checks the YouTube resource and looks for any issues that may prevent download or distribution of the material,
        or would otherwise imply that the resource is not suitable for use in Kolibri.

        :param filter: If True, remove videos with issues from the returned resource info. Defaults to False.

        :return: A tuple containing a list of videos with waranings, and the resource info as a dictionary object.
        """
        output_video_info = self.resource_info
        videos_with_warnings = []
        if filter:
            output_video_info['children'] = []

        for video in self.resource_info['children']:
            warnings = []
            if not video['license']:
                warnings.append('no_license_specified')
            elif video['license'].find("Creative Commons") == -1:
                warnings.append('closed_license')

            if len(warnings) > 0:
                videos_with_warnings.append({'video': video, 'warnings': warnings})
            elif filter:
                output_video_info['children'].append(video)

        return videos_with_warnings, output_video_info


if __name__ == "__main__":
    check = False
    if "--check" in sys.argv:
        sys.argv.remove("--check")
        check = True

    url = sys.argv[1]
    yt_resource = YouTubeResource(url)
    info = yt_resource.get_resource_info()
    if check:
        warnings, out_info = yt_resource.check_for_content_issues()
        for warning in warnings:
            print('Video {} has the following issues: {}'.format(warning['video']['title'], warning['warnings']))
    else:
        print(info)
