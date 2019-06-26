import codecs
from pycaption import CaptionSet, WebVTTWriter

LANGUAGE_CODE_UNKNOWN = 'unknown'


class InvalidSubtitleFormatError(TypeError):
    """
    Custom error indicating a format that is invalid
    """
    pass


class InvalidSubtitleLanguageError(ValueError):
    """
    Custom error indicating that the provided language isn't present in a captions file
    """
    pass


class SubtitleReader:
    """
    A wrapper class for the pycaption readers since the interface differs between all. This will
    call read with `LANGUAGE_CODE_UNKNOWN` if `requires_language` is `True`
    """
    def __init__(self, reader, requires_language=False):
        """
        :param reader: A pycaption reader
        :type reader: WebVTTReader, SRTReader, SAMIReader, SCCReader, DFXPReader
        :param requires_language: A boolean specifying whether the reader requires a language
        :type requires_language: bool
        """
        self.reader = reader
        self.requires_language = requires_language

    def read(self, caption_str):
        """
        Handles detecting and reading the captions

        :param caption_str: A string with the captions contents
        :type caption_str: str
        :return: The captions from the file in a `CaptionSet` or `None` if unsupported
        :rtype: CaptionSet, None
        """
        try:
            if not self.reader.detect(caption_str):
                return None

            if self.requires_language:
                return self.reader.read(caption_str, lang=LANGUAGE_CODE_UNKNOWN)

            return self.reader.read(caption_str)
        except UnicodeDecodeError:
            return None


class SubtitleConverter:
    """
    This class converts subtitle files to the preferred VTT format
    """
    def __init__(self, readers, caption_str):
        """
        :param readers: An array of `SubtitleReader` instances
        :param caption_str: A string with the captions content
        """
        self.readers = readers
        self.caption_str = caption_str
        self.writer = WebVTTWriter()
        # set "video size" to 100 since other types may have layout, 100 should work to generate %
        self.writer.video_width = 100
        self.writer.video_height = self.writer.video_width * 6 / 19
        self.caption_set = None

    def get_caption_set(self):
        """
        Detects and reads the `caption_str` into the cached `caption_set` property and returns it.

        :return: CaptionSet
        """
        if self.caption_set:
            return self.caption_set

        for reader in self.readers:
            self.caption_set = reader.read(self.caption_str)
            if self.caption_set is not None:
                break
        else:
            self.caption_set = None
            raise InvalidSubtitleFormatError('Subtitle file is unsupported or unreadable')

        if self.caption_set.is_empty():
            raise InvalidSubtitleLanguageError('Captions set is invalid')
        return self.caption_set

    def get_language_codes(self):
        """
        This gets the language codes as defined by the caption string. Some caption formats do not
        specify languages, which in that case a special code (constant `LANGUAGE_CODE_UNKNOWN`)
        will be present.

        :return: An array of language codes as defined in the subtitle file.
        """
        return self.get_caption_set().get_languages()

    def has_language(self, lang_code):
        """
        Determines if current caption set to be converted is/has an unknown language. This would
        happen with SRT or other files where language is not specified

        :param: lang_code: A string of the language code to check
        :return: bool
        """
        return lang_code in self.get_language_codes()

    def replace_unknown_language(self, lang_code):
        """
        This essentially sets the "unknown" language in the caption set, by replacing the key
        with this new language code

        :param lang_code: A string with the language code to replace the unknown language with
        """
        caption_set = self.get_caption_set()

        captions = {}
        for lang in caption_set.get_languages():
            set_lang = lang_code if lang == LANGUAGE_CODE_UNKNOWN else lang
            captions[set_lang] = caption_set.get_captions(lang)

        # Replace caption_set with new version, having replaced unknown language
        self.caption_set = CaptionSet(
            captions, styles=dict(caption_set.get_styles()), layout_info=caption_set.layout_info)

    def write(self, out_filename, lang_code):
        """
        Convenience method to write captions as file. Captions contents must be unicode for
        conversion.

        :param out_filename: A string path to put the converted captions contents
        :param lang_code: A string of the language code to write
        """
        with codecs.open(out_filename, 'w', encoding='utf-8') as converted_file:
            converted_file.write(self.convert(lang_code))

    def convert(self, lang_code):
        """
        Converts the caption set to the VTT format

        :param lang_code: A string with one of the languages to output the captions for
        :type: lang_code: str
        :return: A string with the converted caption contents
        :rtype: str
        """
        caption_set = self.get_caption_set()
        captions = caption_set.get_captions(lang_code)

        if not captions:
            raise InvalidSubtitleLanguageError(
                "Language '{}' is not present in caption set".format(lang_code))

        styles = caption_set.get_styles()
        layout_info = caption_set.get_layout_info(lang_code)
        lang_caption_set = CaptionSet(
            {lang_code: captions}, styles=dict(styles), layout_info=layout_info)
        return self.writer.write(lang_caption_set)

