import json
import requests
import sys
from bs4 import BeautifulSoup


host = "http://chinabidding.org.cn/"
def parse_urls(doc):
    soup = BeautifulSoup(doc, "html.parser")
    # print(soup.prettify())
    table = soup.find(id="TableList")
    urls = []
    for link in table.find_all('a'):
        desc = link.get_text()
        url = host + link.get('href')
        print("{}|{}".format(desc, url))
        urls.append((desc, url))
    sys.stdout.flush()
    return urls


def parse_all():
    # host = "http://chinabidding.org.cn/"
    start_url = "http://chinabidding.org.cn/LuceneSearch.aspx?kwd=%u5927%u6570%u636e&filter=b-12-0-keyword-30"
    # start_url = "http://www.baidu.com"

    all_urls = []
    payload = {
        '__VIEWSTATE': '/wEPDwUKMjA4NDg4Mzg2MA9kFgICAQ9kFgQCDw8PFgIeBFRleHQFE+eUqOaXtu+8mjUzNjPmr6vnp5JkZAITDw8WCB4IQ3NzQ2xhc3MFDGFsaWduLWNlbnRlch4LUmVjb3JkQ291bnQCrAgeBF8hU0ICAh4HQ3VyUGFnZQICZGRkwUNMcxN+g7z1mRNKwWDjOlsaRSQFruqcOyEShYYjqVg=',
        'AspNetPager': '1',
        'DropDownList1': 'b',
        'DropDownList2': '12',
        'DropDownList3': '',
        'DropDownList4': 'keyword',
        'DropDownList5': '360',
        'TextBoxSearch': '大数据',
    }
    for page in range(1, 37):
        sys.stderr.write("Page {} of {}\n".format(page, 37))
        payload['AspNetPager'] = str(page)
        r = requests.post(start_url, data=payload)
        r.encoding = 'utf-8'
        urls_one_page = parse_urls(r.text)
        all_urls.extend(urls_one_page)

    return all_urls


all_urls = parse_all()
# print(all_urls)
json_data = {'urls': all_urls}
with open('urls.txt', 'w') as outfile:
    json.dump(json_data, outfile)
