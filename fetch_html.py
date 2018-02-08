import json
import urllib.parse as urlparse
import requests


def get_bid(url):
    parsed = urlparse.urlparse(url)
    params = urlparse.parse_qs(parsed.query)
    return params['bid'][0]


def write_html(filename, html_doc):
    with open(filename, 'w') as html_file:
        html_file.write(html_doc)


def fetch_all_html(filename):
    with open(filename) as json_file:
        data = json.load(json_file)
        total = len(data['urls'])
        for (count, p) in enumerate(data['urls']):
            desc = p[0]
            url = p[1]
            bid = get_bid(url)
            r = requests.get(url)
            write_html('html/' + str(bid) + '.html', r.text)
            print("Fetched {} of {}: {}|{}".format(count + 1, total, desc, url))


fetch_all_html('urls.txt')
