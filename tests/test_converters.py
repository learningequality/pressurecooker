import os
import hashlib
import tempfile
from unittest import TestCase
from pressurecooker.converters import convert_subtitles
from pressurecooker.subtitles import InvalidSubtitleFormatError
from pressurecooker.subtitles import InvalidSubtitleLanguageError
from le_utils.constants import languages, file_formats

test_files_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'files', 'subtitles')


class SubtitleConverterTest(TestCase):
    def get_file_hash(self, path):
        hash = hashlib.md5()
        with open(path, 'rb') as fobj:
            for chunk in iter(lambda: fobj.read(2097152), b""):
                hash.update(chunk)

        return hash.hexdigest()

    def assertFileHashesEqual(self, expected_file, actual_file):
        expected_hash = self.get_file_hash(expected_file)
        actual_hash = self.get_file_hash(actual_file)
        self.assertEqual(expected_hash, actual_hash)

    def test_srt_conversion(self):
        expected_file = os.path.join(test_files_dir, 'basic.vtt')
        expected_language = languages.getlang_by_name('Arabic')

        with tempfile.NamedTemporaryFile() as actual_file:
            convert_subtitles(os.path.join(test_files_dir, 'basic.srt'), actual_file.name,
                              expected_language.code)
            self.assertFileHashesEqual(expected_file, actual_file.name)

    def test_expected_srt_conversion(self):
        expected_format = file_formats.SRT
        expected_file = os.path.join(test_files_dir, 'basic.vtt')
        expected_language = languages.getlang_by_name('Arabic')

        with tempfile.NamedTemporaryFile() as actual_file:
            convert_subtitles(os.path.join(test_files_dir, 'basic.srt'), actual_file.name,
                              expected_language.code, expected_format)
            self.assertFileHashesEqual(expected_file, actual_file.name)

    def test_not_expected_type(self):
        expected_format = file_formats.SCC
        expected_language = languages.getlang_by_name('Arabic')

        with tempfile.NamedTemporaryFile() as actual_file,\
                self.assertRaises(InvalidSubtitleFormatError):
            convert_subtitles(os.path.join(test_files_dir, 'basic.srt'),
                              actual_file.name, expected_language.code, expected_format)

    def test_invalid_format(self):
        expected_language = languages.getlang_by_name('English')

        with tempfile.NamedTemporaryFile() as actual_file,\
                self.assertRaises(InvalidSubtitleFormatError):
            convert_subtitles(os.path.join(test_files_dir, 'not.txt'), actual_file.name,
                              expected_language.code)

    def test_valid_language(self):
        expected_file = os.path.join(test_files_dir, 'encapsulated.vtt')
        expected_language = languages.getlang_by_name('English')

        with tempfile.NamedTemporaryFile() as actual_file:
            convert_subtitles(os.path.join(test_files_dir, 'encapsulated.sami'), actual_file.name,
                              expected_language.code)
            self.assertFileHashesEqual(expected_file, actual_file.name)

    def test_invalid_language(self):
        expected_language = languages.getlang_by_name('Spanish')

        with self.assertRaises(InvalidSubtitleLanguageError),\
                tempfile.NamedTemporaryFile() as actual_file:
            convert_subtitles(os.path.join(test_files_dir, 'encapsulated.sami'), actual_file.name,
                              expected_language.code)
