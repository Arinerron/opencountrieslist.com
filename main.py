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

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('countryscrape.log')
sh = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s[%(filename)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
fh.setFormatter(formatter)
sh.setFormatter(colorlog.ColoredFormatter('%(log_color)s[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%a, %d %b %Y %H:%M:%S'))
logger.addHandler(fh)
logger.addHandler(sh)


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


def has_file_expired(filename, expire_after=60*60*24):
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
            f.write(requests.get(url).text)

    with open(filename, 'r') as f:
        return f.read()


def parse_directory():
    DIR_URL = 'https://travel.state.gov/content/travel/en/traveladvisories/COVID-19-Country-Specific-Information.html'
    FILENAME = 'data/directory.html'
    
    if has_file_expired(FILENAME):
        logger.debug('Directory file has expired; fetching new data...')
        with open(FILENAME, 'w') as f:
            f.write(requests.get(DIR_URL).text)

    with open(FILENAME, 'r') as f:
        contents = f.read()

    countries = dict()

    rstring = r'<\/tr><tr><td><a href="(https?:\/\/(((..|china))\.(usembassy-china\.org\.cn|usembassy\.gov|usconsulate\.gov|usmission\.gov)).*?)">([\w \'\.,]*)<\/a>'
    for match in re.findall(rstring, contents):
        # ('https://mx.usembassy.gov/covid-19-information/', 'mx', 'mx', 'usembassy.gov', 'Mexico')
        url, domain, country_abbreviation, _, _, country_name = match
        filename = 'data/country_' + normalize_country_filename(country_name) + '.html'

        try:
            if has_file_expired(filename):
                logger.debug(f'Country {country_name!r} file {filename!r} has expired, pulling new data...')
                with open(filename, 'w') as f:
                    extra_urls = ['covid-19-information/', 'u-s-citizen-services/covid-19-information/']
                    data = requests.get(url).text
                    for _u in extra_urls:
                        u = ('https://%s/' % domain) + _u
                        if u.rstrip('/') != url.rstrip('/'):
                            data += requests.get(u).text
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


def _preformat_answer(answer):
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

    return preformatted_answer


def _parse_answer(_answer, url=None):
    answer = re.sub(r'\s+', ' ', re.sub(r'[^\w \n]', '', strip_tags(_answer))).strip().lower()

    if not answer:
        return ANSWER_UNKNOWN

    yes_sometimess = ['not for tourism', 'entry is restricted', 'no tourism', 'subject to strict limitations', 'purpose of travel', 'only under', 'very limited cases', 'special permission', 'but only if they meet other certain criteria', 'limited circumstances', 'restricting non-essential travel']
    yes_always = ['valid visa', 'approved evisa', 'with additional documentation', 'subject to restrictions']

    no_rarelys = ['limited circumstances', 'few exceptions', 'limited exceptions', 'for exceptions', 'special circumstances']
    no_always = ['nonessential travel', 'residency']

    others_no = ['us visitors are not allowed']
    others_rarely = ['very limited']
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

    yess = ['yes', 'must produce a negative', 'provide a negative', 'requires a negative', 'must undergo', 'requirements for a valid test', 'is required']
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
    nos = ['no', 'not required to quarantine']
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
            statuses.add(_parse_answer(answer, url=cur_url))
            preformatted.add(_preformat_answer(answer))

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

    rstring_quarantine_required = r'(citizens required to quarantine\??)(.*?<\/li>)'
    matches = re.findall(rstring_quarantine_required, contents, re.IGNORECASE | re.MULTILINE | re.DOTALL)
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


def get_statuses():
    directory = parse_directory()
    for _, country in directory.items():
        with open(country['filename'], 'r') as f:
            contents = f.read()
    
        parse_country_contents(country, contents)
        del country['filename']
        del country['domain']
    return list(directory.values())


if __name__ == '__main__':
    OUTPUT_FILENAME = 'web/data.json'
    with open(OUTPUT_FILENAME, 'w') as f:
        f.write(json.dumps({
            'time': int(time.time()),
            'countries': get_statuses()
        }, indent=2))
