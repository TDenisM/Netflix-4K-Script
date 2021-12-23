import pywidevine.downloader.wvdownloaderconfig as wvdl_cfg

class VideoTrack(object):
    def __init__(self, encrypted, size, id, url, codec, bitrate, width, height):
        self.encrypted = encrypted
        self.size = size
        self.id = id
        self.url = url
        self.codec = codec
        self.bitrate = bitrate
        self.width = width
        self.height = height

    def get_type(self):
        return "video"

    def __repr__(self):
        return "(encrypted={}, size={}, id={}, url={}, codec={}, bitrate={}, width={}, height={})"\
            .format(self.encrypted, self.size, self.id, self.url, self.codec, self.bitrate, self.width, self.height)

    def get_filename(self, filename, decrypted=False, fixed=False):
        if not self.encrypted or decrypted:
            fn = wvdl_cfg.DECRYPTED_FILENAME
        else:
            fn = wvdl_cfg.ENCRYPTED_FILENAME
        if fixed:
            fn = fn + '_fixed.mp4'
        return fn.format(filename=filename, track_type="video", track_no=self.id)



class AudioTrack(object):
    def __init__(self, encrypted, size, id, url, codec, bitrate, language):
        self.encrypted = encrypted
        self.size = size
        self.id = id
        self.url = url
        self.codec = codec
        self.bitrate = bitrate
        self.language = language

    def get_type(self):
        return "audio"

    def get_lang(self):
        return "audio"

    def __repr__(self):
        return "(encrypted={}, language={}, size={}, id={}, url={}, codec={}, bitrate={})"\
            .format(self.encrypted, self.language, self.size, self.id, self.url, self.codec, self.bitrate)

    def get_filename(self, filename, decrypted=False, fixed=False):
        if not self.encrypted or decrypted:
            fn = wvdl_cfg.DECRYPTED_FILENAME_AUDIO
        else:
            fn = wvdl_cfg.ENCRYPTED_FILENAME_AUDIO
        if fixed:
            fn = fn + '_fixed.mka'
        return fn.format(filename=filename, language=self.language, track_type="audio", track_no=self.id)

class SubtitleTrack(object):
    def __init__(self, id, name, language_code, default, url, type):
        self.id = id
        self.name = name
        self.language_code = language_code
        self.url = url
        self.type = type
        self.default = default

    def __repr__(self):
        return "(id={}, name={}, language_code={}, url={}, type={})".format(self.id, self.name, self.language_code, self.url, self.type)

    def get_filename(self, filename, subtitle_format):
        return wvdl_cfg.SUBTITLES_FILENAME.format(filename=filename, language_code=self.language_code, id=self.id, subtitle_type=subtitle_format)