import re
import os
import platform

# constants

BINARIES_FOLDER = 'binaries'
COOKIES_FOLDER = 'cookies'
TEMP_FOLDER = 'temp'
OUTPUT_FOLDER = 'output'

MP4DECRYPT_BINARY = 'mp4decrypt'
MKVMERGE_BINARY = 'mkvmerge'
MP4DUMP_BINARY = 'mp4dump'
FFMPEG_BINARY = 'avconv'

if platform.system() == 'Windows':
    MP4DECRYPT_BINARY = 'mp4decrypt.exe'
    MKVMERGE_BINARY = 'mkvmerge.exe'
    MP4DUMP_BINARY = 'mp4dump.exe'
    #FFMPEG_BINARY = 'avconv.exe'
    FFMPEG_BINARY = 'ffmpeg.exe'

MP4DECRYPT_BINARY_PATH = os.path.join(BINARIES_FOLDER, MP4DECRYPT_BINARY)
MKVMERGE_BINARY_PATH = os.path.join(BINARIES_FOLDER, MKVMERGE_BINARY)
MP4DUMP_BINARY_PATH = os.path.join(BINARIES_FOLDER, MP4DUMP_BINARY)
FFMPEG_BINARY_PATH = os.path.join(BINARIES_FOLDER, FFMPEG_BINARY)

MP4DUMP_REGEX = re.compile(b"sample info count = (\d+)")

BASE_TRACK_FILENAME = '{filename}_{track_type}_{track_no}_'
BASE_TRACK_FILENAME_AUDIO = '{filename}_{track_type}_{track_no}_{language}_'


ENCRYPTED_FILENAME = os.path.join(TEMP_FOLDER, BASE_TRACK_FILENAME + 'encrypted.mp4')
#DECRYPTED_FILENAME = os.path.join(TEMP_FOLDER, BASE_TRACK_FILENAME + 'decrypted.mp4')

DECRYPTED_FILENAME = os.path.join(TEMP_FOLDER, BASE_TRACK_FILENAME + 'decrypted.mp4')

ENCRYPTED_FILENAME_AUDIO = os.path.join(TEMP_FOLDER, BASE_TRACK_FILENAME_AUDIO + 'encrypted.mp4')
DECRYPTED_FILENAME_AUDIO = os.path.join(TEMP_FOLDER, BASE_TRACK_FILENAME_AUDIO + 'decrypted.mp4')

SUBTITLES_FILENAME = os.path.join(TEMP_FOLDER, '{filename}_subtitles_{language_code}_{id}.{subtitle_type}')
MUXED_FILENAME = os.path.join(OUTPUT_FOLDER, '{filename}.mkv')


class WvDownloaderConfig(object):
    def __init__(self, client, filename, subtitle_format, print_info, skip_cleanup, dont_mux, subs_only, license, quality, profile, gf=None):
        self.client = client
        self.filename = filename
        self.subtitle_format = subtitle_format
        self.print_info = print_info
        self.skip_cleanup = skip_cleanup
        self.dont_mux = dont_mux
        self.subs_only = subs_only
        self.license = license
        self.quality = quality
        self.profile = profile
        self.gf = gf
