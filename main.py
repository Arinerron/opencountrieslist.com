#!/usr/bin/env python3

import requests
import time
import os
import pathlib
import re
import sys
import logging
import colorlog
import html.parser
import io
import json
import hashlib
import datetime
import sqlite3

import yaml
import tweepy

import sitemap

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('countryscrape.log')
sh = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s[%(filename)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
fh.setFormatter(formatter)
sh.setFormatter(colorlog.ColoredFormatter('%(log_color)s[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%a, %d %b %Y %H:%M:%S'))
logger.addHandler(fh)
logger.addHandler(sh)

######

TWEET_MSGS = list()
CONFIG = dict()

try:
    with open('config.yml', 'r') as f:
        CONFIG = yaml.safe_load(f.read())
except FileNotFoundError:
    pass

######


COUNTRIES = {k.lower(): v.upper() for k, v in {'Afghanistan': 'AF', 'Albania': 'AL', 'Algeria': 'DZ', 'American Samoa': 'AS', 'Andorra': 'AD', 'Angola': 'AO', 'Anguilla': 'AI', 'Antarctica': 'AQ', 'Antigua and Barbuda': 'AG', 'Argentina': 'AR', 'Armenia': 'AM', 'Aruba': 'AW', 'Australia': 'AU', 'Austria': 'AT', 'Azerbaijan': 'AZ', 'Bahamas': 'BS', 'Bahrain': 'BH', 'Bangladesh': 'BD', 'Barbados': 'BB', 'Belarus': 'BY', 'Belgium': 'BE', 'Belize': 'BZ', 'Benin': 'BJ', 'Bermuda': 'BM', 'Bhutan': 'BT', 'Bolivia, Plurinational State of': 'BO', 'Bolivia': 'BO', 'Bosnia and Herzegovina': 'BA', 'Botswana': 'BW', 'Bouvet Island': 'BV', 'Brazil': 'BR', 'British Indian Ocean Territory': 'IO', 'Brunei Darussalam': 'BN', 'Brunei': 'BN', 'Bulgaria': 'BG', 'Burkina Faso': 'BF', 'Burundi': 'BI', 'Cambodia': 'KH', 'Cameroon': 'CM', 'Canada': 'CA', 'Cape Verde': 'CV', 'Cayman Islands': 'KY', 'Central African Republic': 'CF', 'Chad': 'TD', 'Chile': 'CL', 'China': 'CN', 'Christmas Island': 'CX', 'Cocos (Keeling) Islands': 'CC', 'Colombia': 'CO', 'Comoros': 'KM', 'Congo': 'CG', 'Congo, the Democratic Republic of the': 'CD', 'Cook Islands': 'CK', 'Costa Rica': 'CR', "Côte d'Ivoire": 'CI', 'Ivory Coast': 'CI', 'Croatia': 'HR', 'Cuba': 'CU', 'Cyprus': 'CY', 'Czech Republic': 'CZ', 'Denmark': 'DK', 'Djibouti': 'DJ', 'Dominica': 'DM', 'Dominican Republic': 'DO', 'Ecuador': 'EC', 'Egypt': 'EG', 'El Salvador': 'SV', 'Equatorial Guinea': 'GQ', 'Eritrea': 'ER', 'Estonia': 'EE', 'Ethiopia': 'ET', 'Falkland Islands (Malvinas)': 'FK', 'Faroe Islands': 'FO', 'Fiji': 'FJ', 'Finland': 'FI', 'France': 'FR', 'French Guiana': 'GF', 'French Polynesia': 'PF', 'French Southern Territories': 'TF', 'Gabon': 'GA', 'Gambia': 'GM', 'Georgia': 'GE', 'Germany': 'DE', 'Ghana': 'GH', 'Gibraltar': 'GI', 'Greece': 'GR', 'Greenland': 'GL', 'Grenada': 'GD', 'Guadeloupe': 'GP', 'Guam': 'GU', 'Guatemala': 'GT', 'Guernsey': 'GG', 'Guinea': 'GN', 'Guinea-Bissau': 'GW', 'Guyana': 'GY', 'Haiti': 'HT', 'Heard Island and McDonald Islands': 'HM', 'Holy See (Vatican City State)': 'VA', 'Honduras': 'HN', 'Hong Kong': 'HK', 'Hungary': 'HU', 'Iceland': 'IS', 'India': 'IN', 'Indonesia': 'ID', 'Iran, Islamic Republic of': 'IR', 'Iraq': 'IQ', 'Ireland': 'IE', 'Isle of Man': 'IM', 'Israel': 'IL', 'Italy': 'IT', 'Jamaica': 'JM', 'Japan': 'JP', 'Jersey': 'JE', 'Jordan': 'JO', 'Kazakhstan': 'KZ', 'Kenya': 'KE', 'Kiribati': 'KI', "Korea, Democratic People's Republic of": 'KP', 'Korea, Republic of': 'KR', 'South Korea': 'KR', 'Kuwait': 'KW', 'Kyrgyzstan': 'KG', "Lao People's Democratic Republic": 'LA', 'Latvia': 'LV', 'Lebanon': 'LB', 'Lesotho': 'LS', 'Liberia': 'LR', 'Libyan Arab Jamahiriya': 'LY', 'Libya': 'LY', 'Liechtenstein': 'LI', 'Lithuania': 'LT', 'Luxembourg': 'LU', 'Macao': 'MO', 'Macedonia, the former Yugoslav Republic of': 'MK', 'Madagascar': 'MG', 'Malawi': 'MW', 'Malaysia': 'MY', 'Maldives': 'MV', 'Mali': 'ML', 'Malta': 'MT', 'Marshall Islands': 'MH', 'Martinique': 'MQ', 'Mauritania': 'MR', 'Mauritius': 'MU', 'Mayotte': 'YT', 'Mexico': 'MX', 'Micronesia, Federated States of': 'FM', 'Moldova, Republic of': 'MD', 'Monaco': 'MC', 'Mongolia': 'MN', 'Montenegro': 'ME', 'Montserrat': 'MS', 'Morocco': 'MA', 'Mozambique': 'MZ', 'Myanmar': 'MM', 'Burma': 'MM', 'Namibia': 'NA', 'Nauru': 'NR', 'Nepal': 'NP', 'Netherlands': 'NL', 'Netherlands Antilles': 'AN', 'New Caledonia': 'NC', 'New Zealand': 'NZ', 'Nicaragua': 'NI', 'Niger': 'NE', 'Nigeria': 'NG', 'Niue': 'NU', 'Norfolk Island': 'NF', 'Northern Mariana Islands': 'MP', 'Norway': 'NO', 'Oman': 'OM', 'Pakistan': 'PK', 'Palau': 'PW', 'Palestinian Territory, Occupied': 'PS', 'Panama': 'PA', 'Papua New Guinea': 'PG', 'Paraguay': 'PY', 'Peru': 'PE', 'Philippines': 'PH', 'Pitcairn': 'PN', 'Poland': 'PL', 'Portugal': 'PT', 'Puerto Rico': 'PR', 'Qatar': 'QA', 'Réunion': 'RE', 'Romania': 'RO', 'Russian Federation': 'RU', 'Russia': 'RU', 'Rwanda': 'RW', 'Saint Helena, Ascension and Tristan da Cunha': 'SH', 'Saint Kitts and Nevis': 'KN', 'Saint Lucia': 'LC', 'Saint Pierre and Miquelon': 'PM', 'Saint Vincent and the Grenadines': 'VC', 'Saint Vincent & the Grenadines': 'VC', 'St. Vincent and the Grenadines': 'VC', 'Samoa': 'WS', 'San Marino': 'SM', 'Sao Tome and Principe': 'ST', 'Saudi Arabia': 'SA', 'Senegal': 'SN', 'Serbia': 'RS', 'Seychelles': 'SC', 'Sierra Leone': 'SL', 'Singapore': 'SG', 'Slovakia': 'SK', 'Slovenia': 'SI', 'Solomon Islands': 'SB', 'Somalia': 'SO', 'South Africa': 'ZA', 'South Georgia and the South Sandwich Islands': 'GS', 'South Sudan': 'SS', 'Spain': 'ES', 'Sri Lanka': 'LK', 'Sudan': 'SD', 'Suriname': 'SR', 'Svalbard and Jan Mayen': 'SJ', 'Swaziland': 'SZ', 'Sweden': 'SE', 'Switzerland': 'CH', 'Syrian Arab Republic': 'SY', 'Taiwan, Province of China': 'TW', 'Taiwan': 'TW', 'Tajikistan': 'TJ', 'Tanzania, United Republic of': 'TZ', 'Thailand': 'TH', 'Timor-Leste': 'TL', 'Togo': 'TG', 'Tokelau': 'TK', 'Tonga': 'TO', 'Trinidad and Tobago': 'TT', 'Tunisia': 'TN', 'Turkey': 'TR', 'Turkmenistan': 'TM', 'Turks and Caicos Islands': 'TC', 'Tuvalu': 'TV', 'Uganda': 'UG', 'Ukraine': 'UA', 'United Arab Emirates': 'AE', 'United Kingdom': 'GB', 'United States': 'US', 'United States Minor Outlying Islands': 'UM', 'Uruguay': 'UY', 'Uzbekistan': 'UZ', 'Vanuatu': 'VU', 'Venezuela, Bolivarian Republic of': 'VE', 'Venezuela': 'VE', 'Viet Nam': 'VN', 'Vietnam': 'VN', 'Virgin Islands, British': 'VG', 'Virgin Islands, U.S.': 'VI', 'Wallis and Futuna': 'WF', 'Western Sahara': 'EH', 'Yemen': 'YE', 'Zambia': 'ZM', 'Zimbabwe': 'ZW'}.items()}

conns = dict()

_REG_DB = 'history.db'
CURRENT_DB = _REG_DB

# get a cursor
def database(use_file: str=None, read_only: bool=False):
    global conns, CURRENT_DB
    _old_current_db = CURRENT_DB
    if use_file == None:
        use_file = CURRENT_DB
    else:
        CURRENT_DB = use_file

    args = {}
    if read_only:
        args['uri'] = True

    # create the database if not exist
    if not conns.get(use_file):
        conns[use_file] = sqlite3.connect(use_file, detect_types=sqlite3.PARSE_DECLTYPES, **args)
        if not read_only:
            # none of this would be able to run if it was readonly anyway
            _init_database(conns[use_file])

    CURRENT_DB = _old_current_db
    return conns[use_file].cursor()


def commit() -> None:
    global conns
    return conns[CURRENT_DB].commit()


def _init_database(conn) -> None:
    c = conn.cursor()
    c.execute(
        'CREATE TABLE IF NOT EXISTS `countries` ('
            '`id` INT AUTO_INCREMENT,'
            '`unixts` INT NOT NULL,'
            '`abbreviation` VARCHAR(10) NOT NULL,'
            '`name` VARCHAR(400) NOT NULL,'
            '`url` VARCHAR(1000) NOT NULL,'
            '`classification` INT NOT NULL,'
            '`preformatted` VARCHAR(20000),'
            '`test_required` INT NOT NULL,'
            '`quarantine_required` INT NOT NULL,'
            '`last_changed` INT,'
            #'KEY `id` (`id`) USING BTREE,'
            'PRIMARY KEY (`id`)'
        ');'
    )
    
    commit()
    c.close()


class MLStripper(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = io.StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


CLASSIFICATION_SAME = (
    (0, 1), # unknowns
    (2, 3, 4), # not opens
    (5,) # open
)

CLASSIFICATION_TEXT = {
    2: 'is no longer open to U.S. travelers',
    3: 'is no longer open to U.S. travelers',
    4: 'is now only open to U.S. travelers who enter for specific purposes (school, etc)',
    5: 'is now open to U.S. travelers'
}

QUARANTINE_REQUIRED_TEXT = {
    1: 'now requires U.S. travelers to quarantine upon arrival',
    2: 'no longer requires U.S. travelers to quarantine upon arrival'
}

TEST_REQUIRED_TEXT = {
    1: 'now requires U.S. travelers to take a COVID-19 test for entry',
    2: 'no longer requires U.S. travelers to take a COVID-19 test'
}


def generate_change_text(country, recent_row):
    to_classification, to_test_required, to_quarantine_required = (
        country['classification'],
        country['test_required'],
        country['quarantine_required']
    )
    from_classification, from_test_required, from_quarantine_required = recent_row[2:5]
    msgs = list()

    if from_classification != to_classification:
        # check to make sure they aren't "identical classifications"
        changed = False
        for _test in CLASSIFICATION_SAME:
            _results = [from_classification in _test, to_classification in _test]
            if any(_results) and not all(_results):
                changed = True
                break

        if changed and from_classification not in CLASSIFICATION_SAME[0] and to_classification not in CLASSIFICATION_SAME[0]:
            msg = CLASSIFICATION_TEXT.get(to_classification)
            if msg:
                msgs.append(msg)
    
    if to_classification not in CLASSIFICATION_SAME[1]:
        if from_quarantine_required != to_quarantine_required:
            msg = QUARANTINE_REQUIRED_TEXT.get(to_quarantine_required)
            if msg:
                msgs.append(msg)

        if from_test_required != to_test_required:
            msg = TEST_REQUIRED_TEXT.get(to_test_required)
            if msg:
                msgs.append(msg)

    outmsg = country['name'] + ' '
    _msgs = list()
    for msg in msgs:
        if to_classification in CLASSIFICATION_SAME[2] and from_classification in CLASSIFICATION_SAME[1] and msg.startswith('now '):
            msg = 'but ' + msg.lstrip('now ')
        
        _msgs.append(msg)

    # XXX: utter hack
    if len(_msgs) == 1:
        outmsg += _msgs[0]
    elif len(_msgs) == 3:
        dat = '{}, {}, and {}.'.format(*_msgs)
        # Ukraine is now open to U.S. travelers and no longer requires U.S. travelers to quarantine upon arrival, but requires U.S. travelers to take a COVID-19 test for entry
        if ', and but ' in dat:
            dat = '{} and {}, {}.'.format(*_msgs)
        # Ukrainex is now open to U.S. travelers and but requires U.S. travelers to quarantine upon arrival, but requires U.S. travelers to take a COVID-19 test for entry
        if ' and but ' in dat:
            dat = '{}, {} and {}.'.format(*_msgs).replace(' and but ', ' and ')
            if dat.count(' requires U.S. travelers to ') == 2:
                dat = dat.replace('requires U.S. travelers to take a COVID-19 test', 'take a COVID-19 test')
        outmsg += dat
    elif len(_msgs) == 2:
        outmsg += '{}, and {}.'.format(*_msgs)
        outmsg = outmsg.replace('and but ', 'but ')
    elif not _msgs:
        outmsg = ''
    else:
        raise ValueError('Invalid number of msgs: ' + repr(_msgs))

    outmsg = outmsg.replace('now requires U.S. travelers to quarantine upon arrival, and now requires U.S. travelers to take a COVID-19 test for entry', 'now requires U.S. travelers to quarantine upon arrival and take a COVID-19 test for entry')
    
    return outmsg or False


def has_file_expired(filename, expire_after=60*60*5):
    try:
        p = pathlib.Path(filename)
        if not p:
            return True
        elif (time.time() - p.stat().st_mtime) > expire_after:
            return True
        else:
            return False
    except:
        return True


def normalize_country_filename(country_name):
    return country_name.lower().replace('.', '').replace('/', '').replace(' ', '_')


def fetch_url(country_name, url):
    filename = 'data/country_' + normalize_country_filename(country_name) + '_' + hashlib.sha256(url.encode()).hexdigest() + '.html'

    if has_file_expired(filename):
        logger.debug('URL %r for country %r has expired, fetching new data...' % (url, country_name))
        with open(filename, 'w') as f:
            f.write(requests.get(url, allow_redirects=True).text)

    with open(filename, 'r') as f:
        return f.read()


def parse_directory():
    DIR_URL = 'https://travel.state.gov/content/travel/en/traveladvisories/COVID-19-Country-Specific-Information.html'
    FILENAME = 'data/directory.html'
    
    if has_file_expired(FILENAME):
        logger.debug('Directory file has expired; fetching new data...')
        with open(FILENAME, 'w') as f:
            f.write(requests.get(DIR_URL, allow_redirects=True).text)

    with open(FILENAME, 'r') as f:
        contents = f.read()

    countries = dict()

    rstring = r'<\/tr><tr><td><a href="(https?:\/\/(((..|china))\.(usembassy-china\.org\.cn|usembassy\.gov|usconsulate\.gov|usmission\.gov)).*?)">([\w \'\.,]*)<\/a>'
    for match in re.findall(rstring, contents):
        # ('https://mx.usembassy.gov/covid-19-information/', 'mx', 'mx', 'usembassy.gov', 'Mexico')
        url, domain, country_abbreviation, _, _, country_name = match
        country_abbreviation = COUNTRIES.get(country_name.lower(), country_abbreviation)
        filename = 'data/country_' + normalize_country_filename(country_name) + '.html'

        try:
            if has_file_expired(filename):
                logger.debug(f'Country {country_name!r} file {filename!r} has expired, pulling new data...')
                with open(filename, 'w') as f:
                    extra_urls = ['covid-19-information/', 'u-s-citizen-services/covid-19-information/']
                    data = requests.get(url, allow_redirects=True).text
                    for _u in extra_urls:
                        u = ('https://%s/' % domain) + _u
                        if u.rstrip('/') != url.rstrip('/'):
                            data += requests.get(u, allow_redirects=True).text
                    f.write(data)

        except:
            logger.exception(f'Failed to pull info for country {country_name!r} to file {filename!r}. Match: {match!r}')
        
        assert country_name not in countries, f'Country {country_name!r} is already in countries! countries[{country_name!r}] == {countries.get(country_name)!r}'
        countries[country_name] = {
            'name': country_name,
            'abbreviation': country_abbreviation.upper().replace('CHINA', 'CN'),
            'url': url,
            'domain': domain,
            'filename': filename
        }

    return countries


ANSWER_UNKNOWN, ANSWER_READ_MORE, ANSWER_NO, ANSWER_RARELY, ANSWER_SOMETIMES, ANSWER_YES = range(6)
ANSWERS = {
    ANSWER_UNKNOWN: 'Unknown',
    ANSWER_READ_MORE: 'Read More',
    ANSWER_NO: 'No',
    ANSWER_RARELY: 'Rarely',
    ANSWER_SOMETIMES: 'Sometimes',
    ANSWER_YES: 'Yes'
}


def _preformat_answer(country, answer):
    preformatted_answer = re.sub(r'\s+', ' ', strip_tags(answer).strip())
    preformatted_answer = re.sub(r'[^\(\) \w,\.]', '', preformatted_answer)

    if not re.match(r'.*[\.!\?]$', preformatted_answer):
        preformatted_answer += '.'

    # >>> ' '.join(x.capitalize() for x in re.findall(r' ?(.*?[\.!\?])', 'This is an example sentence. Are you able to read this? what about now. ok boomer! ok.sadf.'))
    # 'This is an example sentence. Are you able to read this? What about now. Ok boomer! Ok. Sadf.'

    fmts = {
        'YES': 'Yes',
        'NO': 'No',
        'US': 'U.S.'
    }

    for key, val in fmts.items():
        #preformatted_answer = re.sub('\b' + re.escape(key) + '\b', val, preformatted_answer)
        preformatted_answer = preformatted_answer.replace(key, val)

    preformatted_answer = re.sub('\.+', '.', preformatted_answer)
    preformatted_answer = re.sub('( \.)', '', preformatted_answer).strip()

    if len(preformatted_answer) >= 2:
        preformatted_answer = preformatted_answer[0].upper() + preformatted_answer[1:]

    preformatted_answer = re.sub(r'(https[^\s]*?)(\.\W|"| |\.\s|\.$)', r'the website\2', preformatted_answer, flags=re.IGNORECASE) 
    preformatted_answer = re.sub(r'^' + re.escape(country['name']) + r' (Yes|No)', r'\1', preformatted_answer, flags=re.IGNORECASE)
    preformatted_answer = re.sub(r'(Yes|No) ([\(A-Z])', r'\1. \2', preformatted_answer, flags=re.IGNORECASE)

    preformatted_answer = re.sub(r'Covid19', 'COVID-19', preformatted_answer, flags=re.IGNORECASE)

    return preformatted_answer


def _parse_answer(_answer, url=None):
    answer = re.sub(r'\s+', ' ', re.sub(r'[^\w \n]', '', strip_tags(_answer))).strip().lower()

    if not answer:
        return ANSWER_UNKNOWN

    yes_sometimess = ['not for tourism', 'entry is restricted', 'no tourism', 'subject to strict limitations', 'purpose of travel', 'only under', 'very limited cases', 'special permission', 'but only if they meet other certain criteria', 'limited circumstances', 'restricting non-essential travel', 'only essential travel is permitted']
    yes_always = ['valid visa', 'approved evisa', 'with additional documentation', 'subject to restrictions']

    no_rarelys = ['limited circumstances', 'few exceptions', 'limited exceptions', 'for exceptions', 'special circumstances', 'but currently most us citizens can', 'other us visitors are not allowed']
    no_always = ['nonessential travel', 'residency']

    others_override = {'other us visitors are not allowed': ANSWER_RARELY}
    others_no = ['us visitors are not allowed']
    others_rarely = ['very limited', 'other us visitors are not allowed', 'but currently most us citizens can']
    others_sometimes = ['it depends']
    others_always = ['in most cases', 'the countryyes', 'some us citizens are permitted to enter']

    if re.findall(r'\byes\b', answer) or answer.startswith('yes'):
        for d in yes_sometimess:
            if d in answer:
                return ANSWER_SOMETIMES
        for d in yes_always:
            if d in answer:
                return ANSWER_YES

        return ANSWER_YES
    
    if re.findall(r'\bno\b', answer) or answer.startswith('no'):
        for d in no_rarelys:
            if d in answer:
                return ANSWER_RARELY

        for d in no_always:
            if d in answer:
                return ANSWER_NO

        return ANSWER_NO
    
    for d, k in others_override.items():
        if d in answer:
            return k
    for d in others_no:
        if d in answer:
            return ANSWER_NO
    for d in others_rarely:
        if d in answer:
            return ANSWER_RARELY
    for d in others_sometimes:
        if d in answer:
            return ANSWER_SOMETIMES
    for d in others_always:
        if d in answer:
            return ANSWER_YES

    logger.warning('Unknown response: _answer=%r, answer=%r, url=%r' % (_answer, answer, url))
    return ANSWER_UNKNOWN


TEST_REQUIRED_UNKNOWN, TEST_REQUIRED_YES, TEST_REQUIRED_NO = range(3)

def _parse_covid_test_answer(question, _answer, url=None):
    answer = re.sub(r'\s+', ' ', re.sub(r'[^\w ]', '', strip_tags(_answer))).strip().lower()
    
    if not answer:
        return TEST_REQUIRED_UNKNOWN

    # HACK: [Sun, 07 Mar 2021 14:53:03] WARNING [main.py._parse_covid_test_answer:236] Unknown response for test_required: _answer=' to Mexico.</li>', answer='to mexico', url='https://mx.usembassy.gov/u-s-citizen-services/covid-19-information/'
    answer += re.sub(r'\s+', ' ', re.sub(r'[^\w ]', '', strip_tags(question))).strip().lower()

    yess = ['yes', 'must produce a negative', 'provide a negative', 'requires a negative', 'must undergo', 'requirements for a valid test', 'is required', 'will be tested for covid-19 at their own expense']
    nos = ['no', 'not required']
    unknowns = ['remain closed']

    for d in yess:
        if d in answer:
            return TEST_REQUIRED_YES

    for d in nos:
        if d in answer:
            return TEST_REQUIRED_NO

    for d in unknowns:
        if d in answer:
            return TEST_REQUIRED_UNKNOWN

    logger.warning('Unknown response for test_required: question=%r, _answer=%r, answer=%r, url=%r' % (question, _answer, answer, url))
    return TEST_REQUIRED_UNKNOWN


QUARANTINE_REQUIRED_UNKNOWN, QUARANTINE_REQUIRED_YES, QUARANTINE_REQUIRED_NO = range(3)

def _parse_quarantine_required_answer(_answer, url=None):
    answer = re.sub(r'\s+', ' ', re.sub(r'[^\w ]', '', strip_tags(_answer))).strip().lower()
    
    if not answer:
        return QUARANTINE_REQUIRED_UNKNOWN

    yess = ['yes', 'subject to quarantine', 'the following restrictions apply']
    nos = ['no', 'not required to quarantine', 'travelers with elevated temperatures']
    unknowns = ['possibly']

    for d in yess:
        if d in answer:
            return QUARANTINE_REQUIRED_YES

    for d in nos:
        if d in answer:
            return QUARANTINE_REQUIRED_NO

    for d in unknowns:
        if d in answer:
            return QUARANTINE_REQUIRED_UNKNOWN

    logger.warning('Unknown response for quarantine_required: _answer=%r, answer=%r, url=%r' % (_answer, answer, url))
    return QUARANTINE_REQUIRED_UNKNOWN


def parse_country_contents(country, contents, ignore_urls=None, temp_url=None):
    cur_url = temp_url or country['url']
    if not ignore_urls:
        ignore_urls = [country['url']]

    contents = contents.replace('&nbsp;', ' ').replace('&amp;', '&').replace('\xa0', ' ').strip()
    
    # deal with accordions

    _sep = r'<h4 class="panel-title">\s*(?:' + '|'.join([re.escape(country['name']), re.escape(country['name'].replace('and', '&'))]) + r')\s*<\/h4>'
    matches = re.compile(_sep, re.IGNORECASE | re.MULTILINE | re.DOTALL).split(contents, 1)
    if len(matches) != 1:
        contents = matches[1].split(' class="panel panel-default">', 1)[0]

    # parse the "open" question

    retval = True
    rstring_us_citizens = r'((Are )?U\.S\. citizens permitted to enter\??)(.*?<\/li>)'
    matches = re.findall(rstring_us_citizens, contents, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if not matches:
        rstring_latest = r'(latest|updated).*info.*"(http.*?' + re.escape(country['domain']) + '.*?)"'
        matches = re.findall(rstring_latest, contents, re.IGNORECASE | re.MULTILINE)
        all_urls = [x[1] for x in matches]
        _found = False
        for _, url2 in matches:
            if url2 not in ignore_urls:
                contents = fetch_url(country['name'], url2)
                if parse_country_contents(country, contents, ignore_urls=ignore_urls+all_urls, temp_url=url2):
                    _found = True
                    break
        
        if not _found:
            # didn't find additional URLs or anything interesting :(
            country['classification'] = ANSWER_UNKNOWN
            country['preformatted'] = []
            retval = False
    else:
        statuses = set()
        preformatted = set()

        for _, question, answer in matches:
            answer = answer.split('Is a negative COVID-19 test (PCR and/or serology)', 1)[0]
            statuses.add(_parse_answer(answer, url=cur_url))
            preformatted.add(_preformat_answer(country, answer))

        if len(statuses) >= 2:
            if len(statuses) >= 3:
                statuses = ANSWER_READ_MORE
            elif statuses == {ANSWER_YES, ANSWER_SOMETIMES}:
                statuses = ANSWER_YES
            elif statuses == {ANSWER_SOMETIMES, ANSWER_RARELY}:
                statuses = ANSWER_RARELY
            elif statuses == {ANSWER_NO, ANSWER_RARELY}:
                statuses = ANSWER_NO
            elif statuses == {ANSWER_NO, ANSWER_YES}:
                statuses = ANSWER_READ_MORE
            elif statuses == {ANSWER_RARELY, ANSWER_YES}:
                statuses = ANSWER_READ_MORE
            else:
                logger.warning('Undefined STATUSes combo: %r' % statuses)
                statuses = ANSWER_READ_MORE
        else:
            statuses = list(statuses)[0] # prefer lower #'s because set() is unordered
        
        country['classification'] = statuses
        country['preformatted'] = list(preformatted)

    # parse the updated date

    update_date = None
    matches = set(re.findall(r'<meta property="article:modified_time" content="(.*?)" \/>', contents, re.IGNORECASE))
    for match in matches:
        try:
            # fetch most recent date
            ts = int(datetime.datetime.fromisoformat(match).timestamp())
            if (not update_date) or ts > update_date:
                update_date = ts
        except:
            logger.exception('Failed to parse match %r for country %r at URL %r' % (match, country['name'], country['url']))

    country['last_changed'] = update_date

    # parse the "test required" question

    rstring_covid_test = r'(Is a negative COVID-19 test.*?required for entry\??)(.*?<\/li>)'
    matches = re.findall(rstring_covid_test, contents, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    answers = set()
    
    for question, answer in matches:
        a = _parse_covid_test_answer(question, answer, url=cur_url)
        answers.add(a)

    if TEST_REQUIRED_YES in answers:
        country['test_required'] = TEST_REQUIRED_YES
    elif TEST_REQUIRED_NO in answers:
        country['test_required'] = TEST_REQUIRED_NO
    else:
        country['test_required'] = TEST_REQUIRED_UNKNOWN

    # parse the "quarantine required" column

    rstring_quarantine_required = r'(citizens +required +to +quarantine\??)(.*?<\/li>)'
    matches = re.findall(rstring_quarantine_required, contents.replace('<span data-contrast="none">', '').replace('</span>', '').replace('&nbsp;', ' '), re.IGNORECASE | re.MULTILINE | re.DOTALL)
    answers = set()

    for question, answer in matches:
        answers.add(_parse_quarantine_required_answer(answer, url=cur_url))

    if QUARANTINE_REQUIRED_YES in answers:
        country['quarantine_required'] = QUARANTINE_REQUIRED_YES
    elif QUARANTINE_REQUIRED_NO in answers:
        country['quarantine_required'] = QUARANTINE_REQUIRED_NO
    else:
        country['quarantine_required'] = QUARANTINE_REQUIRED_UNKNOWN


    return retval


def handle_change(country, recent_row):
    outmsg = generate_change_text(country, recent_row)
    if outmsg:
        # generate tweet
        _tweet_outmsg = outmsg.strip().rstrip('.') + '.'
        tweet_text = f'{_tweet_outmsg} For more info, see https://opencountrieslist.com/\n#{country["name"].replace(" ", "")} #traveling #travel #travelban'
        if len(tweet_text) > 280:
            logger.warning('Tweet %r is too long for the 280 length limit, skipping...' % tweet_text)
        else:
            TWEET_MSGS.append(tweet_text)


def get_statuses():
    directory = parse_directory()
    for _, country in directory.items():
        with open(country['filename'], 'r') as f:
            contents = f.read()
    
        parse_country_contents(country, contents)
        del country['filename']
        del country['domain']

    # add stuff to db
    for _, country in directory.items():
        c = database()

        c.execute(
            r"SELECT * FROM ("
                r"SELECT 'change', `unixts`, `classification`, `test_required`, `quarantine_required`"
                r" FROM `countries`"
                r" WHERE `name`=? AND (`classification`!=? OR `test_required`!=? OR `quarantine_required`!=?)"
                r" ORDER BY `unixts` DESC"
                r" LIMIT 1"
            r") UNION ALL SELECT * FROM ("
                r"SELECT 'recent', `unixts`, `classification`, `test_required`, `quarantine_required`"
                r" FROM `countries`"
                r" WHERE `name`=?"
                r" ORDER BY `unixts` DESC"
                r" LIMIT 1"
            r")", (country['name'], country['classification'], country['test_required'], country['quarantine_required'], country['name']))

        change_row = None
        recent_row = None
        for i in range(2):
            row = c.fetchone()
            if row:
                # we found the most recent change in status.
                row_type, unixts, old_classification, old_test_required, old_quarantine_required = row
                if row_type == 'change':
                    change_row = row
                elif row_type == 'recent':
                    recent_row = row

        if (change_row and recent_row) and (change_row[2] == recent_row[2] and change_row[3] == recent_row[3] and change_row[4] == recent_row[4]):
            print(country)
            print(change_row)
            print(recent_row)
            # a country just changed status!
            row_type, unixts, old_classification, old_test_required, old_quarantine_required = change_row
            logger.info('Change in status for country %r:\n* classification: %r -> %r\n* test_required: %r -> %r\n* quarantine_required: %r -> %r\n* unixts: %r -> %r' % (country['name'], old_classification, country['classification'], old_test_required, country['test_required'], old_quarantine_required, country['quarantine_required'], unixts, int(time.time())))

            handle_change(country, recent_row)

        if change_row:
            row_type, unixts, old_classification, old_test_required, old_quarantine_required = change_row
            country['last_updated'] = unixts
            country['old_data'] = {
                'classification': old_classification,
                'test_required': old_test_required,
                'quarantine_required': old_quarantine_required
            }
        
        c.execute("INSERT INTO `countries` (`unixts`, `abbreviation`, `name`, `url`, `classification`, `preformatted`, `test_required`, `quarantine_required`, `last_changed`) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            int(time.time()),
            country['abbreviation'],
            country['name'],
            country['url'],
            country['classification'],
            '\n'.join(country['preformatted']),
            country['test_required'],
            country['quarantine_required'], # don't trust this btw
            country['last_changed']))
    commit()

    return list(directory.values())


if __name__ == '__main__':
    OUTPUT_FILENAME = 'web/data.json'
    statuses = get_statuses()
    with open(OUTPUT_FILENAME, 'w') as f:
        f.write(json.dumps({
            'time': int(time.time()),
            '_note': [
                'Hey developer / hacker! You\'re more than welcome to use the data I collected and publish here. I just have a couple requests.',
                'The first is that you don\'t fetch the JSON blob more frequently than like an hour or so. The data only updates every 6 hours anyway, and if you fetch frequently, it\'ll put extra strain I don\'t need on my server.',
                'Also, please contact me at the email address at the bottom of the home page and let me know of your intent to use the data (and purpose, if you are okay with disclosing that). This allows me, among other things, to have contact information to notify you of future potentially-breaking changes to the API. I\'ll even throw in some instructions on how to access and interpret this data! Don\'t worry, I\'m not gonna tell you "no". Otherwise I\'d bother to make this data harder to access :P I intentionally made this a simple, human-readable JSON blob FOR YOU!',
                'Also btw if you\'re using this endpoint to write your own update bot instead of paying for mine, that\'s totally fine. The reason I even bother charging is because I\'m a student and I\'ve always wanted to try making an online store. I care less about the money, although, of course, I can use extra cash for the infra and for school.',
                'Feel free to shoot me an email if you want to chat about this project or other things, and I\'ll give you discord/telegram contact info.'
            ],
            'countries': statuses
        }, separators=(',', ':')))

    sitemap.generate_sitemap()

    if TWEET_MSGS:
        if not all([key in CONFIG for key in [
            'api-key', 'api-secret', 'access-token', 'access-secret']]):
            logger.warning('Skipping %d tweets as mandatory keys are missing from the config file.' % len(TWEET_MSGS))
        else:
            auth = tweepy.OAuthHandler(CONFIG['api-key'], CONFIG['api-secret'])
            auth.set_access_token(CONFIG['access-token'], CONFIG['access-secret'])
            api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
            logger.info('Creating %d tweets...' % len(TWEET_MSGS))
            for msg in TWEET_MSGS:
                api.update_status(msg)
    
