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

    rstring = r'<\/tr><tr><td><a href="(https?:\/\/((..|china))\.(usembassy-china\.org\.cn|usembassy\.gov|usconsulate\.gov|usmission\.gov).*?)">([\w \'\.,]*)<\/a>'
    for match in re.findall(rstring, contents):
        # ('https://mx.usembassy.gov/covid-19-information/', 'mx', 'mx', 'usembassy.gov', 'Mexico')
        url, country_abbreviation, _, domain, country_name = match
        filename = 'data/country_' + country_name.lower().replace('.', '').replace('/', '').replace(' ', '_') + '.html'

        try:
            if has_file_expired(filename):
                logger.debug(f'Country {country_name!r} file {filename!r} has expired, pulling new data...')
                with open(filename, 'w') as f:
                    f.write(requests.get(url).text)

        except:
            logger.exception(f'Failed to pull info for country {country_name!r} to file {filename!r}. Match: {match!r}')
        
        assert country_name not in countries, f'Country {country_name!r} is already in countries! countries[{country_name!r}] == {countries.get(country_name)!r}'
        countries[country_name] = {
            'name': country_name,
            'abbreviation': country_abbreviation.upper(),
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


def _parse_answer(_answer):
    answer = re.sub(r'\s+', ' ', re.sub(r'[^\w ]', '', strip_tags(_answer))).strip().lower()

    yes_sometimess = ['not for tourism', 'entry is restricted', 'no tourism', 'subject to strict limitations', 'purpose of travel', 'only under', 'very limited cases', 'special permission', 'but only if they meet other certain criteria', 'limited circumstances']
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
    if answer == '':
        return ANSWER_UNKNOWN

    logger.warning('Unknown response: _answer=%r, answer=%r' % (_answer, answer))
    return ANSWER_UNKNOWN


def parse_country(country):
    with open(country['filename'], 'r') as f:
        contents = f.read()
    
    rstring_us_citizens = r'((Are )?U\.S\. citizens permitted to enter\??)(.*$.*$)'
    matches = re.findall(rstring_us_citizens, contents, re.IGNORECASE | re.MULTILINE)
    if not matches:
        rstring_latest = r'(latest|updated).*info.*"(http.*?' + re.escape(country['domain']) + '.*?)"'
        for _, url2 in re.findall(rstring_latest, contents, re.IGNORECASE | re.MULTILINE):
            # print(url2)
            # TODO: parse additional info URLs
            pass
    else:
        statuses = set()
        preformatted = set()

        for _, question, answer in matches:
            statuses.add(_parse_answer(answer))
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

    return country


def get_statuses():
    directory = parse_directory()
    for _, country in directory.items():
        parse_country(country)
        del country['filename']
        del country['domain']
    return directory


if __name__ == '__main__':
    OUTPUT_FILENAME = 'data.json'
    with open(OUTPUT_FILENAME, 'w') as f:
        f.write(json.dumps(get_statuses(), indent=2))
