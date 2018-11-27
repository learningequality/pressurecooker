import copy
import logging
import os
import sys
import time

from le_utils.constants import languages

import youtube_dl

from . import utils

LOGGER = logging.getLogger("YouTubeResource")



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

        if not 'youtube.com' in url and not 'youtu.be' in url:
            raise utils.VideoURLFormatError(url, 'YouTube')
        self.url = url
        self.subtitles = {}
        self.num_retries = 3
        self.preferred_formats = {
            'video': 'mp4',
            'audio': 'm4a'
        }
        self.get_resource_info()

    def get_resource_info(self, filter=True, download_dir=None):
        """
        This method checks the YouTube URL, then returns a dictionary object with info about the video(s) in it.

        :param download_dir: If set, downloads videos to the specified directory. Defaults to None.

        :return: A dictionary object containing information about the channel, playlist or video.
        """

        options = dict(
            verbose = True,
            no_warnings = True,
            outtmpl = '{}/%(id)s.%(ext)s'.format(download_dir),
            # by default, YouTubeDL will pick what it determines to be the best formats, but for consistency's sake
            # we want to always get preferred formats (default of mp4 and m4a) when possible.
            # TODO: Add customization for video dimensions
            format = "bestvideo[height<=720][ext={}]+bestaudio[ext={}]/best[height<=720][ext={}]".format(
                self.preferred_formats['video'], self.preferred_formats['audio'], self.preferred_formats['video']
            ),
            writethumbnail = download_dir is not None
        )
        LOGGER.info("Download options = {}".format(options))
        client = youtube_dl.YoutubeDL(options)
        results = client.extract_info(self.url, download=(download_dir is not None), process=True)

        keys = list(results.keys())
        keys.sort()
        if not filter:
            return results

        edited_results = self._format_for_ricecooker(results)

        edited_keys = list(edited_results.keys())
        edited_keys.sort()

        return edited_results

    def get_dir_name_from_url(self, url=None):
        """
        Takes a URL and returns a directory name to store files in.

        :param url: URL of a YouTube resource, if None, defaults to the url passed to the YouTubeResource object
        :return: (String) directory name
        """
        if url is None:
            url = self.url
        name = url.split("/")[-1]
        name = name.split("?")[0]
        return " ".join(name.split("_")).title()

    def download(self, base_path=None):
        download_dir = utils.make_dir_if_needed(os.path.join(base_path, self.get_dir_name_from_url()))
        LOGGER.debug("download_dir = {}".format(download_dir))
        for i in range(self.num_retries):
            try:
                info = self.get_resource_info(filter=True, download_dir=download_dir)
                if 'children' in info:
                    for child in info['children']:
                        child['filename'] = os.path.join(download_dir, "{}.{}".format(child["id"], child['ext']))
                else:
                    info['filename'] =  os.path.join(download_dir, "{}.{}".format(info["id"], info['ext']))
                return info
            except (youtube_dl.utils.DownloadError, youtube_dl.utils.ContentTooShortError,
                    youtube_dl.utils.ExtractorError, OSError) as e:
                LOGGER.info("    + An error ocurred, may be the video is not available.")
                print("YouTube error")
                break
            except (ValueError, IOError, OSError) as e:
                LOGGER.info(e)
                LOGGER.info("Download retry")
                sleep_seconds = .5
                time.sleep(sleep_seconds)
            except OSError:
                print("OS Error")
                break

        return None

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
            'ext': 'mp4',
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
        resource_info = self.get_resource_info()
        output_video_info = copy.copy(resource_info)
        videos_with_warnings = []
        if filter:
            output_video_info['children'] = []

        for video in resource_info['children']:
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



def get_language_with_alpha2_fallback(language_code):
    """
    Lookup language code `language_code` (string) in the internal language codes,
    and if that fails, try to map map `language_code` to the internal represention
    using the `getlang_by_alpha2` helper method.
    Returns either a le-utils Language object or None if both lookups fail.
    """
    # 1. try to lookup `language` using internal representation
    language_obj = languages.getlang(language_code)
    # if language_obj not None, we know `language` is a valid language_id in the internal repr.
    if language_obj is None:
        # 2. try to match by two-letter ISO code
        language_obj = languages.getlang_by_alpha2(language_code)
    return language_obj


def is_youtube_subtitle_file_supported_language(language):
    """
    Check if the language code `language` (string) is a valid language code in the
    internal language id format `{primary_code}` or `{primary_code}-{subcode}`
    ot alternatively if it s YouTube language code that can be mapped to one of
    the languages in the internal represention.
    """
    language_obj = get_language_with_alpha2_fallback(language)
    if language_obj is None:
        print('Found unsupported language code {}'.format(language))
        return False
    else:
        return True





if __name__ == "__main__":
    check = False
    if "--check" in sys.argv:
        sys.argv.remove("--check")
        check = True

    url = sys.argv[1]
    download_dir = None
    if len(sys.argv) > 2:
        download_dir = os.path.abspath(sys.argv[2])
    print("Download_dir = {}".format(download_dir))
    yt_resource = YouTubeResource(url)
    if download_dir is not None:
        print("Downloading videos...")
        yt_resource.download(base_path=download_dir)
    else:
        info = yt_resource.get_resource_info(download_dir=download_dir)
        if check:
            warnings, out_info = yt_resource.check_for_content_issues()
            for warning in warnings:
                print('Video {} has the following issues: {}'.format(warning['video']['title'], warning['warnings']))
        else:
            print(info)
