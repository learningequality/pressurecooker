# pressurecooker
A library of various media processing functions and utilities


## Setting up your environment

* [Install ffmpeg](https://ffmpeg.org/) if you don't have it already.

* [Install ImageMagick](https://www.imagemagick.org/) if you don't have it already. (If you are running Windows, you will need to add a `MAGICK_HOME` environment variable that points to your ImageMagick directory)

* [Install GhostScript](https://www.ghostscript.com/) if you don't have it already.

* [Install poppler-utils](https://poppler.freedesktop.org/) if you don't have it already


## Converting caption files
The `pressurecooker` library contains utilities for converting caption files from a few various
formats into the preferred `VTT` format. The currently supported formats include:
- [DFXP](https://en.wikipedia.org/wiki/Timed_Text_Markup_Language) 
- [SAMI](https://en.wikipedia.org/wiki/SAMI)
- [SCC](http://www.theneitherworld.com/mcpoodle/SCC_TOOLS/DOCS/SCC_FORMAT.HTML)
- [SRT](https://en.wikipedia.org/wiki/SubRip) 
- [TTML](https://en.wikipedia.org/wiki/Timed_Text_Markup_Language)
- [WebVTT or just VTT](https://en.wikipedia.org/wiki/WebVTT)

> Within `pressurecooker`, the term "captions" and "subtitles" are used interchangeably. All of the 
classes and functions handling conversion use the "subtitles" term.  


### Language codes
The `DFXP`, `SAMI`, and `TTML` formats can encapsulate caption contents for multiple languages within one file.
The `SCC`, `SRT`, and `VTT` formats are generally limited to a single language that isn't defined in
the file (the `VTT` may be an exception to this rule, but our converters do not detect its language).
Therefore when converting these files we cannot know what language we are working
with and must instead use the constant `LANGUAGE_CODE_UNKNOWN` to extract the converted subtitles.

Note also that language codes used within the subtitle files might differ from
the LE internal language codes defined in `le-utils`.


### Creating a converter from a file
To create a subtitle converter from a local file path, use these commands:
```python
from pressurecooker.subtitles import build_subtitle_converter_from_file

converter = build_subtitle_converter_from_file('/path/to/file.srt')
```

### Creating a converter from a string
If you already have the captions loaded into a string variable,
you can create the converter like so:
```python
from pressurecooker.subtitles import build_subtitle_converter

captions_str = ''   # In this example, `captions_str` holds the caption contents
converter = build_subtitle_converter(captions_str)
```


### Converting captions
For the `SCC`, `SRT`, and `VTT` subtitles format that do not contain language code info,
you must refer to the language as the constant `LANGUAGE_CODE_UNKNOWN` at the
time of extracting the converted subtitles:
```python
from pressurecooker.subtitles import build_subtitle_converter_from_file
from pressurecooker.subtitles import LANGUAGE_CODE_UNKNOWN

converter = build_subtitle_converter_from_file('/path/to/file.srt')

# Option A: Obtain the contents of the converted VTT file as a string
output_str = converter.convert(LANGUAGE_CODE_UNKNOWN)

# Option B: Write the converted subtitles to a local path
converter.write("/path/to/file.vtt", LANGUAGE_CODE_UNKNOWN)
```
The `LANGUAGE_CODE_UNKNOWN` constant is the internal representation `pycaption`
uses to denote subtitles in an unknown language code. This will be the default
and only language code for `SCC`, `SRT`, and `VTT` subtitle converters.

If you are unsure of the format, but you know the language of the file,
it is safer to conditionally replace the `LANGUAGE_CODE_UNKNOWN` with that language:
```python
from pressurecooker.subtitles import build_subtitle_converter_from_file
from pressurecooker.subtitles import LANGUAGE_CODE_UNKNOWN

converter = build_subtitle_converter_from_file('/path/to/file')

# Replace unknown language code if present
if converter.has_language(LANGUAGE_CODE_UNKNOWN):
    converter.replace_unknown_language('en')
    
assert converter.has_language('en'), 'Must have English after replace'

output_str = converter.convert('en')
```

An example showing how to handle the subtitle formats like `DFXP`, `SAMI`, and `TTML`,
which have multiple languages is shown below:
```python
from pressurecooker.subtitles import build_subtitle_converter_from_file
from pressurecooker.subtitles import LANGUAGE_CODE_UNKNOWN, InvalidSubtitleLanguageError

converter = build_subtitle_converter_from_file('/path/to/file')

for lang_code in converter.get_language_codes():
    # `some_logic` would be your decisions on whether to use this language
    if some_logic(lang_code):
        converter.write("/path/to/file-{}.vtt".format(lang_code), lang_code)
    elif lang_code == LANGUAGE_CODE_UNKNOWN:
        raise InvalidSubtitleLanguageError('Unexpected unknown language')
```

