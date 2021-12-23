import logging
import subprocess
import re
from tqdm import tqdm
import base64
import progressbar
from time import sleep
import binascii

from pywidevine.cdm import cdm, deviceconfig
import pywidevine.downloader.wvdownloaderconfig as wvdl_cfg


class WvDecrypt(object):

    WV_SYSTEM_ID = [237, 239, 139, 169, 121, 214, 74, 206, 163, 200, 39, 220, 213, 29, 33, 237]

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.wvdecrypt_process = None
        self.logger.debug(self.log_message("wvdecrypt object created"))

        self.cdm = cdm.Cdm()

        def check_pssh(pssh_b64):
            pssh = base64.b64decode(pssh_b64)
            if not pssh[12:28] == bytes(self.WV_SYSTEM_ID):
                new_pssh = bytearray([0,0,0])
                new_pssh.append(32+len(pssh))
                new_pssh[4:] = bytearray(b'pssh')
                new_pssh[8:] = [0,0,0,0]
                new_pssh[13:] = self.WV_SYSTEM_ID
                new_pssh[29:] = [0,0,0,0]
                new_pssh[31] = len(pssh)
                new_pssh[32:] = pssh
                return base64.b64encode(new_pssh)
            else:
                return pssh_b64
        
        print("binitdata64 " + config.init_data_b64)

        if config.device == 'mpl':
         self.session = self.cdm.open_session(check_pssh(config.init_data_b64),deviceconfig.DeviceConfig(deviceconfig.device_android_generic_2))
        else:
         self.session = self.cdm.open_session(check_pssh(config.init_data_b64),deviceconfig.DeviceConfig(deviceconfig.device_android_generic_2))
        #print(self.session) device_nexus6_lvl1
        self.logger.debug(self.log_message("widevine session opened"))
        if self.config.server_cert_required:
            self.logger.debug(self.log_message("server cert set"))
            self.cdm.set_service_certificate(self.session,config.cert_data_b64)


    def log_message(self, msg):
        return "{}_{} : {}".format(self.config.tracktype, self.config.trackno, msg)
    """
    def start_process(self):
        if self.config.license:
            for key in self.cdm.get_keys(self.session):
                if key.type == 'CONTENT':
                    #key.kid.hex()
                    self.logger.logkey(self.log_message('{}:{}'.format(key.kid.hex(),key.key.hex())))
        else:
                
            #bar = progressbar.ProgressBar(maxval=progressbar.UnknownLength)#, \
            
            #widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
                
            self.logger.debug(self.log_message("starting mp4decrypt process"))
            self.logger.debug(self.config.build_commandline_list(self.cdm.get_keys(self.session)))
            print(self.cdm.get_keys(self.session))
            print(self.config.build_commandline_list(self.cdm.get_keys(self.session)))
            #exit(1)
            self.wvdecrypt_process = subprocess.Popen(
                self.config.build_commandline_list(self.cdm.get_keys(self.session)),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            
            
            #i = 0
            poll = self.wvdecrypt_process.poll()
            print(poll)
            #bar.start()
            while poll is None:
                    #bar.update(i)
                    #sleep(0.1)
                    #i = i +1
                    poll = self.wvdecrypt_process.poll()
            
            #bar.finish()
            
            self.wvdecrypt_process.wait()
            self.logger.debug(self.log_message("mp4decrypt decrypted successfully"))
         """

    def start_process(self):
        #self.key_file = open("key", "w")
        if self.config.license:
            for key in self.cdm.get_keys(self.session):
                if key.type == 'CONTENT':
                    self.logger.logkey(self.log_message('{}:{}'.format(key.kid.hex(),key.key.hex())))
                    #self.key_file.write(key.kid.hex() + ':' + key.key.hex() + '\n')
        else:
            self.logger.debug(self.log_message("starting mp4decrypt process"))
            self.logger.debug(self.config.build_commandline_list(self.cdm.get_keys(self.session)))
            print(self.cdm.get_keys(self.session))
            print(self.config.build_commandline_list(self.cdm.get_keys(self.session)))
            self.wvdecrypt_process = subprocess.Popen(
                self.config.build_commandline_list(self.cdm.get_keys(self.session)),
                #stdout=subprocess.PIPE,
                #stderr=subprocess.STDOUT
            )
            self.wvdecrypt_process.wait()
            self.logger.debug(self.log_message("mp4decrypt decrypted successfully"))
        #self.key_file.close()
        
    def get_challenge(self):
        return self.cdm.get_license_request(self.session)
        
    def get_sid(self):
        return (binascii.hexlify(self.session)).decode('utf-8').upper()

    def update_license(self, license_b64):
        self.cdm.provide_license(self.session, license_b64)
        return True

