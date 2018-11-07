import webvtt


def srt2vtt(srt_filename, vtt_filename):
    try:
        #webvtt does not accept io.buffered only string path
        vtt = webvtt.from_srt(srt_filename)
        #webvtt does not accept io.buffered only string path
        vtt.save(vtt_filename)
    except webvtt.errors.MalformedCaptionError as e:
         return str(e)
