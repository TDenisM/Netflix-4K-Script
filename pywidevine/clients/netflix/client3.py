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
from itertools import islice


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
	id = int(time.time() * 10000)
	"""
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
	    'clientVersion': '6.0011.474.011',
	    'uiVersion': 'shakti-v25d2fa21',
	    'showAllSubDubTracks': all_subs
	    
	}
	"""
	#'profiles': config_dict['profiles'],
	#profiles = ['playready-h264mpl30-dash', 'playready-h264mpl31-dash', 'playready-h264mpl40-dash', 'playready-h264hpl30-dash', 'playready-h264hpl31-dash', 'playready-h264hpl40-dash', 'heaac-2-dash', 'dfxp-ls-sdh', 'simplesdh',]
	#profiles = ['playready-h264mpl30-dash', 'playready-h264mpl31-dash', 'playready-h264mpl40-dash', 'playready-h264hpl30-dash', 'playready-h264hpl31-dash', 'playready-h264hpl40-dash', 'heaac-2-dash', 'BIF240', 'BIF320']
	
	manifest_request_data = {
	    'version': 2,
	    'url': '/manifest',
	    'id': id,
	    'esn': self.client_config.config['esn'],
	    'languages' : ['en-US'],
	    'uiVersion': 'shakti-v25d2fa21',
	    'clientVersion': '6.0011.474.011',
	    'params': {
		'type': 'standard',
		'viewableId': [self.client_config.viewable_id],
		'profiles': config_dict['profiles'],             
		'flavor': 'PRE_FETCH',
		'drmType': 'widevine',
		'drmVersion': 25,
		'usePsshBox': True,
		'isBranching': False,
		'useHttpsStreams': False,
		'imageSubtitleHeight': 1080,
		'uiVersion': 'shakti-vb45817f4',
		'clientVersion': '6.0011.511.011',
		'supportsPreReleasePin': True,
		'supportsWatermark': True,
		'showAllSubDubTracks': False,
		'titleSpecificData': {},
		'videoOutputInfo': [{
		    'type': 'DigitalVideoOutputDescriptor',
		    'outputType': 'unknown',
		    'supportedHdcpVersions': [],
		    'isHdcpEngaged': False
		}],
		'preferAssistiveAudio': False,
		'isNonMember': False
	    }
	}
	self.logger.debug("requesting manifest")
	request_data = self.__generate_msl_request_data(manifest_request_data)
	resp = self.session.post(nf_cfg.MANIFEST_ENDPOINT, request_data, proxies=self.client_config.get_proxies())
	self.logger.debug(manifest_request_data)
	data = {}


	try:
	    # if the json() does not fail we have an error because the manifest response is a chuncked json response
	    resp.json()
	    self.logger.debug('Error getting Manifest: '+resp.text)
	    return False, None
	except ValueError:
	    # json() failed so parse the chunked response
	    global data1
	    self.logger.debug('Got chunked Manifest Response: ' + resp.text)
	    resp = self.__parse_chunked_msl_response(resp.text)
	    #print(resp.text)
	    self.logger.debug('Parsed chunked Response: ' + json.dumps(resp))
	    data = self.__decrypt_payload_chunk(resp['payloads'])
	    data1 = self.__decrypt_payload_chunk(resp['payloads'])
	    fobj = open("manifest.json", "w") 
	    #fobj.write(str(data['result']))
	    #data['result']['links']['license']['href']
	    playlist = json.dumps(data)
	    fobj.write(playlist)
	    fobj.close()
	    self.logger.debug(data['result'])
	    #[0]

	try:
	    
	    #self.logger.debug("manifest json: %s" % data['result']['viewables'][0])
	    #self.playbackContextId = data['result']['viewables'][0]['playbackContextId']
	    #self.drmContextId = data['result']['viewables'][0]['drmContextId']
	    self.logger.debug("manifest json: %s" % data['result'])
	    self.playbackContextId = data['result']['playbackContextId']
	    self.drmContextId = data['result']['drmContextId']
	except (KeyError, IndexError):
	    self.logger.error('No viewables found')
	    if 'errorDisplayMessage' in data['result']:
		self.logger.error('MSL Error Message: {}'.format(data['result']['errorDisplayMessage']))
	    return False, None
	
	self.logger.debug(data)
	self.logger.debug("netflix cannot get title name from manifest")
	#subtitle_tracks_js = data['result']['viewables'][0]['textTracks']
	subtitle_tracks_js = data['result']['timedtexttracks']
	self.logger.debug(len(subtitle_tracks_js))
	subtitle_tracks_filtered = [x for x in subtitle_tracks_js if "language" in x]
	subtitle_tracks_filtered = list(islice(subtitle_tracks_filtered, len(subtitle_tracks_js)-1))
	self.logger.debug(subtitle_tracks_filtered)

	self.logger.info("found {} subtitle tracks".format(len(subtitle_tracks_filtered)))
	for subtitle_track in subtitle_tracks_filtered:
	    self.logger.info(
		"Name: {} bcp47: {} type: {}".format(subtitle_track['language'], subtitle_track['language'], subtitle_track['trackType'])
	    )

	if only_subs:
	    wvdl_sts = []
	    for i, subtitle in enumerate(subtitle_tracks_filtered):
		if not subtitle['isForcedNarrative']:
		    wvdl_sts.append(
				    SubtitleTrack(i, subtitle['language'], subtitle['language'], True, next(iter(list(subtitle['downloadables'][0]['urls'].values()))),
						'srt')
				)
	    return True, wvdl_sts

	#video_tracks_js = data['result']['viewables'][0]['videoTracks'][0]['downloadables']
	video_tracks_js = data['result']['video_tracks'][0]['streams']

	self.logger.info("found {} video tracks".format(len(video_tracks_js)))
	for vid_id, video in enumerate(sorted(video_tracks_js, key= lambda v: int(v['bitrate']))):
	    self.logger.info(
		"{} - Bitrate: {} Profile: {} Size: {} Width: {} Height: {}".format(vid_id, video['bitrate'],
										    video['content_profile'],
										    video['size'],
										    video['res_w'],
										    video['res_h'])
	    )

	audio_tracks_js = data['result']['audio_tracks']
	audio_tracks_flattened = []

	for audio_track in audio_tracks_js:
	    for downloadable in audio_track['streams']:
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
												      'content_profile'],
												  audio_track[
												      'channels'],
												  audio_track[
												      'language'],
												  audio_track['language'],
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
												video_track['content_profile'],
												video_track['size'],
												video_track['res_w'],
												video_track['res_h']))
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
	    #default_audio_lang = data['result']['viewables'][0]['orderedAudioTracks'][0]
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

	    if video_track['res_h'] == 480:
		sorted_aud = [a_track for a_track in sorted_aud if a_track['channels'] == '2.0']
		
	    audio_selected = ['en']
	    if config_dict['audio_language'] is not None:
		audio_selected = config_dict['audio_language']

	    for audio_select in audio_selected:
		for aud_track_sorted in sorted_aud:
		    if aud_track_sorted['language'] == audio_select:
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
		audio_track['downloadables']['content_profile'],
		audio_track['channels'],
		audio_track['language'],
		audio_track['downloadables']['size']))

	if config_dict['subtitle_languages'] is not None:
	    self.logger.debug("SUBTITLE_LANGUAGE_ARGUMENT: {}".format(config_dict['subtitle_languages']))
	    if 'all' in config_dict['subtitle_languages']:
		subtitle_tracks = subtitle_tracks_filtered
	    else:
		subtitle_tracks = [x for x in subtitle_tracks_filtered if
				   x['language'] in config_dict['subtitle_languages']]
	else:
	    subtitle_tracks = None
	if subtitle_tracks:
	    for subtitle in subtitle_tracks:
		self.logger.info("SUBTITLE - Name: {} bcp47: {}".format(subtitle['language'], subtitle['language']))

	#init_data_b64 = data['result']['viewables'][0]['psshb64'][0]
	init_data_b64 = data['result']['video_tracks'][0]['drmHeader']['bytes']
	
	#init_data_b64 = 'AAAANHBzc2gAAAAA7e+LqXnWSs6jyCfc1R0h7QAAABQIARIQAAAAAAUrePMAAAAAAAAAAA=='
	#init_data_b64 = ""

	#cert_data_b64 = data['result']['viewables'][0]['cert']
	cert_data_b64 = 'CAUSwwUKvQIIAxIQ5US6QAvBDzfTtjb4tU/7QxiH8c+TBSKOAjCCAQoCggEBAObzvlu2hZRsapAPx4Aa4GUZj4/GjxgXUtBH4THSkM40x63wQeyVxlEEo1D/T1FkVM/S+tiKbJiIGaT0Yb5LTAHcJEhODB40TXlwPfcxBjJLfOkF3jP6wIlqbb6OPVkDi6KMTZ3EYL6BEFGfD1ag/LDsPxG6EZIn3k4S3ODcej6YSzG4TnGD0szj5m6uj/2azPZsWAlSNBRUejmP6Tiota7g5u6AWZz0MsgCiEvnxRHmTRee+LO6U4dswzF3Odr2XBPD/hIAtp0RX8JlcGazBS0GABMMo2qNfCiSiGdyl2xZJq4fq99LoVfCLNChkn1N2NIYLrStQHa35pgObvhwi7ECAwEAAToQdGVzdC5uZXRmbGl4LmNvbRKAA4TTLzJbDZaKfozb9vDv5qpW5A/DNL9gbnJJi/AIZB3QOW2veGmKT3xaKNQ4NSvo/EyfVlhc4ujd4QPrFgYztGLNrxeyRF0J8XzGOPsvv9Mc9uLHKfiZQuy21KZYWF7HNedJ4qpAe6gqZ6uq7Se7f2JbelzENX8rsTpppKvkgPRIKLspFwv0EJQLPWD1zjew2PjoGEwJYlKbSbHVcUNygplaGmPkUCBThDh7p/5Lx5ff2d/oPpIlFvhqntmfOfumt4i+ZL3fFaObvkjpQFVAajqmfipY0KAtiUYYJAJSbm2DnrqP7+DmO9hmRMm9uJkXC2MxbmeNtJHAHdbgKsqjLHDiqwk1JplFMoC9KNMp2pUNdX9TkcrtJoEDqIn3zX9p+itdt3a9mVFc7/ZL4xpraYdQvOwP5LmXj9galK3s+eQJ7bkX6cCi+2X+iBmCMx4R0XJ3/1gxiM5LiStibCnfInub1nNgJDojxFA3jH/IuUcblEf/5Y0s1SzokBnR8V0KbA=='
	#cert_data_b64 = cert_data_b64.decode("utf-8")
	#cert_data_b64 = 'Cr0CCAMSEOVEukALwQ8307Y2+LVP+0MYh/HPkwUijgIwggEKAoIBAQDm875btoWUbGqQD8eAGuBlGY+Pxo8YF1LQR+Ex0pDONMet8EHslcZRBKNQ/09RZFTP0vrYimyYiBmk9GG+S0wB3CRITgweNE15cD33MQYyS3zpBd4z+sCJam2+jj1ZA4uijE2dxGC+gRBRnw9WoPyw7D8RuhGSJ95OEtzg3Ho+mEsxuE5xg9LM4+Zuro/9msz2bFgJUjQUVHo5j+k4qLWu4ObugFmc9DLIAohL58UR5k0XnvizulOHbMMxdzna9lwTw/4SALadEV/CZXBmswUtBgATDKNqjXwokohncpdsWSauH6vfS6FXwizQoZJ9TdjSGC60rUB2t+aYDm74cIuxAgMBAAE6EHRlc3QubmV0ZmxpeC5jb20SgAOE0y8yWw2Win6M2/bw7+aqVuQPwzS/YG5ySYvwCGQd0Dltr3hpik98WijUODUr6PxMn1ZYXOLo3eED6xYGM7Riza8XskRdCfF8xjj7L7/THPbixyn4mULsttSmWFhexzXnSeKqQHuoKmerqu0nu39iW3pcxDV/K7E6aaSr5ID0SCi7KRcL9BCUCz1g9c43sNj46BhMCWJSm0mx1XFDcoKZWhpj5FAgU4Q4e6f+S8eX39nf6D6SJRb4ap7Znzn7preIvmS93xWjm75I6UBVQGo6pn4qWNCgLYlGGCQCUm5tg566j+/g5jvYZkTJvbiZFwtjMW5njbSRwB3W4CrKoyxw4qsJNSaZRTKAvSjTKdqVDXV/U5HK7SaBA6iJ981/aforXbd2vZlRXO/2S+Maa2mHULzsD+S5l4/YGpSt7PnkCe25F+nAovtl/ogZgjMeEdFyd/9YMYjOS4krYmwp3yJ7m9ZzYCQ6I8RQN4x/yLlHG5RH/+WNLNUs6JAZ0fFdCmw='
	#cert_data_b64 = ''

	"""
	self.logger.debug(video_track['urls'][0]['url'])
	self.logger.debug(audio_track['downloadables']['urls'][0]['url'])
	self.logger.debug(list(subtitle['ttDownloadables']['simplesdh']['downloadUrls'].values())[0])
	"""
	
	#iter(video_track['urls'].values())
	#next(iter(video_track['urls'][0]['url'])),

	wvdl_vt = VideoTrack(True, video_track['size'], 0, video_track['urls'][0]['url'],
			     video_track['content_profile'], video_track['bitrate'],
			     video_track['res_w'], video_track['res_h'])

	wvdl_ats = []
	audio_languages = []


	#iter(audio_track['downloadables']['urls'].values())),
	#next(iter(audio_track['downloadables']['urls'][0]['url'])),

	

	for id, audio_track in enumerate(audio_tracks):
	    audio_languages.append(audio_track['language'])
	    wvdl_ats.append(
		AudioTrack(False, audio_track['downloadables']['size'], id, audio_track['downloadables']['urls'][0]['url'],
			   audio_track['downloadables']['content_profile'], audio_track['downloadables']['bitrate'], audio_track['language'])
	    )

	wvdl_sts = []
	use_captions = { 'it': True }
	if subtitle_tracks:
	    for track in subtitle_tracks:
		use_captions.update({track['language']: True})
	    for track in subtitle_tracks:
		if track['language'] == 'it' and track['trackType'] == "SUBTITLES" and  not track['isForcedNarrative']:
		    use_captions.update({track['language']:False})
	    for i, subtitle in enumerate(subtitle_tracks):
		if 'it' in audio_languages:
		    if subtitle['isForcedNarrative'] and subtitle['language'] == 'it' and (subtitle['trackType'] == "SUBTITLES" or use_captions[subtitle['language']] == True):
			wvdl_sts.append(
			    SubtitleTrack(i, 'Forced', subtitle['language'], True, next(iter(list(subtitle['downloadables'][0]['urls'].values()))),
					'srt')
			)
		    elif not subtitle['isForcedNarrative'] and (subtitle['trackType'] == "SUBTITLES" or use_captions[subtitle['labguage']] == True):
			wvdl_sts.append(
			    SubtitleTrack(i, subtitle['language'], subtitle['language'], False, next(iter(list(subtitle['downloadables'][0]['urls'].values()))),
					'srt')
			)
		else:
		    if not subtitle['isForcedNarrative'] and subtitle['language'] == 'it' and (subtitle['trackType'] == "SUBTITLES" or use_captions[subtitle['language']] == True):
			wvdl_sts.append(
			    SubtitleTrack(i, subtitle['language'], subtitle['language'], True, next(iter(list(subtitle['downloadables'][0]['urls'].values()))),
					'srt')
			)
		    elif not subtitle['isForcedNarrative'] and (subtitle['trackType'] == "SUBTITLES" or use_captions[subtitle['language']] == True):
			wvdl_sts.append(
			    SubtitleTrack(i, subtitle['language'], subtitle['language'], False, next(iter(list(subtitle['ttDownloadables']['simplesdh']['downloadUrls'].values())[0])),
					'srt')
			)

			#SubtitleTrack(i, subtitle['language'], subtitle['language'], False, next(iter(subtitle['downloadables'][0]['urls'].values())),
			#(subtitle['ttDownloadables']['simplesdh']['downloadUrls'].values()[0])
	
	return True, [wvdl_vt, wvdl_ats, wvdl_sts, init_data_b64, cert_data_b64]
    #, cert_data_b64


    def get_license(self, challenge, session_id):
	id = int(time.time() * 10000)
	self.logger.info("doing license request")
	#self.logger.debug(challenge)
	#.decode('latin-1'),
	#'challengeBase64': base64.b64encode(challenge).decode('utf-8'),
	#challenge = "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"
	self.logger.debug("challenge - {}".format(base64.b64encode(challenge)))
	license_request_data = {
	    #'method': 'license',
	    #'licenseType': 'STANDARD',
	    #'clientVersion': '4.0004.899.011',
	    #'uiVersion': 'akira',
	    #'languages': ['en-US'],
	    #'playbackContextId': self.playbackContextId,
	    #'drmContextIds': [self.drmContextId],
	    #'challenges': [{
	    #    'dataBase64': base64.b64encode(challenge).decode('utf-8'),
	    #    'sessionId': "14673889385265"
	    'version': 2,
	    'url': data1['result']['links']['license']['href'],
	    'id': id,
	    'esn': 'NFCDIE-02-DMT4C1VHTF81YTJY8LXRA4GF9J07H1',
	    'languages': ['en-US'],
	    'uiVersion': 'shakti-v25d2fa21',
	    'clientVersion': '6.0011.511.011',
	    'params': [{
		'sessionId': session_id,
		'clientTime': int(id / 10000),
		'challengeBase64': base64.b64encode(challenge).decode('utf-8'),
		'xid': int(id + 1610)
	    }],
            #self.client_config.config['esn']
	    #'clientTime': int(time.time()),
	    #'clientTime': int(id / 10000),
	    #'sessionId': '14673889385265',
	    #'clientTime': int(id / 10000),
	    #'xid': int((int(time.time()) + 0.1612) * 1000)
	    'echo': 'sessionId'
	}
	#license_request_data = str(license_request_data)
	request_data = self.__generate_msl_request_data_lic(license_request_data)
	
	
	resp = self.session.post(nf_cfg.LICENSE_ENDPOINT, request_data, proxies=self.client_config.get_proxies())
	
	"""
	try:
	    # If is valid json the request for the licnese failed
	    resp.json()
	    self.logger.debug('Error getting license: '+resp.text)
	    exit(1)
	except ValueError:
	    # json() failed so we have a chunked json response
	    resp = self.__parse_chunked_msl_response(resp.text)
	    data = self.__decrypt_payload_chunk(resp['payloads'])
	    self.logger.debug(data)
	    #if data['success'] is True:
	    if 'licenseResponseBase64' in data[0]:
		#return data['result']['licenses'][0]['data']
		#return response['result'][0]['licenseResponseBase64']
		return data[0]['licenseResponseBase64']
	    else:
		self.logger.debug('Error getting license: ' + json.dumps(data))
		exit(1)
	"""
	# json() failed so we have a chunked json response
	resp = self.__parse_chunked_msl_response(resp.text)
	data = self.__decrypt_payload_chunk(resp['payloads'])
	self.logger.debug(data)
	
	fobj = open("license.json", "w") 
	playlist = str(data)
	fobj.write(playlist)
	fobj.close()
	
	return data['result'][0]['licenseResponseBase64']
	
	#if data['success'] is True:
	#data[0]
	#if 'licenseResponseBase64' in data:
		#return data['result']['licenses'][0]['data']
		#return response['result'][0]['licenseResponseBase64']
		#return data['links']['releaseLicense']['href']
	 #       return data['licenseResponseBase64']


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
	    data = base64.standard_b64decode(data)
	    #if plaintext['compressionalgo'] == 'GZIP':
	    #    data = zlib.decompress(base64.standard_b64decode(data), 16 + zlib.MAX_WBITS)
	    #else:
	    #    data = base64.standard_b64decode(data)

	    decrypted_payload += data.decode('utf-8')
	#decrypted_payload = json.loads(decrypted_payload)[1]['payload']['data']
	#decrypted_payload = base64.standard_b64decode(decrypted_payload)
	#return json.loads(decrypted_payload)
	decrypted_payload = json.loads(decrypted_payload)
	return decrypted_payload

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
	#serialized_data = json.dumps(data)
	#serialized_data = serialized_data.replace('"', '\\"')
	#serialized_data = '[{},{"headers":{},"path":"/cbp/cadmium-13","payload":{"data":"' + serialized_data + '"},"query":""}]\n'
	#compressed_data = self.__compress_data(serialized_data)
	
	
	data1 = json.dumps(data)
	print(data1)
	data1 = data1.encode('utf-8')
	
	# Create FIRST Payload Chunks
	first_payload = {
	    "messageid": self.current_message_id,
	    #"data": compressed_data.decode('utf-8'),
	    #"compressionalgo": "GZIP",
	    "data": (base64.standard_b64encode(data1)).decode('utf-8'),
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
	
	
    def __generate_msl_request_data_lic(self, data):
	header_encryption_envelope = self.__encrypt(self.__generate_msl_header())
	header = {
	    'headerdata': base64.standard_b64encode(header_encryption_envelope.encode('utf-8')).decode('utf-8'),
	    'signature': self.__sign(header_encryption_envelope).decode('utf-8'),
	    'mastertoken': self.mastertoken,
	}
	# Serialize the given Data
	#serialized_data = json.dumps(data)
	#serialized_data = serialized_data.replace('"', '\\"')
	#serialized_data = '[{},{"headers":{},"path":"/cbp/cadmium-13","payload":{"data":"' + serialized_data + '"},"query":""}]\n'
	#compressed_data = self.__compress_data(serialized_data)
	
	
	print(data)
	#print('\n')
	
	#data1 = json.dumps(data)
	#print(data1)
	#data1 = data1.encode('utf-8')
	
	
	
	# Create FIRST Payload Chunks
	first_payload = {
	    "messageid": self.current_message_id,
	    #"data": compressed_data.decode('utf-8'),
	    #"compressionalgo": "GZIP",
	    #"data": (base64.standard_b64encode(data1)).decode('utf-8'),
	    "data": base64.standard_b64encode(json.dumps(data).encode('utf-8')).decode('utf-8'),
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
		'languages': ["en-US"]
		#'languages': ["en-US"],
		#'compressionalgos': [],
		#'encoderformats' : ['JSON'],
	    },
	    'recipient': 'Netflix',
	    'renewable': True,
	    'messageid': self.current_message_id,
	    'timestamp': time.time()
	}

	# Add compression algo if not empty
	#if compressionalgo is not "":
	#    header_data['capabilities']['compressionalgos'].append(compressionalgo)

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

