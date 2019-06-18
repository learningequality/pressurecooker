from abc import ABCMeta, abstractmethod
import codecs
from pycaption import CaptionSet, WebVTTWriter
from pycaption.base import DEFAULT_LANGUAGE_CODE


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


class SubtitleReader(ABCMeta('ABC', (object,), {})):
    """
    Base class for specifying two different types of reader functionality split based on language
    handling
    """
    def __init__(self, reader):
        """
        :param reader: A pycaption reader
        :type reader: WebVTTReader, SRTReader, SAMIReader, SCCReader, DFXPReader
        """
        self.reader = reader

    def read(self, captions_str, lang_code=DEFAULT_LANGUAGE_CODE):
        """
        Handles detecting and reading the captions

        :param captions_str: A string with the captions contents
        :param lang_code: A string representing the lang code of the file
        :type captions_str: str
        :type lang_code: str
        :return: The captions from the file in a `CaptionSet` or `None` if unsupported
        :rtype: CaptionSet, None
        """
        try:
            if not self.reader.detect(captions_str):
                return None
            return self.do_read(captions_str, lang_code)
        except UnicodeDecodeError:
            return None

    @abstractmethod
    def do_read(self, captions_str, lang_code):
        """
        :param captions_str: A string with the captions contents
        :param lang_code: A string representing the lang code of the `captions_str`
        :type captions_str: str
        :type lang_code: str
        :return: The captions a `CaptionSet` or `None` if unsupported
        :rtype: CaptionSet
        """
        pass

    def validate_caption_set(self, caption_set, lang_code):
        """
        Validates the `caption_set` is not empty. Assumes that empty means an invalid language

        :param caption_set: A `CaptionSet`
        :param lang_code:
        :return:
        """
        if caption_set.is_empty():
            raise InvalidSubtitleLanguageError(
                "Captions set is empty for language '{}'".format(lang_code))


class AmbiguousSubtitleReader(SubtitleReader):
    """
    This class handles readers that accept a language when reading, since the format may not
    specify a language.
    """
    def do_read(self, captions_str, lang_code):
        caption_set = self.reader.read(captions_str, lang=lang_code)
        self.validate_caption_set(caption_set, lang_code)
        return caption_set


class EncapsulatedSubtitleReader(SubtitleReader):
    """
    Some subtitle formats encapsulate multiple caption sets for different languages. This class
    handles the reading differently since the readers for those formats will not accept a language,
    but will return a `CaptionSet` with all of the languages. We'll reduce it to the `lang_code`
    language to ensure we're writing captions for the language we're expecting to write.
    """
    def do_read(self, captions_str, lang_code=None):
        caption_set = self.new_caption_set(self.reader.read(captions_str), lang_code)
        self.validate_caption_set(caption_set, lang_code)
        return caption_set

    def new_caption_set(self, old_caption_set, lang_code):
        """
        Builds a new `CaptionSet` from `old_caption_set` with only one language specified by
        `lang_code` since caption sets can contain multiple languages

        :param old_caption_set: A `CaptionSet`
        :param lang_code: A string of the requesting language code
        :type old_caption_set: CaptionSet
        :type lang_code: str
        :return: A `CaptionSet` with captions only for `lang_code`
        :rtype: CaptionSet
        """
        captions = old_caption_set.get_captions(lang_code)
        styles = old_caption_set.get_styles()
        layout_info = old_caption_set.get_layout_info(lang_code)

        return CaptionSet({lang_code: captions}, styles=dict(styles), layout_info=layout_info)


class SubtitleConverter:
    """
    This class converts subtitle files to the preferred VTT format
    """
    def __init__(self, readers, lang_code):
        """
        :param readers: An array of `SubtitleReader` instances
        :param lang_code: A string with the language code
        """
        self.readers = readers
        self.lang_code = lang_code
        self.writer = WebVTTWriter()
        # set "video size" to 100 since other types may have layout, 100 should work to generate %
        self.writer.video_width = 100
        self.writer.video_height = self.writer.video_width * 6 / 19

    def convert(self, in_filename, out_filename):
        """
        Convenience method as captions contents must be unicode for conversion

        :param in_filename: A string path to the captions file to parse
        :param out_filename: A string path to put the converted captions contents
        :return:
        """
        with codecs.open(in_filename, encoding='utf-8') as captions_file:
            captions_str = captions_file.read()

        with codecs.open(out_filename, 'w', encoding='utf-8') as converted_file:
            converted_file.write(self.convert_str(captions_str))

    def convert_str(self, captions_str):
        """
        :param captions_str: A string with captions to convert
        :type: captions_str: str
        :return: A string with the converted caption contents
        :rtype: str
        """
        for reader in self.readers:
            captions = reader.read(captions_str, self.lang_code)
            if captions is not None:
                break
        else:
            raise InvalidSubtitleFormatError('Subtitle file is unsupported or unreadable')

        return self.writer.write(captions)

