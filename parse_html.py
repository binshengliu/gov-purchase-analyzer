import json
import urllib.parse as urlparse
import re
# from bs4 import BeautifulSoup


def isfloat(x):
    try:
        a = float(x)
    except ValueError:
        return False
    else:
        return True


def isint(x):
    try:
        a = float(x)
        b = int(a)
    except ValueError:
        return False
    else:
        return a == b


def get_bid(url):
    parsed = urlparse.urlparse(url)
    params = urlparse.parse_qs(parsed.query)
    return params['bid'][0]


def starts_with_wan(string):
    return string.startswith('万') or string.startswith('万元') \
        or string.startswith('（万）') or string.startswith('（万元）') \
        or string.startswith('(万元)')


def try_parse_num(string):
        candidate = ''
        pos = 0
        char = string[0]
        while char.isspace() or char == ',' or isfloat(candidate + char):
            if isfloat(candidate + char):
                candidate += char
            pos += 1
            char = string[pos]

        ten_thousand = False
        if starts_with_wan(string[pos:]):
            ten_thousand = True

        if isfloat(candidate):
            num = float(candidate)
            if ten_thousand:
                num *= 10000
            return num

        return -1


def parse_html(filename):
    total = 0
    with open(filename) as html_file:
        html_doc = html_file.read()
        for match in re.finditer('金额：', html_doc):
            start = match.start()
            num = try_parse_num(html_doc[start+3:])
            if num != -1:
                total += num
                print("Found {} in {}".format(num, filename))
    return total


def parse_all_html(metafile):
    total = 0
    processed = 0
    valid = 0
    with open(metafile) as json_file:
        data = json.load(json_file)
        for p in data['urls']:
            url = p[1]
            bid = get_bid(url)
            filename = 'html/' + str(bid) + ".html"
            value = parse_html(filename)
            if value != 0:
                valid += 1
            total += value
            processed += 1

    print("Total: {} in {} of {} files".format(total, valid, processed))

parse_all_html('urls.txt')
