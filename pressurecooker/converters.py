import codecs
from pycaption import WebVTTReader, SRTReader, SAMIReader, SCCReader, DFXPReader
from .subtitles import SubtitleConverter, InvalidSubtitleFormatError
from .subtitles import SubtitleReader
from le_utils.constants import file_formats


def build_dfxp_reader():
    return SubtitleReader(DFXPReader())


def build_sami_reader():
    return SubtitleReader(SAMIReader())


def build_scc_reader():
    return SubtitleReader(SCCReader(), requires_language=True)


def build_srt_reader():
    return SubtitleReader(SRTReader(), requires_language=True)


def build_vtt_reader():
    return SubtitleReader(WebVTTReader(), requires_language=True)


BUILD_READER_MAP = {
    file_formats.VTT: build_vtt_reader,
    file_formats.SRT: build_srt_reader,
    file_formats.SAMI: build_sami_reader,
    file_formats.SCC: build_scc_reader,
    file_formats.TTML: build_dfxp_reader,
    file_formats.DFXP: build_dfxp_reader,
}


def build_subtitle_reader(reader_format):
    if reader_format not in BUILD_READER_MAP:
        raise InvalidSubtitleFormatError('Unsupported')
    return BUILD_READER_MAP[reader_format]()


def build_subtitle_readers():
    readers = []
    for reader_format, build in BUILD_READER_MAP.items():
        readers.append(build())
    return readers


def build_subtitle_converter(caption_str, in_format=None):
    """
    Builds a subtitle converter used to convert subtitle files to VTT format

    :param caption_str: A string with the captions contents
    :type: captions_str: str
    :param in_format: A string with expected format of the file to be converted
    :type: in_format: str
    :return: A SubtitleConverter
    :rtype: SubtitleConverter
    """
    readers = []
    if in_format is not None:
        readers.append(build_subtitle_reader(in_format))
    else:
        readers = build_subtitle_readers()

    return SubtitleConverter(readers, caption_str)


def build_subtitle_converter_from_file(captions_filename, in_format=None):
    """
    Reads `captions_filename` as the file to be converted, and returns a `SubtitleConverter`
    instance that can be used to do the conversion.

    :param captions_filename: A string path to the captions file to parse
    :type: captions_filename: str
    :param in_format: A string with expected format of `captions_filename`, otherwise detected
    :type: in_format: str
    :return: A SubtitleConverter
    :rtype: SubtitleConverter
    """
    with codecs.open(captions_filename, encoding='utf-8') as captions_file:
        captions_str = captions_file.read()

    return build_subtitle_converter(captions_str, in_format)

