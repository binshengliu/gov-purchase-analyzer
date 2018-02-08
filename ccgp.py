import requests
import os
from bs4 import BeautifulSoup
from bid import BidInfo, BidEntry
import sys
import urllib

html_store = "html"
ccgp_search_url = "http://search.ccgp.gov.cn/bxsearch"
chrome_headers = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/64.0.3282.119 Safari/537.36"}


def fetch_ccgp_bid_info(filename, pages):
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
        search_page = fetch_search_page(pageno)
        bid_list = parse_search_page(search_page)

        fetch_and_store_bids(bid_list, directory)

        bid.extend_page(bid_list)
        sys.stderr.write("Fetched {} docs at page {}. ".format(len(bid_list), pageno))
        sys.stderr.write("Total bids: {}.\n".format(
            len(bid.entries)))

        # Save data after every parsing every pageno
        bid.save(filename)


def fetch_search_page(pageno):
    payload = {
        "searchtype": "1",
        "page_index": str(pageno),
        "bidSort": "0",
        "buyerName": "",
        "projectId": "",
        "pinMu": "0",
        "bidType": "0",
        "dbselect": "bidx",
        "kw": "大数据",
        "start_time": "2017:01:01",
        "end_time": "2017:12:31",
        "timeType": "6",
        "displayZone": "",
        "zoneId": "",
        "pppStatus": "0",
        "agentName": "",
    }
    return http_get_html(ccgp_search_url, payload=payload)


def fetch_bid_page(link):
    return http_get_html(link)


def parse_search_page(search_doc):
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
    for bid in bid_list:
        bid_page = fetch_bid_page(bid.link)
        html_path = urllib.parse.urlparse(bid.link).path
        html_name = os.path.basename(html_path)
        file_path = os.path.join(directory, html_name)
        with open(file_path, 'w') as html_file:
            html_file.write(bid_page)
        bid.file_path = file_path
        print('Fetched {}|{}'.format(bid.link, bid.desc))