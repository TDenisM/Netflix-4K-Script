import base64
from datetime import datetime
import gzip
import zlib
import json
import logging
from io import BytesIO
import random
import time
import os
import re

import requests
from Cryptodome.Cipher import AES
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.Hash import HMAC, SHA256
from Cryptodome.PublicKey import RSA
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util import Padding

import pywidevine.downloader.wvdownloaderconfig as wvdl_cfg
import pywidevine.clients.netflix.config as nf_cfg
import pywidevine.clients.netflix.subs as subs
from pywidevine.downloader.tracks import VideoTrack, AudioTrack, SubtitleTrack


# keys are not padded properly
def base64key_decode(payload):
    l = len(payload) % 4
    if l == 2:
        payload += '=='
    elif l == 3:
        payload += '='
    elif l != 0:
        raise ValueError('Invalid base64 string')
    return base64.urlsafe_b64decode(payload.encode('utf-8'))


class NetflixClient(object):
    def __init__(self, client_config):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("creating NetflixClient object")
        self.client_config = client_config
        self.session = requests.Session()
        self.current_message_id = 0
        self.rsa_key = None
        self.encryption_key = None
        self.sign_key = None
        self.sequence_number = None
        self.mastertoken = None
        self.useridtoken = None
        self.playbackContextId = None
        self.drmContextId = None
        self.tokens = []
        self.rndm = random.SystemRandom()
        #self.cookies = self.cookie_login()

    def login(self):
        self.logger.info("acquiring token & key for netflix api")
        config_dict = self.client_config.config

        #if self.cookies is None:
        #    self.cookies = self.cookie_login()

        if self.file_exists(wvdl_cfg.COOKIES_FOLDER, config_dict['msl_storage']):
            self.logger.info("old MSL data found, using")
            self.__load_msl_data()
        elif self.file_exists(wvdl_cfg.COOKIES_FOLDER, 'rsa_key.bin'):
            self.logger.info('old RSA key found, using')
            self.__load_rsa_keys()
            self.__perform_key_handshake()
        else:
            self.logger.info('create new RSA Keys')
            # Create new Key Pair and save
            self.rsa_key = RSA.generate(2048)
            self.__save_rsa_keys()
            self.__perform_key_handshake()

        if self.encryption_key:
            self.logger.info("negotiation successful, token & key acquired")
            return True
        else:
            self.logger.error("failed to perform key handshake")
            return False
    
    '''def cookie_login(self):
        """Logs into netflix"""
        config_dict = self.client_config.config
        post_data = {
            'email': config_dict['username'],
            'password': config_dict['password'],
            'rememberMe': 'true',
            'mode': 'login',
            'action': 'loginAction',
            'withFields': 'email,password,rememberMe,nextPage,showPassword',
            'nextPage': '',
            'showPassword': '',
        }
        req = self.session.post('https://www.netflix.com/login', post_data)
        return req.cookies'''

    def get_track_and_init_info(self,all_subs=False,only_subs=False):
        config_dict = self.client_config.config
        self.logger.info("video information")
        manifest_request_data = {
            'method': 'manifest',
            'lookupType': 'PREPARE',
            'viewableIds': [self.client_config.viewable_id],
            'profiles': config_dict['profiles'],
            'drmSystem': 'widevine',
            'appId': '14673889385265',
            'sessionParams': {
                'pinCapableClient': False,
                'uiplaycontext': 'null'
            },
            'sessionId': '14673889385265',
            'trackId': 0,
            'flavor': 'PRE_FETCH',
            'secureUrls': True,
            'supportPreviewContent': True,
            'forceClearStreams': False,
            'languages': ['en-US'],
            'clientVersion': '4.0004.899.011',
            'uiVersion': 'akira',
            'showAllSubDubTracks': all_subs
        }
        self.logger.debug("requesting manifest")
        request_data = self.__generate_msl_request_data(manifest_request_data)
        resp = self.session.post(nf_cfg.MANIFEST_ENDPOINT, request_data, proxies=self.client_config.get_proxies())

        data = {}


        try:
            # if the json() does not fail we have an error because the manifest response is a chuncked json response
            resp.json()
            self.logger.debug('Error getting Manifest: '+resp.text)
            return False, None
        except ValueError:
            # json() failed so parse the chunked response
            self.logger.debug('Got chunked Manifest Response: ' + resp.text)
            resp = self.__parse_chunked_msl_response(resp.text)
            #print(resp.text)
            self.logger.debug('Parsed chunked Response: ' + json.dumps(resp))
            data = self.__decrypt_payload_chunk(resp['payloads'])

        try:
            self.logger.debug("manifest json: %s" % data['result']['viewables'][0])
            self.playbackContextId = data['result']['viewables'][0]['playbackContextId']
            self.drmContextId = data['result']['viewables'][0]['drmContextId']
        except (KeyError, IndexError):
            self.logger.error('No viewables found')
            if 'errorDisplayMessage' in data['result']:
                self.logger.error('MSL Error Message: {}'.format(data['result']['errorDisplayMessage']))
            return False, None
        
        self.logger.debug(data)
        self.logger.debug("netflix cannot get title name from manifest")
        subtitle_tracks_js = data['result']['viewables'][0]['textTracks']
        subtitle_tracks_filtered = [x for x in subtitle_tracks_js if "bcp47" in x]

        self.logger.info("found {} subtitle tracks".format(len(subtitle_tracks_filtered)))
        for subtitle_track in subtitle_tracks_filtered:
            self.logger.info(
                "Name: {} bcp47: {} type: {}".format(subtitle_track['language'], subtitle_track['bcp47'], subtitle_track['trackType'])
            )

        if only_subs:
            wvdl_sts = []
            for i, subtitle in enumerate(subtitle_tracks_filtered):
                if not subtitle['isForced']:
                    wvdl_sts.append(
                                    SubtitleTrack(i, subtitle['language'], subtitle['bcp47'], True, next(iter(subtitle['downloadables'][0]['urls'].values())),
                                                'srt')
                                )
            return True, wvdl_sts

        video_tracks_js = data['result']['viewables'][0]['videoTracks'][0]['downloadables']

        self.logger.info("found {} video tracks".format(len(video_tracks_js)))
        for vid_id, video in enumerate(sorted(video_tracks_js, key= lambda v: int(v['bitrate']))):
            self.logger.info(
                "{} - Bitrate: {} Profile: {} Size: {} Width: {} Height: {}".format(vid_id, video['bitrate'],
                                                                                    video['contentProfile'],
                                                                                    video['size'],
                                                                                    video['width'],
                                                                                    video['height'])
            )

        audio_tracks_js = data['result']['viewables'][0]['audioTracks']
        audio_tracks_flattened = []

        for audio_track in audio_tracks_js:
            for downloadable in audio_track['downloadables']:
                new_track = audio_track.copy()
                new_track['downloadables'] = downloadable
                audio_tracks_flattened.append(new_track)

        self.logger.info("found {} audio tracks".format(len(audio_tracks_flattened)))
        for aud_id, audio_track in enumerate(
                sorted(audio_tracks_flattened, key=lambda v: int(v['downloadables']['bitrate']))):
            self.logger.info(
                "{} = Bitrate: {} Profile: {} Channels: {} Language: {} Lang: {} Size: {}".format(aud_id, audio_track[
                    'downloadables']['bitrate'],
                                                                                                  audio_track[
                                                                                                      'downloadables'][
                                                                                                      'contentProfile'],
                                                                                                  audio_track[
                                                                                                      'channels'],
                                                                                                  audio_track[
                                                                                                      'language'],
                                                                                                  audio_track['bcp47'],
                                                                                                  audio_track[
                                                                                                      'downloadables'][
                                                                                                      'size'])
            )


        self.logger.info("selected tracks")
        if config_dict['video_track'] is not None:
            self.logger.debug("VIDEO_TRACK_ID ARGUMENT: {}".format(config_dict['video_track']))
            if config_dict['video_track'] >= len(video_tracks_js):
                self.logger.error("selected video track does not exist")
                return False, []
            video_track = sorted(video_tracks_js, key= lambda v: int(v['bitrate']))[int(config_dict['video_track'])]
        else:
            video_track = sorted(video_tracks_js, key= lambda v: int(v['bitrate']), reverse=True)[0]
        self.logger.info("VIDEO - Bitrate: {} Profile: {} Size: {} Width: {} Height: {}".format(video_track['bitrate'],
                                                                                                video_track['contentProfile'],
                                                                                                video_track['size'],
                                                                                                video_track['width'],
                                                                                                video_track['height']))
        audio_tracks = []

        if config_dict['audio_tracks'] != []:
            self.logger.debug("AUDIO_TRACK_ID ARUGMENT: {}".format(config_dict['audio_tracks']))
            sorted_aud = sorted(audio_tracks_flattened, key=lambda v: int(v['downloadables']['bitrate']))
            for t_id in config_dict['audio_tracks']:
                audio_tracks.append(sorted_aud[int(t_id)])
        else:
            selected_track = None
            bitrate = 0
            channels = 0
            profile = None
            default_audio_lang = data['result']['viewables'][0]['orderedAudioTracks'][0]
            audio_lang_selectors = {
                'English': 'en',
                'French': 'fr',
                'German': 'de',
                'Italian': 'it',
                'Spanish': 'es',
                'Flemish': 'nl-BE',
                'Finnish': 'fi',
                'No Dialogue': 'zxx',
                'Czech': 'cs',
                'European Spanish': 'es-ES',
                'Japanese': 'ja',
                'Brazilian Portuguese': 'pt-BR',
                'Polish': 'pl',
                'Turkish': 'tr',
                'Mandarin': 'zh',
                'Cantonese': 'yue',
                'Arabic': 'ar',
                'Korean': 'ko',
                'Hebrew': 'he',
                'Norwegian': 'nb'
            }
            aud_profile_table = {
                'heaac-2-dash': 0,
                'ddplus-2.0-dash': 1,
                'ddplus-5.1-dash': 2,
                'dd-5.1-dash': 3
            }
            sorted_aud = sorted(audio_tracks_flattened, key=lambda v: int(v['downloadables']['bitrate']), reverse=True)

            audio_selected = ['en']
            if config_dict['audio_language'] is not None:
                audio_selected = config_dict['audio_language']

            for audio_select in audio_selected:
                for aud_track_sorted in sorted_aud:
                    if aud_track_sorted['bcp47'] == audio_select:
                        audio_tracks.append(aud_track_sorted)
                        break

                        # if selected_track == None:
                        #     selected_track = aud_track_sorted
                        #     bitrate = aud_track_sorted['downloadables']['bitrate']
                        #     channels = aud_track_sorted['channels']
                        #     profile = aud_profile_table[aud_track_sorted['downloadables']['contentProfile']]
                        # if (bitrate < aud_track_sorted['downloadables']['bitrate']) and (
                        #     channels <= aud_track_sorted['channels']) and (
                        #     profile <= aud_profile_table[aud_track_sorted['downloadables']['contentProfile']]):
                        #     selected_track = aud_track_sorted
                        #     bitrate = aud_track_sorted['downloadables']['bitrate']
                        #     channels = aud_track_sorted['channels']
                        #     profile = aud_profile_table[aud_track_sorted['downloadables']['contentProfile']]

                # audio_tracks.append(selected_track)
                # if selected_track == None:
                #     self.logger.error("netfix cannot auto select audio track, please specify at least one")
                #     return False, []
        for audio_track in audio_tracks:
            self.logger.info("AUDIO - Bitrate: {} Profile: {} Channels: {} Language: {} Size: {}".format(
                audio_track['downloadables']['bitrate'],
                audio_track['downloadables']['contentProfile'],
                audio_track['channels'],
                audio_track['language'],
                audio_track['downloadables']['size']))

        if config_dict['subtitle_languages'] is not None:
            self.logger.debug("SUBTITLE_LANGUAGE_ARGUMENT: {}".format(config_dict['subtitle_languages']))
            if 'all' in config_dict['subtitle_languages']:
                subtitle_tracks = subtitle_tracks_filtered
            else:
                subtitle_tracks = [x for x in subtitle_tracks_filtered if
                                   x['bcp47'] in config_dict['subtitle_languages']]
        else:
            subtitle_tracks = None
        if subtitle_tracks:
            for subtitle in subtitle_tracks:
                self.logger.info("SUBTITLE - Name: {} bcp47: {}".format(subtitle['language'], subtitle['bcp47']))

        init_data_b64 = data['result']['viewables'][0]['psshb64'][0]

        cert_data_b64 = data['result']['viewables'][0]['cert']

        wvdl_vt = VideoTrack(True, video_track['size'], 0, next(iter(video_track['urls'].values())),
                             video_track['contentProfile'], video_track['bitrate'],
                             video_track['width'], video_track['height'])

        wvdl_ats = []
        audio_languages = []
        

        for id, audio_track in enumerate(audio_tracks):
            audio_languages.append(audio_track['bcp47'])
            wvdl_ats.append(
                AudioTrack(False, audio_track['downloadables']['size'], id, next(iter(audio_track['downloadables']['urls'].values())),
                           audio_track['downloadables']['contentProfile'], audio_track['downloadables']['bitrate'], audio_track['language'])
            )

        wvdl_sts = []
        use_captions = { 'en': True }
        if subtitle_tracks:
            for track in subtitle_tracks:
                use_captions.update({track['bcp47']: True})
            for track in subtitle_tracks:
                if track['bcp47'] == 'en' and track['trackType'] == "SUBTITLES" and  not track['isForced']:
                    use_captions.update({track['bcp47']:False})
            for i, subtitle in enumerate(subtitle_tracks):
                if 'en' in audio_languages:
                    if subtitle['isForced'] and subtitle['bcp47'] == 'en' and (subtitle['trackType'] == "SUBTITLES" or use_captions[subtitle['bcp47']] == True):
                        wvdl_sts.append(
                            SubtitleTrack(i, 'Forced', subtitle['bcp47'], True, next(iter(subtitle['downloadables'][0]['urls'].values())),
                                        'srt')
                        )
                    elif not subtitle['isForced'] and (subtitle['trackType'] == "SUBTITLES" or use_captions[subtitle['bcp47']] == True):
                        wvdl_sts.append(
                            SubtitleTrack(i, subtitle['language'], subtitle['bcp47'], False, next(iter(subtitle['downloadables'][0]['urls'].values())),
                                        'srt')
                        )
                else:
                    if not subtitle['isForced'] and subtitle['bcp47'] == 'en' and (subtitle['trackType'] == "SUBTITLES" or use_captions[subtitle['bcp47']] == True):
                        wvdl_sts.append(
                            SubtitleTrack(i, subtitle['language'], subtitle['bcp47'], True, next(iter(subtitle['downloadables'][0]['urls'].values())),
                                        'srt')
                        )
                    elif not subtitle['isForced'] and (subtitle['trackType'] == "SUBTITLES" or use_captions[subtitle['bcp47']] == True):
                        wvdl_sts.append(
                            SubtitleTrack(i, subtitle['language'], subtitle['bcp47'], False, next(iter(subtitle['downloadables'][0]['urls'].values())),
                                        'srt')
                        )
        
        return True, [wvdl_vt, wvdl_ats, wvdl_sts, init_data_b64, cert_data_b64]


    def get_license(self, challenge):
        #
        self.logger.info("doing license request")
        self.logger.debug("challenge - {}".format(base64.b64encode(challenge)))
        license_request_data = {
            'method': 'license',
            'licenseType': 'STANDARD',
            'clientVersion': '4.0004.899.011',
            'uiVersion': 'akira',
            'languages': ['en-US'],
            'playbackContextId': self.playbackContextId,
            'drmContextIds': [self.drmContextId],
            'challenges': [{
                'dataBase64': base64.b64encode(challenge).decode('utf-8'),
                'sessionId': "14673889385265"
            }],
            'clientTime': int(time.time()),
            'xid': int((int(time.time()) + 0.1612) * 1000)

        }
        request_data = self.__generate_msl_request_data(license_request_data)

        resp = self.session.post(nf_cfg.LICENSE_ENDPOINT, request_data, proxies=self.client_config.get_proxies())

        try:
            # If is valid json the request for the licnese failed
            resp.json()
            self.logger.debug('Error getting license: '+resp.text)
            exit(1)
        except ValueError:
            # json() failed so we have a chunked json response
            resp = self.__parse_chunked_msl_response(resp.text)
            data = self.__decrypt_payload_chunk(resp['payloads'])
            if data['success'] is True:
                return data['result']['licenses'][0]['data']
            else:
                self.logger.debug('Error getting license: ' + json.dumps(data))
                exit(1)


    def __get_base_url(self, urls):
        for key in urls:
            return urls[key]

    def __decrypt_payload_chunk(self, payloadchunks):
        decrypted_payload = ''
        for chunk in payloadchunks:
            payloadchunk = json.loads(chunk)
            try:
                encryption_envelope = str(bytes(payloadchunk['payload'], encoding="utf-8").decode('utf8'))
            except TypeError:
                encryption_envelope = payloadchunk['payload']
            # Decrypt the text
            cipher = AES.new(self.encryption_key, AES.MODE_CBC, base64.standard_b64decode(json.loads(base64.standard_b64decode(encryption_envelope))['iv']))
            plaintext = cipher.decrypt(base64.standard_b64decode(json.loads(base64.standard_b64decode(encryption_envelope))['ciphertext']))
            # unpad the plaintext
            plaintext = json.loads((Padding.unpad(plaintext, 16)))
            data = plaintext['data']

            # uncompress data if compressed
            if plaintext['compressionalgo'] == 'GZIP':
                data = zlib.decompress(base64.standard_b64decode(data), 16 + zlib.MAX_WBITS)
            else:
                data = base64.standard_b64decode(data)

            decrypted_payload += data.decode('utf-8')
        decrypted_payload = json.loads(decrypted_payload)[1]['payload']['data']
        decrypted_payload = base64.standard_b64decode(decrypted_payload)
        return json.loads(decrypted_payload)

    def __parse_chunked_msl_response(self, message):
        header = message.split('}}')[0] + '}}'
        payloads = re.split(',\"signature\":\"[0-9A-Za-z=/+]+\"}', message.split('}}')[1])
        payloads = [x + '}' for x in payloads][:-1]

        return {
            'header': header,
            'payloads': payloads
        }

    def __generate_msl_request_data(self, data):
        header_encryption_envelope = self.__encrypt(self.__generate_msl_header())
        header = {
            'headerdata': base64.standard_b64encode(header_encryption_envelope.encode('utf-8')).decode('utf-8'),
            'signature': self.__sign(header_encryption_envelope).decode('utf-8'),
            'mastertoken': self.mastertoken,
        }
        # Serialize the given Data
        serialized_data = json.dumps(data)
        serialized_data = serialized_data.replace('"', '\\"')
        serialized_data = '[{},{"headers":{},"path":"/cbp/cadmium-13","payload":{"data":"' + serialized_data + '"},"query":""}]\n'
        compressed_data = self.__compress_data(serialized_data)

        # Create FIRST Payload Chunks
        first_payload = {
            "messageid": self.current_message_id,
            "data": compressed_data.decode('utf-8'),
            "compressionalgo": "GZIP",
            "sequencenumber": 1,
            "endofmsg": True
        }
        first_payload_encryption_envelope = self.__encrypt(json.dumps(first_payload))
        first_payload_chunk = {
            'payload': base64.standard_b64encode(first_payload_encryption_envelope.encode('utf-8')).decode('utf-8'),
            'signature': self.__sign(first_payload_encryption_envelope).decode('utf-8'),
        }
        request_data = json.dumps(header) + json.dumps(first_payload_chunk)
        return request_data

    def __compress_data(self, data):
        # GZIP THE DATA
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="w") as f:
            f.write(data.encode('utf-8'))
        return base64.standard_b64encode(out.getvalue())

    def __generate_msl_header(self, is_handshake=False, is_key_request=False, compressionalgo="GZIP", encrypt=True):
        """
        Function that generates a MSL header dict
        :return: The base64 encoded JSON String of the header
        """
        self.current_message_id = self.rndm.randint(0, pow(2, 52))

        header_data = {
            'sender': self.client_config.config['esn'],
            'handshake': is_handshake,
            'nonreplayable': False,
            'capabilities': {
                'languages': ["en-US"],
                'compressionalgos': [],
                'encoderformats' : ['JSON'],
            },
            'recipient': 'Netflix',
            'renewable': True,
            'messageid': self.current_message_id,
            'timestamp': 1467733923,
        }

        # Add compression algo if not empty
        if compressionalgo is not "":
            header_data['capabilities']['compressionalgos'].append(compressionalgo)

        # If this is a keyrequest act diffrent then other requests
        if is_key_request:
            public_key = base64.standard_b64encode(self.rsa_key.publickey().exportKey(format='DER')).decode('utf-8')
            header_data['keyrequestdata'] = [{
                'scheme': 'ASYMMETRIC_WRAPPED',
                'keydata': {
                    'publickey': public_key,
                    'mechanism': 'JWK_RSA',
                    'keypairid': 'superKeyPair'
                }
            }]
            #header_data['userauthdata'] = {
            #    'scheme' : 'NETFLIXID',
            #    'authdata' : {
            #        'netflixid' : self.cookies['NetflixId'],
            #        'securenetflixid' : self.cookies['SecureNetflixId'],
            #    }
            #}
            #header_data['keyrequestdata'] = [{
            #    'scheme': 'WIDEVINE',
            #    'keydata': {
            #        'keyrequest':'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',
            #    },
            #}]
        else:
            if 'usertoken' in self.tokens:
                pass
            else:
                # Auth via email and password
                header_data['userauthdata'] = {
                    'scheme': 'EMAIL_PASSWORD',
                    'authdata': {
                        'email': self.client_config.config['username'],
                        'password': self.client_config.config['password']
                    }
                }
        return json.dumps(header_data)

    def __encrypt(self, plaintext):
        """
        Encrypt the given Plaintext with the encryption key
        :param plaintext:
        :return: Serialized JSON String of the encryption Envelope
        """
        iv = get_random_bytes(16)
        encryption_envelope = {
            'ciphertext': '',
            'keyid': self.client_config.config['esn'] + '_' + str(self.sequence_number),
            'sha256': 'AA==',
            'iv': base64.standard_b64encode(iv).decode('utf-8')
        }
        # Padd the plaintext
        plaintext = Padding.pad(plaintext.encode('utf-8'), 16)
        # Encrypt the text
        cipher = AES.new(self.encryption_key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(plaintext)
        encryption_envelope['ciphertext'] = base64.standard_b64encode(ciphertext).decode('utf-8')
        return json.dumps(encryption_envelope)

    def __sign(self, text):
        """
        Calculates the HMAC signature for the given text with the current sign key and SHA256
        :param text:
        :return: Base64 encoded signature
        """
        signature = HMAC.new(self.sign_key, text.encode('utf-8'), SHA256).digest()
        return base64.standard_b64encode(signature)

    def __perform_key_handshake(self):
        header = self.__generate_msl_header(is_key_request=True, is_handshake=True, compressionalgo="", encrypt=False)
        request = {
            'entityauthdata': {
                'scheme': 'NONE',
                'authdata': {
                    'identity': self.client_config.config['esn']
                }
            },
            'headerdata': base64.standard_b64encode(header.encode('utf-8')).decode('utf-8'),
            'signature': '',
        }
        self.logger.debug('Key Handshake Request:')
        self.logger.debug(json.dumps(request))

        resp = self.session.post(nf_cfg.MANIFEST_ENDPOINT, json.dumps(request, sort_keys=True), proxies=self.client_config.get_proxies())
        if resp.status_code == 200:
            resp = resp.json()
            if 'errordata' in resp:
                self.logger.debug('Key Exchange failed')
                self.logger.debug(base64.standard_b64decode(resp['errordata']))
                return False
            self.logger.debug(resp)
            self.logger.debug('Key Exchange Sucessful')
            self.__parse_crypto_keys(json.JSONDecoder().decode(base64.standard_b64decode(resp['headerdata']).decode('utf-8')))
        else:
            self.logger.debug('Key Exchange failed')
            self.logger.debug(resp.text)

    def __parse_crypto_keys(self, headerdata):
        self.__set_master_token(headerdata['keyresponsedata']['mastertoken'])
        #self.__set_userid_token(headerdata['useridtoken'])
        # Init Decryption
        encrypted_encryption_key = base64.standard_b64decode(headerdata['keyresponsedata']['keydata']['encryptionkey'])
        encrypted_sign_key = base64.standard_b64decode(headerdata['keyresponsedata']['keydata']['hmackey'])
        cipher_rsa = PKCS1_OAEP.new(self.rsa_key)

        # Decrypt encryption key
        encryption_key_data = json.JSONDecoder().decode(cipher_rsa.decrypt(encrypted_encryption_key).decode('utf-8'))
        self.encryption_key = base64key_decode(encryption_key_data['k'])

        # Decrypt sign key
        sign_key_data = json.JSONDecoder().decode(cipher_rsa.decrypt(encrypted_sign_key).decode('utf-8'))
        self.sign_key = base64key_decode(sign_key_data['k'])

        self.__save_msl_data()
        self.handshake_performed = True

    def __load_msl_data(self):
        msl_data = json.JSONDecoder().decode(
            self.load_file(wvdl_cfg.COOKIES_FOLDER, self.client_config.config['msl_storage']).decode('utf-8'))
        # Check expire date of the token
        master_token = json.JSONDecoder().decode(
            base64.standard_b64decode(msl_data['tokens']['mastertoken']['tokendata']).decode('utf-8'))
        valid_until = datetime.utcfromtimestamp(int(master_token['expiration']))
        present = datetime.now()
        difference = valid_until - present
        difference = difference.total_seconds() / 60 / 60
        # If token expires in less then 10 hours or is expires renew it
        if difference < 10:
            self.__load_rsa_keys()
            self.__perform_key_handshake()
            return

        self.__set_master_token(msl_data['tokens']['mastertoken'])
        #self.__set_userid_token(msl_data['tokens']['useridtoken'])
        self.encryption_key = base64.standard_b64decode(msl_data['encryption_key'])
        self.sign_key = base64.standard_b64decode(msl_data['sign_key'])

    def __save_msl_data(self):
        """
        Saves the keys and tokens in json file
        :return:
        """
        data = {
            "encryption_key": base64.standard_b64encode(self.encryption_key).decode('utf-8'),
            'sign_key': base64.standard_b64encode(self.sign_key).decode('utf-8'),
            'tokens': {
                'mastertoken': self.mastertoken,
                #'useridtoken': self.useridtoken,
            }
        }
        serialized_data = json.JSONEncoder().encode(data)
        self.save_file(wvdl_cfg.COOKIES_FOLDER, self.client_config.config['msl_storage'], serialized_data.encode('utf-8'))

    def __set_master_token(self, master_token):
        self.mastertoken = master_token
        self.sequence_number = json.JSONDecoder().decode(base64.standard_b64decode(master_token['tokendata']).decode('utf-8'))[
            'sequencenumber']

    def __set_userid_token(self, userid_token):
        self.useridtoken = userid_token

    def __load_rsa_keys(self):
        loaded_key = self.load_file(wvdl_cfg.COOKIES_FOLDER, self.client_config.config['rsa_key'])
        self.rsa_key = RSA.importKey(loaded_key)

    def __save_rsa_keys(self):
        self.logger.debug('Save RSA Keys')
        # Get the DER Base64 of the keys
        encrypted_key = self.rsa_key.exportKey()
        self.save_file(wvdl_cfg.COOKIES_FOLDER, self.client_config.config['rsa_key'], encrypted_key)

    @staticmethod
    def file_exists(msl_data_path, filename):
        """
        Checks if a given file exists
        :param filename: The filename
        :return: True if so
        """
        return os.path.isfile(os.path.join(msl_data_path, filename))

    @staticmethod
    def save_file(msl_data_path, filename, content):
        """
        Saves the given content under given filename
        :param filename: The filename
        :param content: The content of the file
        """
        with open(os.path.join(msl_data_path,filename), 'wb') as file_:
            file_.write(content)
            file_.flush()
            file_.close()

    @staticmethod
    def load_file(msl_data_path, filename):
        """
        Loads the content of a given filename
        :param filename: The file to load
        :return: The content of the file
        """
        with open(os.path.join(msl_data_path,filename), 'rb') as file_:
            file_content = file_.read()
            file_.close()
        return file_content


    def get_track_download(self, track):
        return self.session.get(track.url, stream=True, proxies=self.client_config.get_proxies())

    def get_subtitle_download(self, track):
        try:
            req = self.session.get(track.url, proxies=self.client_config.get_proxies())
        except:
            while True:
                try:
                    req = self.session.get(track.url, proxies=self.client_config.get_proxies())
                    return req
                except:
                    continue
        return req


    def get_wvconfig_options(self):
            return {'server_cert_required': True, 'pssh_header': True}

    def needs_ffmpeg(self):
        return True

    def finagle_subs(self, subtitles):
        return subs.to_srt(subtitles)

