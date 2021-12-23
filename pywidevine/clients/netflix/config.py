from pywidevine.cdm import deviceconfig 


config = {
    #'username': 'georgecorbett683@gmail.com',
    #'password': 'HjyHjyScq1Scq1',


    #'username': 'rita889@mail.com',
    #'password': 'qwertzui',

    'username': 'trkoneplus@gmail.com',
    'password': '132546as',

    #'username': 'bonniegoz@outlook.com',
    #'password': 'ffJ5yc4wvl',
    'msl_storage': 'msl.json',
    'rsa_key': 'rsa.bin',
    #'esn': "NFCDCH-02-DMT46QNHH01MNAHJF9414XFCF9X5YJ",
    #'esn': "NFCDIE-02-DMT4C1VHTF81YTJY8LXRA4GF9J07H1",
    #'esn': "NFCDSF-01-EYVQ7NW9NEVJ43C5LCQM6HV2PLC2PP",
    #'esn': "NFUWA-001-DMT46QNHH01MNAHJF9415XFCF9X5YJ",
    #'esn': 'NFANDROID1-PRV-P-MOTORNEXUS=6-5730-DFA914FBB2E4815708C10A6E82FD67B9166F9528A11C7A0AE410ACF266DF621F',
    #'esn': 'NFANDROID1-PRV-T-L3-XIAOMMIBOX3-4445-F74EE02DFE6739B1007B33F1E4290AA594839FEA6F8711DBFE837F57E1E8F7C8',
    
    #'esn': "NFCDIE-03-F33YQY3J8827C82NE148PK3XV01R2V",
    #'esn_manifest': "NFCDIE-03-F33YQY3J8827C82NE148PK3XV01R2V",
    
    #'esn': 'NFANDROID1-PRV-P-GOOGLPIXEL-4464-6EA8A15D39427309D0A97686A1A315C6A0ABFE46BECD14BB740EC56C65168E72',
    
    #'esn': "NFANDROID1-PRV-P-GOOGLPIXEL-6720-6EA8A15D39427309D0A97686A1A315C6A0ABFE46BECD14BB740EC56C65168E72",    
    
    
    #'esn': 'NFANDROID2-PRV-SHIELDANDROIDTV-NVIDISHIELD=ANDROID=TV',
    
    #'esn': 'NFANDROID-PRV-P-ASUS=ASUS=X00TD-8195-0519ECDF76149E3600596BE929720A91BAB905487A702E5BEEOF727BAFA2AB74E',
    
    #'esn': 'NFANDROID2-PRV-SONYANDROIDTV2019VU-SONY=BRAVIA=VU1-12360-4AA5B5F40AB2A2AA17A38514CF4B2DBE1E9D4D84CD8658D5DCC0430D4E93A05C',    
     'esn': 'NFANDROID2-PRV-SHIELDANDROIDTV-NVIDISHIELD=ANDROID=TV-15895-4AA5B5F40AB2A2AA17A38514CF4B2DBE1E9D4D84CD8658D5DCC0430D4E93A05C',

    #'esn': 'NFANDROID1-PRV-SONYANDROIDTV2017-SONY=BRAVIA=4K=GB',
    #'esn_manifest': "NFANDROID1-PRV-SONYANDROIDTV2017-SONY=BRAVIA=4K=GB",
    
    #'esn': 'NFANDROID2-PRV-FIRETVSTICK2016-AMAZOFTT-6590-7A32FCE57BD8289B07AC2DBF75125D5A082F10F834C43D2D654A0BAC4',
    #'esn_manifest': "NFANDROID2-PRV-FIRETVSTICK2016-AMAZOFTT-6590-7A32FCE57BD8289B07AC2DBF75125D5A082F10F834C43D2D654A0BAC4",

    'wv_keyexchange': True,
    'wv_device': deviceconfig.device_android_generic_2,
    #'wv_device': deviceconfig.device_chromecdm_903,

    #'esn': "NFCDCH-02-DMT46QNHH01MNAHJF9414XFCF9X5YJ",
    'esn_manifest': "NFCDCH-02-DMT46QNHH01MNAHJF9414XFCF9X5YJ",    
    
    'proxies': {
        'us': None
    },
}

#MANIFEST_ENDPOINT = 'http://www.netflix.com/api/msl/NFCDCH-LX/cadmium/manifest'
#LICENSE_ENDPOINT = 'http://www.netflix.com/api/msl/NFCDCH-LX/cadmium/license'

MANIFEST_ENDPOINT = 'https://www.netflix.com/nq/msl_v1/cadmium/pbo_manifests/%5E1.0.0/router'
LICENSE_ENDPOINT = 'https://www.netflix.com/nq/msl_v1/cadmium/pbo_licenses/%5E1.0.0/router'

#manifest_url = https://www.netflix.com/nq/msl_v1/cadmium/pbo_manifests/%5E1.0.0/router
#license_url = https://www.netflix.com/nq/msl_v1/cadmium/pbo_licenses/%5E1.0.0/router

class NetflixConfig(object):

    def __init__(self, viewable_id, profiles, video_track, audio_tracks, subtitle_languages, audio_language, region):
        self.config = config
        self.viewable_id = int(viewable_id)
        self.config['region'] = region
        self.config['profiles'] = profiles
        self.config['video_track'] = video_track
        self.config['audio_tracks'] = audio_tracks
        self.config['subtitle_languages'] = subtitle_languages
        self.config['audio_language'] = audio_language

    def get_login(self):
        return self.config['username'], self.config['password']

    def get_proxies(self):
        if self.config['proxies'] is not None:
            return self.config['proxies'][self.config['region']]
        return None
