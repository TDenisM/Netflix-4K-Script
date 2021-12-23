PROFILES = {
    'h264_main': {
        '480p': [
            'playready-h264bpl30-dash',
            'playready-h264mpl30-dash',
        ],
        '720p': [
            #'playready-h264mpl30-dash',
            'playready-h264mpl31-dash',
            #'playready-h264mpl40-dash',
            #'playready-h264mpl41-dash',
        ],
        '1080p': [
            'playready-h264mpl40-dash',
        ]
    },
	    'h264_high': {
        '480p': [
            'playready-h264bpl30-dash',
            'playready-h264hpl30-dash',
        ],
        '720p': [
            'playready-h264hpl31-dash',
        ],
        '1080p': [
            'playready-h264hpl40-dash',
        ]
    },
    'hevc': {
        '480p': [
            'hevc-main10-L30-dash-cenc',
        ],
        '720p': [
            'hevc-main10-L31-dash-cenc',
        ],
        '1080p': [
            'hevc-main10-L40-dash-cenc',
            'hevc-main10-L41-dash-cenc',
        ],
        '4k': [
            'hevc-main10-L50-dash-cenc-prk',
            'hevc-main10-L51-dash-cenc-prk',
            'hevc-main10-L50-dash-cenc',
            'hevc-main10-L51-dash-cenc',
        ]
    },
    'hdr': {
        '480p': [
            'hevc-hdr-main10-L30-dash-cenc-prk',
            
        ],
        '720p': [
            'hevc-hdr-main10-L31-dash-cenc-prk',
           
        ],
        '1080p': [
            'hevc-hdr-main10-L40-dash-cenc-prk',
           
        ],
        '4k': [
            'hevc-hdr-main10-L50-dash-cenc-prk',
            
        ]
    },
    'audio': [
        # 'heaac-2-dash',
        'ddplus-2.0-dash',
        'ddplus-5.1hq-dash',
        'ddplus-atmos-dash',
        'dd-5.1-dash',
    ],
    'subs': [
        #'dfxp-ls-sdh',
        'simplesdh',
        #'nflx-cmisc',
        #'webvtt-lssdh-ios8',
        #'webvtt-lssdh-ios'
        #'BIF240',
        #'BIF320',
    ]

}

class NetflixProfiles(object):
    def __init__(self, profile, quality):
        self.profile = profile
        self.quality = quality

    def get(self):
            return PROFILES[self.profile]['480p'] + \
                   PROFILES[self.profile]['720p'] + \
                   PROFILES[self.profile]['1080p']

    def get_all(self):
        if self.profile == 'h2614':
            return PROFILES[self.profile]['480p'] + \
                   PROFILES[self.profile]['720p'] + \
                   PROFILES[self.profile]['1080p'] + \
                   PROFILES['audio'] + \
                   PROFILES['subs']
        else:
            return PROFILES[self.profile]['480p'] + \
                   PROFILES[self.profile]['720p'] + \
                   PROFILES[self.profile]['1080p'] + \
                   PROFILES['audio'] + \
                   PROFILES['subs']

    def set_quality(self, quality):
        self.quality = quality

    def set_profile(self, profile):
        self.profile = profile
