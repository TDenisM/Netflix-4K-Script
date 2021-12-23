import argparse
import logging
import sys
import requests
import re
import json

try:
    from http.cookiejar import CookieJar
except ImportError:
    from cookielib import CookieJar

import colorama
from pywidevine.clients.netflix.client import NetflixClient
from pywidevine.clients.netflix.config import NetflixConfig
from pywidevine.clients.netflix.profiles import NetflixProfiles
from pywidevine.downloader.wvdownloader import WvDownloader
from pywidevine.downloader.wvdownloaderconfig import WvDownloaderConfig



parser = argparse.ArgumentParser(
    description="netflix content downloader"
)

parser.add_argument('-t', '--title',
                    help='title id',
                    nargs='+',
                    type=int,
                    required=True)
parser.add_argument('-o', '--outputfile',
                    default='out',
                    nargs='?',
                    help='output filename (no extension)')
parser.add_argument('-q', '--quality',
                    help='video resolution',
                    choices=['480p', '720p', '1080p', '2160p'])
parser.add_argument('-a', '--audiolang',
                    help='audio language',
                    type=lambda x: x.split(','))
parser.add_argument('-p', '--profile',
                    default='h264',
                    #choices=['h264', 'hevc', 'hdr', 'all'],
                    choices=['h264_main', 'h264_high', 'hevc', 'hdr', 'vp9', 'all'],
                    #choices=['h264', 'h264_hpl', 'hevc', 'hdr', 'vp9', 'all'],
                    help='video type to download')
parser.add_argument('-k', '--skip-cleanup', action='store_true', help='skip cleanup step')
parser.add_argument('-m', '--dont-mux',
                    action='store_true',
                    help='move unmuxed tracks instead of muxing')
parser.add_argument('-i', '--info', action='store_true', help='print track information and exit')
parser.add_argument('-d', '--debug', action='store_true', help='print debug statements')
parser.add_argument('-S', '--subs-only', action='store_true', help='download subtitles and exit')
parser.add_argument('-u', '--sub-type', default='srt', choices=['srt', 'ass', 'none'],
                    help='subtitle type (or none)')
parser.add_argument('-s', '--season', type=int, help='lookup and download season from title id')
parser.add_argument('-e',
                    '--episode_start',
                    dest="episode_start",
                    help="Recursively rip season number that provided viewable ID belongs to, starting at the episode provided")
parser.add_argument('--skip', type=int, default=0, help='skip episodes in season mode')
parser.add_argument('--region', default='us', choices=['us', 'uk', 'jp', 'ca', 'se', 'ru'], help='region to proxy')
parser.add_argument('--license',
                    action='store_true',
                    help='do license request and print decryption keys only')

args = parser.parse_args()
DEBUG_LEVELKEY_NUM = 21
logging.addLevelName(DEBUG_LEVELKEY_NUM, "LOGKEY")


def logkey(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    if self.isEnabledFor(DEBUG_LEVELKEY_NUM):
        self._log(DEBUG_LEVELKEY_NUM, message, args, **kws)


logging.Logger.logkey = logkey

logger = logging.getLogger()

if args.license:
    logger.setLevel(21)
else:
    logger.setLevel(logging.INFO)

if args.debug:
    logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

colorama.init()

BUILD = ''
SESSION = requests.Session()


"""
login_pag = SESSION.get("https://www.netflix.com/login").text
authURL = re.search('name="authURL" value="([^"]+)"', login_pag)
print(authURL)
#authURL = re.search(r'authURL\" value\=\"(.*?)\"', login_pag)
authURL = authURL[1]

def login(username, password):
    #
    post_data = {
        'email': username,
        'password': password,
        'rememberMe': 'true',
        'mode': 'login',
        'action': 'loginAction',
        'withFields': 'email,password,rememberMe,nextPage,showPassword',
        'nextPage': '',
        'showPassword': '',
        'authURL': authURL
    }
    
    req = SESSION.post('https://www.netflix.com/login', post_data)
    #match =re.search (r'.*"BUILD_IDENTIFIER":"([a-z0-9]+)"', req.text)
    match = re.search(r'"BUILD_IDENTIFIER":"([a-z0-9]+)"', req.text) #fix by Castle / https://gist.github.com/xor10/8f65c1e66a34386e1131f8c28ff6bf64#gistcomment-2668063
	
    if match is not None:
        return match.group(1)
    else:
        return None
"""


def login(username, password):
        r = SESSION.get('https://www.netflix.com/login', stream=True, allow_redirects=False, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0'})
        loc = None
        while 'Location' in r.headers:
            loc = r.headers['Location']
            r = SESSION.get(loc, stream=True, allow_redirects=False, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0'})

        x = re.search('name="authURL" value="([^"]+)"', r.text)
        if not x:
            return
        authURL = x.group(1)
        post_data = {'userLoginId':username, 
         'password':password, 
         'rememberMe':'true', 
         'mode':'login', 
         'flow':'websiteSignUp', 
         'action':'loginAction', 
         'authURL':authURL, 
         'withFields':'userLoginId,password,rememberMe,nextPage,showPassword', 
         'nextPage':'', 
         'showPassword':''}
        req = SESSION.post(loc, post_data, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.90 Safari/537.36 CrKey/1.17.46278'})
        try:
            req.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(e)
            logger.error(e)
            sys.exit(1)

        match = re.search('"BUILD_IDENTIFIER":"([a-z0-9]+)"', req.text)
        if match is not None:
            return match.group(1)
        else:
            return



"""
def fetch_metadata(movieid):
    #Fetches metadata for a netflix id
    req = SESSION.get('https://www.netflix.com/api/shakti/' + BUILD + '/metadata?movieid=' + movieid)
    return json.loads(req.text)
"""

def parseCookieFile(cookiefile):
    """Parse a cookies.txt file and return a dictionary of key value pairs
    compatible with requests."""

    cookies = {}
    with open (cookiefile, 'r') as fp:
        for line in fp:
            if not re.match(r'^\#', line):
                lineFields = line.strip().split('\t')
                cookies[lineFields[5]] = lineFields[6]
    return cookies



#proxies = {"https": "159.100.246.156:45382"}

def get_build():
        cookies = parseCookieFile('cookies.txt')
        post_data = ''
        #req1 = SESSION.get('https://www.netflix.com', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'}, cookies=cookies, proxies=proxies) 
        #print(req1.text)
        #exit(1)
        req = SESSION.post('https://www.netflix.com/browse', post_data, headers={'User-Agent': 'Gibbon/2018.1.6.3/2018.1.6.3: Netflix/2018.1.6.3 (DEVTYPE=NFANDROID2-PRV-FIRETVSTICK2016; CERTVER=0)'}, cookies=cookies)
        #req = SESSION.get('https://www.netflix.com/browse', headers={'User-Agent': 'Gibbon/2018.1.6.3/2018.1.6.3: Netflix/2018.1.6.3 (DEVTYPE=NFANDROID2-PRV-FIRETVSTICK2016; CERTVER=0)'}, cookies=cookies, proxies=proxies)
        match = re.search(r'"BUILD_IDENTIFIER":"([a-z0-9]+)"', req.text) #fix by Castle / https://gist.github.com/xor10/8f65c1e66a34386e1131f8c28ff6bf64#gistcomment-2668063
        return match.group(1)

def fetch_metadata(movieid):
        global BUILD
        cookies = parseCookieFile('cookies.txt')
        #BUILD = get_build()
        BUILD = 'vafe38bd5'
        print(BUILD)
        #cookies = 'on'
        #if BUILD == '':
        #    BUILD = login(username, password)
        """
        if cookies == 'off':
            req = SESSION.get('https://www.netflix.com/api/shakti/' + BUILD + '/metadata?movieid=' + movieid + '&drmSystem=widevine&isWatchlistEnabled=false&isShortformEnabled=false&isVolatileBillboardsEnabled=false')
        else:
            req = requests.get('https://www.netflix.com/api/shakti/' + BUILD + '/metadata?movieid=' + movieid + '&drmSystem=widevine&isWatchlistEnabled=false&isShortformEnabled=false&isVolatileBillboardsEnabled=false', cookies=cookies)
        """
        req = requests.get('https://www.netflix.com/api/shakti/' + BUILD + '/metadata?movieid=' + movieid + '&drmSystem=widevine&isWatchlistEnabled=false&isShortformEnabled=false&isVolatileBillboardsEnabled=false', cookies=cookies)
        return json.loads(req.text)
        

def fetch_metadata_movie(BUILD, movieid):
        #global BUILD
        #cookies = 'on'
        #if BUILD == '':
        #    BUILD = login(username, password)
        cookies = parseCookieFile('cookies.txt')
        #BUILD = get_build()
        BUILD = 'vafe38bd5'
        print(BUILD)
        """
        if cookies == 'off':
            req = SESSION.get('https://www.netflix.com/api/shakti/' + BUILD + '/metadata?movieid=' + movieid + '&drmSystem=widevine&isWatchlistEnabled=false&isShortformEnabled=false&isVolatileBillboardsEnabled=false')
        else:
            req = requests.get('https://www.netflix.com/api/shakti/' + BUILD + '/metadata?movieid=' + movieid + '&drmSystem=widevine&isWatchlistEnabled=false&isShortformEnabled=false&isVolatileBillboardsEnabled=false', cookies=cookies)
        """
        req = requests.get('https://www.netflix.com/api/shakti/' + BUILD + '/metadata?movieid=' + movieid + '&drmSystem=widevine&isWatchlistEnabled=false&isShortformEnabled=false&isVolatileBillboardsEnabled=false', cookies=cookies)
        return json.loads(req.text)

episodes = []
if args.season:
    nf_cfg = NetflixConfig(0, None, None, [], ['all'], None, args.region)
    username, password = nf_cfg.get_login()
    #BUILD = login(username, password)
    if BUILD is not None:
        info = fetch_metadata(str(args.title[0]))
        serial_title = info['video']['title']
        serial_title = re.sub(r'[/\\:*?"<>|]', '', serial_title)
        for season in info['video']['seasons']:
            if season['seq'] == args.season:
                episode_list = season['episodes']
                #print(len(episode_list))
                if args.episode_start:
                    #episode_list = episode_list[(int(args.episode_start) - 1):]
                    episode_list = [episode_list[(int(args.episode_start) - 1)]]
                    #print(episode_list)
                for episode in episode_list:
                    if episode['seq'] > args.skip:
                        episodes.append((
                            episode['episodeId'],
                            "{}.S{}E{}.{}".format(
                                serial_title.replace(' ', '.').replace('"', '.').replace('"', '.').replace('(', '').replace(')', ''),
                                str(season['seq']).zfill(2),
                                str(episode['seq']).zfill(2),
                                episode['title'].replace(',', '').replace(':', '').replace('?', '').replace("'", '').replace(' ', '.').replace('/', '').replace('"', '.').replace('"', '.').replace('(', '').replace(')', ''))))
else:
    episodes = [(args.title[0], args.outputfile)]

def get_movie_name():
    #nf_cfg = NetflixConfig(0, None, None, [], ['all'], None, args.region)
    #username, password = nf_cfg.get_login()
    #BUILD = ''
    #BUILD = login(username, password)
    #print(BUILD)
    BUILD = globals()['BUILD']
    if BUILD is not None:
        info = fetch_metadata_movie(BUILD, str(args.title[0]))
        serial_title = info['video']['title']
        #serial_title = 'title'
        synopsis = info['video']['synopsis']
        #synopsis = ''
        year = info['video']['year']
        #year = str('2019')
        try:
         boxart = info['video']['boxart'][0]['url']
        except IndexError:
         boxart = ''
        serial_title = re.sub(r'[/\\:*?"<>|]', '', serial_title)
        #print(serial_title)
        logger.info("ripping {} {}".format(serial_title, serial_title.replace('"', '.').replace('"', '.').replace('(', '').replace(')', '')))
        logger.info("boxart {} ".format(boxart))
        logger.info("synopsis {} ".format(synopsis))
        logger.info("year {} ".format(year))
        return str(serial_title.replace('"', '.').replace('"', '.').replace('(', '').replace(')', ''))
    else:
        return str('')

nf_profiles = NetflixProfiles(args.profile, args.quality)


for title, outputfile in episodes:
    if args.season:
        
        if args.profile == 'h264':
                codec_name = 'x264'
        if args.profile == 'h264_main':
                codec_name = 'x264'
        if args.profile == 'h264_high':
                codec_name = 'x264'
        if args.profile == 'hevc':
                codec_name = 'h265'
        if args.profile == 'hdr':
                codec_name = 'hdr'
        if args.profile == 'vp9':
                codec_name = 'VP9'

        if args.profile == 'all':
                codec_name = 'x264'

        group = 'MI'
        logger.info("ripping {}: {}".format(title, outputfile))
        outputfile = outputfile + '.' + str(args.quality) + '.NF.WEB-DL.' + 'AUDIOCODEC' + '.' + codec_name  + '-' +  group
        outputfile1 = outputfile + '.' + str(args.quality) + '.NF.WEB-DL.' + 'AUDIOCODEC' + '.' + codec_name  + '-' +  group
    if not args.season:
        
        if args.profile == 'h264':
                codec_name = 'x264'
        if args.profile == 'h264_main':
                codec_name = 'x264'
        if args.profile == 'h264_high':
                codec_name = 'x264'
        if args.profile == 'hevc':
                codec_name = 'h265'
        if args.profile == 'hdr':
                codec_name = 'hdr'
        if args.profile == 'vp9':
                codec_name = 'VP9'

        if args.profile == 'all':
                codec_name = 'x264'

        group = 'NFT'
        logger.info("ripping {}: {}".format(title, outputfile))
        info = fetch_metadata_movie(BUILD, str(args.title[0]))
        #print(info)
        year = info['video']['year']
        #year = str('2019')
        outputfile = get_movie_name().replace("'", '').replace(' ', '.').replace('"', '.').replace('"', '.').replace('(', '').replace(')', '') + '.'+ str(year) + '.' + str(args.quality) + '.NF.WEB-DL.'+ 'AUDIOCODEC' + '.' + codec_name + '-' +  group
        outputfile1 = get_movie_name().replace("'", '').replace(' ', '.').replace('"', '.').replace('"', '.').replace('(', '').replace(')', '') + '.'+ str(year) + '.' + str(args.quality) + '.NF.WEB-DL.'+ 'AUDIOCODEC' + '.' + codec_name + '-' +  group
    if args.audiolang:
        audiolang = args.audiolang
    else:
        audiolang = None
    if args.quality is not None:
        profiles = nf_profiles.get_all()
    else:
        profiles = nf_profiles.get_all()
    nf_cfg = NetflixConfig(title, profiles, None, [], ['all'], audiolang, args.region)
    nf_client = NetflixClient(nf_cfg)
    """
    if not args.season:
        outputfile = outputfile + '_' + str(args.profile)
        outputfile1 = outputfile + '_' + str(args.profile)
    else:
        outputfile1 = outputfile + '_' + str(args.profile)
        outputfile = outputfile + '_' + str(args.profile)
    """
    wvdownloader_config = WvDownloaderConfig(nf_client,
                                             outputfile,
                                             args.sub_type,
                                             args.info,
                                             args.skip_cleanup,
                                             args.dont_mux,
                                             args.subs_only,
                                             args.license,
                                             args.quality,
                                             args.profile)

    wvdownloader = WvDownloader(wvdownloader_config)
    wvdownloader.run()
