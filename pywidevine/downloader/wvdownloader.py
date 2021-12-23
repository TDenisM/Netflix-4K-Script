import logging
import threading
import pywidevine.downloader.wvdownloaderconfig as wvdl_cfg
from pywidevine.decrypt.wvdecryptconfig import WvDecryptConfig
from pywidevine.decrypt.wvdecrypt import WvDecrypt
from tqdm import tqdm
import requests
import pycaption
import pysubs2
import subprocess
import os
import shutil
import base64
import time
import binascii




class WvDownloader(object):
        
    def __init__(self, config):
        self.client = config.client
        self.filename = config.filename
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.threads = None

    def get_track_download_thread(self, track, bar_position):
        self.logger.debug("creating thread for {}_{}".format(track.get_type(), track.id))

        if track.encrypted:
            output_file = wvdl_cfg.ENCRYPTED_FILENAME
        else:
            output_file = wvdl_cfg.DECRYPTED_FILENAME
        output_file = output_file.format(filename=self.filename, track_type=track.get_type(), track_no=track.id)
        
        output_dir = output_file.split("\\")[0]
        output_name = output_file.split("\\")[1]
        
        file_size = track.size
        self.logger.debug("file size {}".format(file_size))

        def do_download():
            """
            pbar = tqdm(desc='{}_{}'.format(track.get_type(), track.id), total=int(file_size), unit="bytes", unit_scale=True, position=bar_position)
            downloaded_size = 0
            with open(output_file, 'wb') as fd:
                try:
                    r = self.client.get_track_download(track)
                    for chunk in r.iter_content(1024):
                        fd.write(chunk)
                        downloaded_size += len(chunk)
                        pbar.update(len(chunk))
                except requests.RequestException as e:
                    self.logger.debug("requests download error for track {}_{}, exiting".format(track.get_type(), track.id))
                    exit(1)
                except:
                    exit(1)
            pbar.close()
            """
            aria2_p = subprocess.run(["binaries\\aria2c_nf", "-x16", "-s16", track.url, f"--dir={output_dir}", f"--out={output_name}"])
            return aria2_p.returncode
        return threading.Thread(target=do_download)
        
        
        
    def get_track_download_thread_audio(self, track, bar_position):
        
        language = track.language
        #.replace("English [Original]", "English")
        
        #if track.language == "English [Original]":
        #        track.language = "English"
        self.logger.debug("creating thread for {}_{}".format(track.get_type(), track.id))

        if track.encrypted:
            output_file = wvdl_cfg.ENCRYPTED_FILENAME_AUDIO
        else:
            output_file = wvdl_cfg.DECRYPTED_FILENAME_AUDIO
        output_file = output_file.format(filename=self.filename, language=language, track_type=track.get_type(), track_no=track.id)
        
        output_dir = output_file.split("\\")[0]
        output_name = output_file.split("\\")[1]
        
        #output_file = fn.format(filename=self.filename, language=language, track_type="audio", track_no=track.id)
        file_size = track.size
        self.logger.debug("file size {}".format(file_size))

        def do_download():
            """
            pbar = tqdm(desc='{}_{}'.format(track.get_type(), track.id), total=int(file_size), unit="bytes", unit_scale=True, position=bar_position)
            downloaded_size = 0
            with open(output_file, 'wb') as fd:
                try:
                    r = self.client.get_track_download(track)
                    for chunk in r.iter_content(1024):
                        fd.write(chunk)
                        downloaded_size += len(chunk)
                        pbar.update(len(chunk))
                except requests.RequestException as e:
                    self.logger.debug("requests download error for track {}_{}, exiting".format(track.get_type(), track.id))
                    exit(1)
                except:
                    exit(1)
            pbar.close()
            """
            aria2_p = subprocess.run(["binaries\\aria2c_nf", "-x16", "-s16", track.url, f"--dir={output_dir}", f"--out={output_name}"])
            return aria2_p.returncode
        return threading.Thread(target=do_download)
        
        
    def find_str(self, s, char):
        index = 0
        if char in s:
            c = char[0]
            for ch in s:
                if ch == c and s[index:index + len(char)] == char:
                    return index
                index += 1

        return -1

    def Get_PSSH(self, mp4_file):
        currentFile = __file__
        realPath = os.path.realpath(currentFile)
        dirPath = os.path.dirname(realPath)
        dirName = os.path.basename(dirPath)
        mp4dump = dirPath + "/binaries/mp4dump.exe"
        WV_SYSTEM_ID = '[ed ef 8b a9 79 d6 4a ce a3 c8 27 dc d5 1d 21 ed]'
        pssh = None
        data = subprocess.check_output([mp4dump, '--format', 'json', '--verbosity', '1', mp4_file])
        data = json.loads(data)
        for atom in data:
                if atom['name'] == 'moov':
                        for child in atom['children']:
                                if child['name'] == 'pssh' and child['system_id'] == WV_SYSTEM_ID:
                                        pssh = child['data'][1:-1].replace(' ', '')
                                        pssh = binascii.unhexlify(pssh)
                                        #if pssh.startswith('\x08\x01'):
                                        #	pssh = pssh[0:]
                                        pssh = pssh[0:]
                                        pssh = base64.b64encode(pssh).decode('utf-8')
                                        return pssh

    def do_decrypt(self, config):
        wvdecrypt = WvDecrypt(config)
        chal = wvdecrypt.get_challenge()
        #sess_id = wvdecrypt.get_sid()
        license_b64 = self.client.get_license(chal, '123456')
        if not license_b64:
            return False
        wvdecrypt.update_license(license_b64)
        wvdecrypt.start_process()
        return True

    def download_and_convert_subtitle(self, subtitle):
        language_code = subtitle.language_code
        id = subtitle.id
        self.logger.info("downloading {}_{} subtitles".format(language_code, id))
        output_filename = wvdl_cfg.SUBTITLES_FILENAME.format(filename=self.filename, language_code=language_code, id=id, subtitle_type=self.config.subtitle_format)
        print(output_filename)
        print(subtitle)
        subtitle_text = self.client.get_subtitle_download(subtitle).text
        subtitle_text = self.client.finagle_subs(subtitle_text)
        if subtitle.type == "dfxp":
            srt_subs = pycaption.SRTWriter().write(pycaption.DFXPReader().read(subtitle_text.replace('tt:', '')))
        elif subtitle.type == "srt":
            srt_subs = subtitle_text
        else:
            self.logger.error("subtitle error")
            exit(1)
        if self.config.subtitle_format == 'srt':
            srt_subs = srt_subs.replace('&amp;', '&')
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(srt_subs)
        elif self.config.subtitle_format == 'ass':
            ass_subs = pysubs2.SSAFile.from_string(srt_subs)
            # you can modify ass_subs to change the output format/style here
            # eg
            # ass_subs.styles['Default'].fontname = 'That terrible font HS uses'
            # see https://github.com/tkarabela/pysubs2/blob/master/pysubs2/ssastyle.py etc
            ass_subs.styles['Default'].fontname = 'Open Sans Semibold'
            ass_subs.styles['Default'].fontsize = 36
            ass_subs.styles['Default'].outlinecolor = pysubs2.Color(19,7,2,0)
            ass_subs.styles['Default'].outline = 1.7
            ass_subs.styles['Default'].shadow = 0
            ass_subs.styles['Default'].marginl = 0
            ass_subs.styles['Default'].marginr = 0
            ass_subs.styles['Default'].marginv = 28
            ass_subs.info.update({'PlayResX': 848})
            ass_subs.info.update({'PlayResY': 480})
            ass_subs.save(output_filename)
        else:
            self.logger.error("unknown subtitle output format")
            exit(1)

    def do_ffmpeg_fix(self, track):
        ffmpeg_command = [wvdl_cfg.FFMPEG_BINARY_PATH,
                          "-i",
                          track.get_filename(self.filename, decrypted=True),
                          "-map_metadata",
                          "-1",
                          "-codec",
                          "copy",
                          track.get_filename(self.filename, decrypted=True, fixed=True)]
        subprocess.run(ffmpeg_command)

    def do_merge(self, vt, ats, sts):
        #exit(1)
        if self.client.needs_ffmpeg():
            vfn = vt.get_filename(self.filename, decrypted=True, fixed=True)
        else:
            vfn = vt.get_filename(self.filename, decrypted=True)
        
        for audio_track in ats:
                if 'ddplus-atmos-dash' in audio_track.codec:
                        audiocodec_file = 'DD+5.1.Atmos'
                if 'heaac-2-dash' in audio_track.codec:
                        audiocodec_file = 'AAC2.0'
                if 'ddplus-2.0-dash' in audio_track.codec:
                        audiocodec_file = 'DD+2.0'
                if 'ddplus-2.0-dash' in audio_track.codec:
                        audiocodec_file = 'DD+2.0'
                if 'ddplus-5.1-dash' in audio_track.codec:
                        audiocodec_file = 'DD+5.1'
                if 'ddplus-5.1hq-dash' in audio_track.codec:
                        audiocodec_file = 'DD+5.1'
        
        filename_audiocodec = self.filename.replace('AUDIOCODEC', audiocodec_file)
        filename_audiocodec_fixed = filename_audiocodec + '_fixed'
        filename_audiocodec_fixed1 = filename_audiocodec + '_fixed1'
        
        #self.config1 = config
        #filename = self.config1.filename + '_' + self.config1.tracktype + '_' + str(self.config1.trackno) + '_'
       
        currentFile = __file__
        realPath = os.path.realpath(currentFile)
        realPath = realPath.replace('pywidevine\\downloader\\wvdownloader.py', '')
        dirPath = os.path.dirname(realPath)
        dirName = os.path.basename(dirPath)
        wvDecrypterexe = dirPath + '/binaries/wvDecrypter/wvDecrypter.exe'
        challengeBIN = dirPath + '/binaries/wvDecrypter/challenge.bin'
        licenceBIN = dirPath + '/binaries/wvDecrypter/licence.bin'
        mp4dump = dirPath + "/binaries/mp4dump.exe"
        TEMP_FOLDER = dirPath + '/temp'
        
        
        #if 'h264' in self.filename: 
        #        print('x264x624x264x264')
        #        DECRYPTED_FILENAME = os.path.join(TEMP_FOLDER, self.filename + 'decrypted.264')
        if 'h265' in self.filename: 
                print('x265x265x265x265')
                vfn = vfn.replace('264', 'h265')
        #print(self.filename)
        #print(wvdl_cfg.MUXED_FILENAME.format(filename=DECRYPTED_FILENAME))
        mkvmerge_command = [wvdl_cfg.MKVMERGE_BINARY_PATH,
                            "--compression",
                            "-1:none",
                            "--no-global-tags",
                            "--output",
                            wvdl_cfg.MUXED_FILENAME.format(filename=filename_audiocodec),
                            "--language",
                            "0:und",
                            "(",
                            vfn,
                            ")"]
        for audio_track in ats:
            if self.client.needs_ffmpeg():
                fn = audio_track.get_filename(self.filename, decrypted=True, fixed=True)
            else:
                fn = audio_track.get_filename(self.filename, decrypted=True)
            audio_lang_dict = {
                'English': 'eng',
                'Spanish': 'spa',
                'European Spanish': 'spa',
                'Brazilian Portuguese': 'por',
                'Polish': 'pol',
                'Turkish': 'tur',
                'French': 'fre',
                'German': 'ger',
                'Italian': 'ita',
                'Czech': 'cze',
                'Japanese': 'jpn',
                'Hebrew': 'heb',
                'Norwegian': 'nor',
                'Swedish': 'swe',
                'Arabic': 'ara',
                'Dutch': 'dut',
                'Flemish': 'dut'
            }
            if audio_track.language and audio_track.language in audio_lang_dict:
                lang = '0:{}'.format(audio_lang_dict[audio_track.language])
            else:
                lang = '0:und'
            mkvmerge_command = mkvmerge_command + ["--compression",
                                                   "-1:none",
                                                   "--no-global-tags",
                                                   "--language",
                                                   lang,
                                                   "(",
                                                   fn,
                                                   ")"]
        
        #https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes
        for subtitle_track in sts:
            subtitle_lang_dict = {
                'en': 'eng',
                'es': 'spa',
                'es-ES': 'spa',
                'fr': 'fre',
                'de': 'ger',
                'it': 'ita',
                'pt-BR': 'por',
                'nl-BE': 'dut',
                'pl': 'pol',
                'fi': 'fin',
                'tl': 'tgl',
                'cs': 'cze',
                'zxx': 'zxx',
                'es-ES': 'spa',
                'nl': 'dut',
                'nb': 'nor',
                'da': 'dan',
                'pt': 'por',
                'pl': 'pol',
                'sv': 'swe',
                'fi': 'fin',
                'tr': 'tur',
                'he': 'heb',
                'ru': 'rus',
                'hu': 'hun',
                'id': 'ind',
                'el': 'ell',
                'ar': 'ara',
            }
            if subtitle_track.language_code and subtitle_track.language_code in subtitle_lang_dict:
                lang = '0:{}'.format(subtitle_lang_dict[subtitle_track.language_code])
            else:
                lang = '0:und'

            if subtitle_track.name == 'de':
                track_name = 'German_Full'
            if subtitle_track.name == 'en':
                track_name = 'English_Full'
            if subtitle_track.name == 'it':
                track_name = 'Italian_Full'
            if subtitle_track.name == 'es':
                track_name = 'Spanish_Full'
            if subtitle_track.name == 'es-ES':
                track_name = 'Spanish_Full'
            if subtitle_track.name == 'fr':
                track_name = 'French_Full'
            if subtitle_track.name == 'pl':
                track_name = 'Polish_Full'
            if subtitle_track.name == 'jp':
                track_name = 'Japanese_Full'
            if subtitle_track.name == 'tr':
                track_name = 'Turkish_Full'
            if subtitle_track.name == 'pt-BR':
                track_name = 'Brazilian.Portuguese_Full'
            if subtitle_track.name == 'da':
                track_name = 'Danish_Full'
            if subtitle_track.name == 'nb':
                track_name = 'Norwegian_Full'
            if subtitle_track.name == 'sv':
                track_name = 'Swedish_Full'
            if subtitle_track.name == 'ar':
                track_name = 'Arabic_Full'
            if subtitle_track.name == 'nl-BE':
                track_name = 'Flemish_Full'

            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'de':
                track_name = 'German_Forced'
            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'en':
                track_name = 'English_Forced'
            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'it':
                track_name = 'Italian_Forced'
            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'es':
                track_name = 'Spanish_Forced'
            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'es-ES':
                track_name = 'Spanish_Forced'
            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'fr':
                track_name = 'French_Forced'
            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'pl':
                track_name = 'Polish_Forced'
            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'jp':
                track_name = 'Japanese_Forced'
            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'tr':
                track_name = 'Turkish_Forced'
            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'pt-BR':
                track_name = 'Brazilian.Portuguese_Forced'
            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'da':
                track_name = 'Danish_Forced'
            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'nb':
                track_name = 'Norwegian_Forced'
            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'sv':
                track_name = 'Swedish_Forced'
            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'ar':
                track_name = 'Arabic_Forced'
            if subtitle_track.name == 'Forced' and subtitle_track.language_code == 'nl-BE':
                track_name = 'Flemish_Forced'


            """
            if subtitle_track.default:
                mkvmerge_command = mkvmerge_command + ["--compression",
                                                       "-1:none",
                                                       "--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:yes",
                                                       "--forced-track",
                                                       "0:yes",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]
            else:
                mkvmerge_command = mkvmerge_command + ["--compression",
                                                       "-1:none",
                                                       "--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]
            """


            if subtitle_track.default:
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:yes",
                                                       "--forced-track",
                                                       "0:yes",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            elif subtitle_track.name == 'Forced' and subtitle_track.language_code == 'en':
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            elif subtitle_track.name == 'Forced' and subtitle_track.language_code == 'it':
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            elif subtitle_track.name == 'Forced' and subtitle_track.language_code == 'es':
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            elif subtitle_track.name == 'Forced' and subtitle_track.language_code == 'es-ES':
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            elif subtitle_track.name == 'Forced' and subtitle_track.language_code == 'it':
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            elif subtitle_track.name == 'Forced' and subtitle_track.language_code == 'pl':
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            elif subtitle_track.name == 'Forced' and subtitle_track.language_code == 'jp':
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            elif subtitle_track.name == 'Forced' and subtitle_track.language_code == 'tr':
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            elif subtitle_track.name == 'Forced' and subtitle_track.language_code == 'pt-BR':
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            elif subtitle_track.name == 'Forced' and subtitle_track.language_code == 'da':
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            elif subtitle_track.name == 'Forced' and subtitle_track.language_code == 'nb':
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            elif subtitle_track.name == 'Forced' and subtitle_track.language_code == 'sv':
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            elif subtitle_track.name == 'Forced' and subtitle_track.language_code == 'ar':
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            elif subtitle_track.name == 'Forced' and subtitle_track.language_code == 'nl-BE':
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]

            else:
                mkvmerge_command = mkvmerge_command + ["--language",
                                                       lang,
                                                       "--sub-charset",
                                                       "0:UTF-8",
                                                       "--track-name",
                                                       #"0:{}".format(subtitle_track.name),
                                                       "0:{}".format( track_name),
                                                       "--default-track",
                                                       "0:no",
                                                       "--forced-track",
                                                       "0:no",
                                                       "(",
                                                       subtitle_track.get_filename(self.filename, self.config.subtitle_format),
                                                       ")"]



        if self.config.subtitle_format == 'ass':
            mkvmerge_command = mkvmerge_command + ["--attachment-mime-type",
                                                    "application/x-truetype-font",
                                                    "--attachment-name",
                                                    "OpenSans-Semibold.ttf",
                                                    "--attach-file",
                                                    "./fonts/OpenSans-Semibold.ttf"]

        subprocess.run(mkvmerge_command)


        """
        mkvmerge_command_fixed = [wvdl_cfg.MKVMERGE_BINARY_PATH,
                            "--compression",
                            "-1:none",
                            "--no-attachments",
                            "--no-track-tags",
                            "--no-global-tags",
                            "--disable-track-statistics-tags",
                            "--output",
                            wvdl_cfg.MUXED_FILENAME.format(filename=filename_audiocodec_fixed),
                            "(",
                            wvdl_cfg.MUXED_FILENAME.format(filename=filename_audiocodec),
                            ")"]

        subprocess.run(mkvmerge_command_fixed)

        os.remove(wvdl_cfg.MUXED_FILENAME.format(filename=filename_audiocodec))

        mkvmerge_command_fixed1 = [wvdl_cfg.MKVMERGE_BINARY_PATH,
                            "--compression",
                            "-1:none",
                            "--output",
                            wvdl_cfg.MUXED_FILENAME.format(filename=filename_audiocodec_fixed1),
                            "(",
                            wvdl_cfg.MUXED_FILENAME.format(filename=filename_audiocodec_fixed),
                            ")"]

        subprocess.run(mkvmerge_command_fixed1)

        os.remove(wvdl_cfg.MUXED_FILENAME.format(filename=filename_audiocodec_fixed))
        """

    def run(self):
        self.logger.info("wvdownloader starting")
        self.logger.info("logging client in")
        if self.client.login():
            self.logger.info("login successful")
        else:
            self.logger.error("login failed, please check credentials")
            exit(1)
        self.logger.info("getting track and widevine init data")
        print(self.config.quality)
        success, data = self.client.get_track_and_init_info(self.config.quality, self.config.profile)
        if not success:
            self.logger.error("get_track_and_init_info failed")
            exit(1)
        self.logger.info("track info and init data retrieved")
        if self.config.print_info:
            self.logger.info("info mode done, quitting")
            exit(0)
        
        vt, ats, sts, init_data_b64, cert_data_b64, device = data
        if not self.config.license:
            self.logger.info("downloading subtitles")
            #subs
            self.logger.debug("requested output format {}".format(self.config.subtitle_format))
            for subtitle in sts:
                self.download_and_convert_subtitle(subtitle)
            self.logger.info("all subtitles downloaded, merging")
            if self.config.subs_only:
                self.logger.info("subs downloaded, quitting")
                exit(0)
            self.logger.info("creating video & audio track download threads")
            threads = []
            threads.append(self.get_track_download_thread(vt, 0))
            for i, track in enumerate(ats):
                threads.append(self.get_track_download_thread_audio(track, i+1))
            self.logger.info("starting video&audio downloads")
            self.threads = threads
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.logger.info("video and audio tracks downloaded successfully")
            self.logger.info("decrypting encrypted tracks")
            self.logger.info("note: does not do this in parallel since we're IO bound anyway")
        enc_tracks = [x for x in [vt] + ats if x.encrypted]
        for track in enc_tracks:
            wvdecrypt_config = WvDecryptConfig(self.filename, track.get_type(), track.id, self.config.license, 
                                               init_data_b64, device, cert_data_b64=cert_data_b64)
            if self.config.gf is not None and self.client.client_config.config['region'] != 'us':
                curr_region = self.config.gf.region_get('prime')
                if self.client.client_config.config['region'] == 'uk' and curr_region != 'GB':
                    self.config.gf.region_set('prime','GB')
                elif self.client.client_config.config['region'].upper() != curr_region and self.client.client_config.config['region'] != 'uk':
                    self.config.gf.region_set('prime',self.client.client_config.config['region'].upper())
            try:
                if not self.do_decrypt(wvdecrypt_config):
                    return False
            except:
                if self.config.gf is not None and self.client.client_config.config['region'] != 'us':
                    curr_region = self.config.gf.region_get('prime')
                    if self.client.client_config.config['region'] == 'uk' and curr_region != 'GB':
                        self.config.gf.region_set('prime','GB')
                    elif self.client.client_config.config['region'].upper() != curr_region and self.client.client_config.config['region'] != 'uk':
                        self.config.gf.region_set('prime',self.client.client_config.config['region'].upper())
                if not self.do_decrypt(wvdecrypt_config):
                    return False

        if self.config.license:
            return True
        else:
            self.logger.info("all decrypting complete")

            if self.client.needs_ffmpeg():
                self.logger.info("processing mp4s with ffmpeg to fix the headers")
                #hdr hevc dv no ffmpeg

                self.do_ffmpeg_fix(vt)
                for track in ats:
                    self.do_ffmpeg_fix(track)
            
            #self.config.dont_mux = False
            if self.config.dont_mux:
                self.logger.info('moving tracks instead of muxing')
                #hdr hevc dv no ffmpeg fix
                if self.client.needs_ffmpeg():
                    vfn = vt.get_filename(self.filename, decrypted=True, fixed=True)
                else:
                    vfn = vt.get_filename(self.filename, decrypted=True)
                shutil.move(vfn, vfn.replace(wvdl_cfg.TEMP_FOLDER, wvdl_cfg.OUTPUT_FOLDER))
                for audio_track in ats:
                    if self.client.needs_ffmpeg():
                        fn = audio_track.get_filename(self.filename, decrypted=True, fixed=True)
                    else:
                        fn = audio_track.get_filename(self.filename, decrypted=True)
                    shutil.move(fn, fn.replace(wvdl_cfg.TEMP_FOLDER, wvdl_cfg.OUTPUT_FOLDER))
                for subtitle_track in sts:
                    fn = subtitle_track.get_filename(self.filename, self.config.subtitle_format)
                    shutil.move(fn, fn.replace(wvdl_cfg.TEMP_FOLDER, wvdl_cfg.OUTPUT_FOLDER))
            else:
                self.do_merge(vt, ats, sts)
            self.logger.info("file written, cleaning up temp")
        if self.config.skip_cleanup:
            self.logger.info('skipping clean')
            return True
        file_list = [f for f in os.listdir(wvdl_cfg.TEMP_FOLDER)]
        for f in file_list:
            if f.startswith("{}_".format(self.filename)):
                os.remove(os.path.join(wvdl_cfg.TEMP_FOLDER,f))
        self.logger.info("cleaned up temp")
        return True



