from pycaption import WebVTTReader, SRTReader, SAMIReader, SCCReader, DFXPReader
from .subtitles import SubtitleConverter, InvalidSubtitleFormatError
from .subtitles import AmbiguousSubtitleReader, EncapsulatedSubtitleReader
from le_utils.constants import file_formats


def build_dfxp_reader():
    return EncapsulatedSubtitleReader(DFXPReader())


def build_sami_reader():
    return EncapsulatedSubtitleReader(SAMIReader())


def build_scc_reader():
    return AmbiguousSubtitleReader(SCCReader())


def build_srt_reader():
    return AmbiguousSubtitleReader(SRTReader())


def build_vtt_reader():
    return AmbiguousSubtitleReader(WebVTTReader())


BUILD_READER_MAP = {
    file_formats.VTT: build_vtt_reader,
    file_formats.SRT: build_srt_reader,
    # TODO: update le-utils to 0.1.19
    # file_formats.SAMI: SAMIReader,
    # file_formats.SCC: SCCReader,
    # file_formats.TTML: DFXPReader,
    # file_formats.DFXP: DFXPReader,
    'sami': build_sami_reader,
    'scc': build_scc_reader,
    'ttml': build_dfxp_reader, # ttml == dfxp
    'dfxp': build_dfxp_reader,
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


def convert_subtitles(in_filename, out_filename, lang_code, in_format=None):
    """
    Converts `in_filename` to `out_filename`, where `out_filename` will be a VTT captions file

    :param in_filename: A string path to the captions file to parse
    :param out_filename: A string path to put the converted captions contents
    :param lang_code: A string with the language code
    :param in_format: A string with expected format of `in_filename`, otherwise detected
    :return:
    """
    readers = []
    if in_format is not None:
        readers.append(build_subtitle_reader(in_format))
    else:
        readers = build_subtitle_readers()

    SubtitleConverter(readers, lang_code).convert(in_filename, out_filename)

