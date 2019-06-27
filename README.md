# pressurecooker
A library of various media processing functions and utilities


## Setting up your environment

* [Install ffmpeg](https://ffmpeg.org/) if you don't have it already.

* [Install ImageMagick](https://www.imagemagick.org/) if you don't have it already. (If you are running Windows, you will need to add a `MAGICK_HOME` environment variable that points to your ImageMagick directory)

* [Install GhostScript](https://www.ghostscript.com/) if you don't have it already.

* [Install poppler-utils](https://poppler.freedesktop.org/) if you don't have it already


## Converting caption files
The `pressurecooker` library contains utilities for converting caption files from a few various
formats into the preferred VTT format. The currently supported formats include:
- [DFXP](https://en.wikipedia.org/wiki/Timed_Text_Markup_Language) 
- [SAMI](https://en.wikipedia.org/wiki/SAMI)
- [SCC](http://www.theneitherworld.com/mcpoodle/SCC_TOOLS/DOCS/SCC_FORMAT.HTML)
- [SRT](https://en.wikipedia.org/wiki/SubRip) 
- [TTML](https://en.wikipedia.org/wiki/Timed_Text_Markup_Language)
- [WebVTT or just VTT](https://en.wikipedia.org/wiki/WebVTT)

> Within `pressurecooker`, the term "captions" and "subtitles" are used interchangeably. All of the 
classes and functions handling conversion use the "subtitles" term.  

### Creating the converter
If you already have the captions loaded into a string variable, you can create the convert like so:
```python
from pressurecooker.converters import build_subtitle_converter

# In this example, `captions_str` holds the caption contents
captions_str = ''
converter = build_subtitle_converter(captions_str)
```
otherwise, you can load from a file:
```python
from pressurecooker.converters import build_subtitle_converter_from_file

converter = build_subtitle_converter_from_file('/path/to/file.srt')
```

### Converting captions
The DFXP, SAMI, and TTML formats can encapsulate caption contents for multiple languages within one 
file. The SCC, SRT, and VTT formats are generally limited to a single language that isn't defined in
the file (the VTT may be an exception to this rule, but our converters do not detect its
language). Therefore to convert files, some special handling may be necessary depending on the 
content of the caption files.

For the SCC, SRT, and VTT, if you are sure of the format, this is the most basic approach:
```python
from pressurecooker.converters import build_subtitle_converter_from_file
from pressurecooker.subtitles import LANGUAGE_CODE_UNKNOWN

converter = build_subtitle_converter_from_file('/path/to/file.srt')

# For a SRT file, you can be certain the only language is LANGUAGE_CODE_UNKNOWN
output = converter.convert(LANGUAGE_CODE_UNKNOWN)
```

If you are unsure of the format, but you know the language of the file, it is safer to conditionally 
replace the `LANGUAGE_CODE_UNKNOWN` with that language: 
```python
from pressurecooker.converters import build_subtitle_converter_from_file
from pressurecooker.subtitles import LANGUAGE_CODE_UNKNOWN, InvalidSubtitleLanguageError

converter = build_subtitle_converter_from_file('/path/to/file')

# Replace unknown language code if present
if converter.has_language(LANGUAGE_CODE_UNKNOWN):
    converter.replace_unknown_language('en')
    
if not converter.has_language('en'):
    raise InvalidSubtitleLanguageError('Missing english!')
    
output = converter.convert('en')
```

A fuller example that could handle the other DFXP, SAMI, and TTML formats with multiple languages
may look like this:
```python
from pressurecooker.converters import build_subtitle_converter_from_file
from pressurecooker.subtitles import LANGUAGE_CODE_UNKNOWN, InvalidSubtitleLanguageError

converter = build_subtitle_converter_from_file('/path/to/file')

for lang_code in converter.get_language_codes():
    # `some_logic` would be your decisions on whether to use this language
    if some_logic(lang_code):
        converter.write("/path/to/file-{}.vtt".format(lang_code), lang_code)
    elif lang_code == LANGUAGE_CODE_UNKNOWN:
        raise InvalidSubtitleLanguageError('Unexpected unknown language')

```