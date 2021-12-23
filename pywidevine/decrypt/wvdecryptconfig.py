import pywidevine.downloader.wvdownloaderconfig as wvdl_cfg
import subprocess

class WvDecryptConfig(object):
    def __init__(self, filename, tracktype, trackno, license, init_data_b64, device, cert_data_b64=None):
        self.filename = filename
        self.tracktype = tracktype
        self.trackno = trackno
        self.init_data_b64 = init_data_b64
        self.device = device
        self.license = license
        if cert_data_b64 is not None:
            self.server_cert_required = True
            self.cert_data_b64 = cert_data_b64
        else:
            self.server_cert_required = False

    def get_filename(self, unformatted_filename):
        return unformatted_filename.format(filename=self.filename, track_type=self.tracktype, track_no=self.trackno)


    def find_str(self, s, char):
        index = 0
        if char in s:
            c = char[0]
            for ch in s:
                if ch == c and s[index:index + len(char)] == char:
                    return index
                index += 1
        return -1
        
    def get_kid(self, filename):
        mp4dump = subprocess.Popen([wvdl_cfg.MP4DUMP_BINARY_PATH, filename], stdout=subprocess.PIPE)
        mp4dump = str(mp4dump.stdout.read())
        A = self.find_str(mp4dump, 'default_KID')
        KID = mp4dump[A:A + 63].replace('default_KID = ', '').replace('[', '').replace(']', '').replace(' ', '')
        KID = KID.upper()
        KID_video = KID[0:8] + '-' + KID[8:12] + '-' + KID[12:16] + '-' + KID[16:20] + '-' + KID[20:32]
        if KID == '':
                KID = 'nothing'
        return KID.lower()

    def build_commandline_list(self, keys):
        
        KID_file = self.get_kid(self.get_filename(wvdl_cfg.ENCRYPTED_FILENAME))
        print(KID_file)
        
        commandline = [wvdl_cfg.MP4DECRYPT_BINARY_PATH]
        for key in keys:
            if key.type == 'CONTENT' and key.kid.hex() == KID_file:
                print("OK")
                commandline.append('--show-progress')
                commandline.append('--key')
                #key.kid.hex()
                #2 main high     1  hdr dv hevc
                if 'hdr' in self.get_filename(wvdl_cfg.ENCRYPTED_FILENAME):
                  commandline.append('{}:{}'.format(key.kid.hex(), key.key.hex()))
                else:
                  commandline.append('{}:{}'.format(key.kid.hex(), key.key.hex()))
        commandline.append(self.get_filename(wvdl_cfg.ENCRYPTED_FILENAME))
        commandline.append(self.get_filename(wvdl_cfg.DECRYPTED_FILENAME))
        return commandline
