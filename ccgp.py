import requests
import os
from bs4 import BeautifulSoup
from bid import BidInfo, BidEntry
import sys
import urllib
import datetime
from enum import Enum

ccgp_search_url = "http://search.ccgp.gov.cn/bxsearch"
chrome_headers = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/64.0.3282.119 Safari/537.36"}


def fetch_ccgp_bid_info(keyword, pages, filename, **kwargs):
    """Fetch and store bidding information."""

    bid = BidInfo()
    if os.path.isfile(filename):
        bid.load(filename)
    directory = os.path.splitext(filename)[0]
    if not os.path.exists(directory):
        os.makedirs(directory)

    if bid.next_page > 1:
        print("Already fetched {} pages.".format(bid.next_page - 1))
        print("Begin fetching from page {}.\n".format(bid.next_page))

    begin_page = bid.next_page
    for pageno in range(begin_page, begin_page + pages):
        sys.stderr.write("Page {}:\n".format(pageno))
        search_page = fetch_search_page(keyword, pageno, **kwargs)
        bid_list = parse_search_page(search_page)

        fetch_and_store_bids(bid_list, directory)

        bid.extend_page(bid_list)
        sys.stderr.write("Fetched {} docs at page {}. ".format(len(bid_list), pageno))
        sys.stderr.write("Total bids: {}.\n".format(
            len(bid.entries)))

        # Save data after every parsing every pageno
        bid.save(filename)


class BidType(Enum):
    """Bidding type supported by ccgp."""

    ALL = 0,
    CALL_FOR_BIDDING = 1,
    SUCCESSFUL_BIDDING = 7,
    DEAL = 11


def bid_type_to_string(bid_type):
    """Return string representation of bidding type."""

    map = {BidType.ALL: '0',
           BidType.CALL_FOR_BIDDING: '1',
           BidType.SUCCESSFUL_BIDDING: '7',
           BidType.DEAL: '11'}

    return map[bid_type]


def fetch_search_page(keyword, pageno, **kwargs):
    """Fetch and return one page of search result."""

    date_fmt = '%Y:%m:%d'
    today = datetime.date.today()
    week_before = today - datetime.timedelta(weeks=1)

    payload = {
        "searchtype": "1",
        "page_index": str(pageno),
        "bidSort": "0",
        "buyerName": "",
        "projectId": "",
        "pinMu": "0",
        "bidType": "0",
        "dbselect": "bidx",
        "kw": keyword,
        "start_time": today.strftime(date_fmt),
        "end_time": week_before.strftime(date_fmt),
        "timeType": "6",
        "displayZone": "",
        "zoneId": "",
        "pppStatus": "0",
        "agentName": "",
    }

    if 'type' in kwargs:
        payload['bidType'] = bid_type_to_string(kwargs['type'])

    if 'start' in kwargs:
        start = datetime.datetime.strptime(kwargs['start'], '%Y-%m-%d')
        payload['start_time'] = start.strftime(date_fmt)

    if 'end' in kwargs:
        end = datetime.datetime.strptime(kwargs['end'], '%Y-%m-%d')
        payload['end_time'] = end.strftime(date_fmt)

    return http_get_html(ccgp_search_url, payload=payload)


def fetch_bid_page(link):
    """Fetch bidding announcement web page."""

    return http_get_html(link)


def parse_search_page(search_doc):
    """Parse search result page. Return a list of entries found."""

    soup = BeautifulSoup(search_doc, "html.parser")
    ul = soup.find("ul", class_="vT-srch-result-list-bid")
    li = ul.find("li")
    new_list = []
    while li:
        entry = parse_html_li_tag(li)
        new_list.append(entry)
        li = li.find_next("li")
        print("{}|{}".format(entry.link, entry.desc))

    return new_list


def parse_html_li_tag(li):
    """Parse a \"li\" tag for bidding description, url, and buyer."""

    entry = BidEntry()
    a = li.find("a")
    if a:
        entry.desc = a.text.strip()
        entry.link = a.get("href")

    span = li.find("span")
    if span:
        text = span.text.strip().split("|")
        entry.date = text[0].strip()
        entry.buyer = text[1].strip().replace("采购人：", "")

    return entry


def http_get_html(link, payload=None):
    """Fetch a html web page. Retry three times when timeout."""

    for i in range(3):
        try:
            response = requests.get(link, params=payload,
                                    headers=chrome_headers, timeout=15)
            response.encoding = 'utf-8'
            return response.text
        except Exception:
            print("Timeout. Retry {}".format(link))
            continue

    return None


def fetch_and_store_bids(bid_list, directory):
    """Fetch and store html web pages of a list of bidding information"""

    for bid in bid_list:
        bid_page = fetch_bid_page(bid.link)
        html_path = urllib.parse.urlparse(bid.link).path
        html_name = os.path.basename(html_path)
        file_path = os.path.join(directory, html_name)
        with open(file_path, 'w') as html_file:
            html_file.write(bid_page)
        bid.file_path = file_path
        print('Fetched {}|{}'.format(bid.link, bid.desc))
