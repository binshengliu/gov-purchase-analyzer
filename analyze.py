from bs4 import BeautifulSoup
import os
import re
import datetime
# from IPython.core.debugger import Pdb
import xlsxwriter
# import webbrowser
from bid import BidInfo
from operator import itemgetter


guess_len = 30
large_money_threshold = 100000000
large_money_whitelist = {"t20171130_9255309.htm": None,
                         "t20170817_8703996.htm": None,
                         "t20170810_8660916.htm": None,
                         "t20170724_8569742.htm": None,
                         "t20170321_8023052.htm": None}

money_regexp = '|'.join(['总成交金额', '项目估算金额', '中标金额', '预算金额',
                         '项目预算', '预算价', '采购预算控制额度',
                         '磋商保证金的金额', '预算：', '总报价（元）',
                         '成交价（元）', '成交总价', '成交金额（元）',
                         '总报价（万元）', '招标控制价', '中标（成交）金额'])
money_regexp_obj = re.compile(money_regexp)


def analyze_money(filepath):
    """Analyze biddings from file."""
    bid_info = BidInfo()
    if not os.path.isfile(filepath):
        print("{} not found".format(filepath))
        return

    bid_info.load(filepath)

    excel = MoneyExcel(os.path.splitext(filepath)[0] + ".xlsx")
    excel.init_header()

    bid_map = dedup_by_project_name(bid_info)

    total = 0.0
    found = 0
    failed = 0
    location_stats = {}

    bid_list = [(project, date, money, original_wrong, location, entry)
                for project, (date, money, original_wrong, location, entry)
                in bid_map.items()]
    bid_list.sort(key=itemgetter(1))

    for (project, date, money, original_wrong, location, entry) in bid_list:
        excel.write_entry(project, date, entry.buyer, location, money,
                          original_wrong, entry.link)
        if money:
            location_stats.setdefault(location, 0)
            location_stats[location] += money
            total += money
            found += 1
        else:
            failed += 1

    excel.write_statistics()

    excel.write_location_stats_sheet(location_stats)

    excel.write_comments()

    excel.close()

    # webbrowser.open(os.path.join("html", html))
    print("Found money in {} of {} bids.".format(found, found + failed))
    print("Total money: {}".format(total))


def dedup_by_project_name(bid_info):
    """Deduplicate biddings by their descriptions."""
    bid_map = {}

    for entry in bid_info.entries:
        html_name = entry.get_html_name()
        doc = entry.load_html()
        soup = BeautifulSoup(doc, "html.parser")

        location = find_location(entry.buyer, entry.desc, soup.text)
        money = find_money(soup)
        original_wrong = False
        if money:
            if money > large_money_threshold \
               and html_name not in large_money_whitelist:
                    original_wrong = True
                    money /= 10000

            print("Found in {}: {}\n".format(entry.get_html_name(), money))
        else:
            print("Failed in {}\n".format(entry.get_html_name()))

        date = datetime.datetime.strptime(entry.date.split(" ")[0], '%Y.%m.%d')
        project = formalize_project_name(entry.desc)
        if project in bid_map:
            if money and bid_map[project][1] and bid_map[project][1] < money:
                bid_map[project] = (date, money, original_wrong, location, entry)
        else:
            bid_map[project] = (date, money, original_wrong, location, entry)

    return bid_map


announce = ['评审结果', '答疑澄清', '资格预审', '采购文件',
            '公开招标', '谈判失败', '采购比选', '招标编号',
            '单一来源', '公开招标', '招标报名', '延期开标',
            '竞争性', '预公示', '预公告', '预中标',
            '补充', '询价', '更改', '招标', '采购', '中标',
            '中标', '更正', '变更', '成交', '流标', '结果',
            '终止', '废标', '合同', '磋商', '公开', '磋商'
            '暂停', '比选', '延期', '失败', '澄清', '撤销',
            '谈判', '其它', '答疑', '调整', '中止', '废除',
            '竞标', '征求', '谈判', '公示', '公告', '意见',
            '取消', '通知', '评标', '重新', '公物']
announce_regexp1 = '({keywords})+(：|－)'.format(keywords='|'.join(announce))
announce_regexp2 = '(的?({keywords})+(的|、)?)+'.format(keywords='|'.join(announce))
announce_obj1 = re.compile(announce_regexp1)
announce_obj2 = re.compile(announce_regexp2)


def formalize_project_name(desc):
    """Remove trivial text from bidding description"""
    desc = re.sub('\s', '', desc)
    desc = re.sub('\(', '（', desc)
    desc = re.sub('\)', '）', desc)
    desc = re.sub('<', '〈', desc)
    desc = re.sub('>', '〉', desc)
    desc = re.sub('-', '－', desc)
    desc = re.sub(':', '：', desc)

    desc = re.sub('(（.*编号.*）)|(【.*编号.*】)', "", desc)
    desc = re.sub('(（.*[a-zA-Z0-9－#]{5,}.*）)|【.*[a-zA-Z0-9－#]{5,}.*】', "", desc)
    desc = re.sub('.*关于', '', desc)
    desc = announce_obj1.sub('', desc)
    desc = announce_obj2.sub('', desc)

    desc = re.sub('（）', '', desc)

    desc = desc.strip('项目')
    desc = desc.strip('－')
    desc = desc.strip('、')
    desc = desc.strip('的')
    desc = desc.strip('/')

    desc = re.sub('^[a-zA-Z0-9－#]{5,}', '', desc)
    desc = re.sub('[a-zA-Z0-9－#]{5,}$', '', desc)
    return desc


location_table = [("呼和浩特", "呼和浩特市"),
                  ("锡林浩特", "锡林浩特市"),
                  ("哈尔滨", "哈尔滨市"),
                  ("秦皇岛", "秦皇岛市"),
                  ("武夷山", "武夷山市"),
                  ("张家口", "张家口市"),
                  ("石家庄", "石家庄市"),
                  ("三门峡", "三门峡市"),
                  ("额济纳旗", "额济纳旗"),
                  ("达拉特旗", "达拉特旗"),
                  ("鄂尔多斯", "鄂尔多斯市"),
                  ("辽宁科技学院", "沈阳市")]


def find_location(buyer, desc, content):
    """Find location in buyer, description, and content."""
    return find_location_helper(buyer) or \
        find_location_helper(desc) or \
        find_location_helper(content)


def find_location_helper(string):
    """Find location in a string."""
    for location in location_table:
        if re.search(location[0], string):
            return location[1]

    for pos in re.finditer("市", string):
        start = max(0, pos.start() - 2)
        end = pos.start() + 1
        guess = string[start:end].strip()
        bad_guess = ['市', "城市", "区域市", "县城市", "海城市", "州城市", "性城市",
                     "慧城市", "波城市", "/城市", "京城市", "在城市", "称城市",
                     "他城市", "果）市", "究（市", "发（市"]
        if guess in bad_guess:
            continue
        else:
            return guess

    pos = re.search("州", string)
    if pos:
        start = max(0, pos.start() - 2)
        guess = string[start:pos.start()+1].strip()
        match = re.search('(广|苏|福|郑|池|锦|兰|柳|高|惠|杭|漳|泉|钦)(州)', guess)
        if match:
            return match.group(0) + '市'
        if re.search('贵州', guess):
            return '贵州省'
        bad_guess = ['自治州']
        if guess not in bad_guess:
            return guess

    for pos in re.finditer("省", string):
        start = max(0, pos.start() - 2)
        guess = string[start:start+3].strip()
        if guess == '龙江省':
            return '黑龙江省'
        if guess == '省旅游':
            continue
        return guess

    pos = re.search("县", string)
    if pos:
        start = max(0, pos.start() - 2)
        return string[start:pos.start()+1].strip()

    return None


def find_money(soup):
    """Find money string in a html page."""

    content = soup.find("div", class_="vF_detail_main")
    if not content:
        content = soup.find("div", class_="vT_detail_main")
        if not content:
            return None
    content = content.text
    # print(content)
    # Pdb().set_trace()
    min_num = None
    for match in money_regexp_obj.finditer(content):
        start = match.start()
        # print("Found match: {}".format(content[start:start+guess_len]))
        parse_result = parse_num(content[start:])
        if parse_result:
            if parse_result < 10000:
                continue
            if not min_num:
                min_num = parse_result
            else:
                min_num = min(parse_result, min_num)

    # print("Found money: {}".format(context))
    return min_num


def isfloat(x):
    """Test if a string is a valid float number."""
    try:
        float(x)
    except ValueError:
        return False
    else:
        return True


def starts_with_wan(string):
    """Test if a string starts with Chinese \"ten thousand\"."""
    return string.startswith('万') or string.startswith('万元') \
        or string.startswith('（万）') or string.startswith('（万元）') \
        or string.startswith('(万元)')


def parse_num(string):
    """Try to find a number in a string."""
    candidate = ''
    pos = 0
    while string[pos].isspace():
        pos += 1

    found_digit = False
    for i in range(min(len(string), guess_len)):
        # print(string[i])
        if isfloat(string[i]):
            pos = i
            found_digit = True
            break

    if not found_digit:
        # print("Didn't find an digit.")
        return None

    char = string[pos]
    while char == ',' or isfloat(candidate + char):
        if isfloat(candidate + char):
            candidate += char
        pos += 1
        if pos >= len(string):
            break
        char = string[pos]

    ten_thousand = False
    if starts_with_wan(string[pos:]):
        ten_thousand = True

    if isfloat(candidate):
        num = float(candidate)
        if ten_thousand:
            num *= 10000
        return num

    return None


PRJ_COL = 0
DATE_COL = 1
BUYER_COL = 2
LOC_COL = 3
MONEY_COL = 4
URL_COL = 5
COMMENT_COL = 7
COUNT_COL = 8
TOTAL_COL = 9


class MoneyExcel(object):
    """Write analysis result to an excel file."""

    def __init__(self, filename):
        super(MoneyExcel, self).__init__()
        self.filename = filename
        self.workbook = xlsxwriter.Workbook(filename)
        self.worksheet = self.workbook.add_worksheet("详细信息")
        self.row = 1
        self.data_count = 1
        # Add a number format for cells with money.
        self.date_format = self.workbook.add_format({'num_format': 'yyyy年mm月dd日'})

        self.money_format = self.workbook.add_format({'num_format': '￥#,##0'})

        self.large_format = self.workbook.add_format({'num_format': '￥#,##0'})
        self.__fill_color(self.large_format, 'green')

        self.moderate_format = self.workbook.add_format({'num_format': '￥#,##0'})
        self.__fill_color(self.moderate_format, 'orange')

        self.million_format = self.workbook.add_format({'num_format': '￥#,##0'})
        self.__fill_color(self.million_format, 'yellow')

        self.wrong_format = self.workbook.add_format({'num_format': '￥#,##0'})
        self.__fill_color(self.wrong_format, 'red')

    def __fill_color(self, fmt, color):
        fmt.set_pattern(1)
        fmt.set_bg_color(color)

    def init_header(self):
        """Init excel table header."""
        self.worksheet.write(0, PRJ_COL, "项目")
        self.worksheet.set_column(PRJ_COL, PRJ_COL, 40)

        self.worksheet.write(0, DATE_COL, "日期")
        self.worksheet.set_column(DATE_COL, DATE_COL, 20)

        self.worksheet.write(0, BUYER_COL, "采购方")
        self.worksheet.set_column(BUYER_COL, BUYER_COL, 20)

        self.worksheet.write(0, LOC_COL, "地点")

        self.worksheet.write(0, MONEY_COL, "金额")
        self.worksheet.set_column(MONEY_COL, MONEY_COL, 20)

        self.worksheet.write(0, URL_COL, "网址")
        self.worksheet.set_column(URL_COL, URL_COL, 60)

    def write_entry(self, desc, date, buyer, location, money, original_wrong, url):
        """Write a bidding entry as a row."""
        self.worksheet.write(self.row, PRJ_COL, desc)

        self.worksheet.write_datetime(self.row, DATE_COL, date, self.date_format)

        self.worksheet.write(self.row, BUYER_COL, buyer)

        self.worksheet.write(self.row, LOC_COL, location)

        if money:
            if original_wrong:
                self.worksheet.write(self.row, MONEY_COL, money, self.wrong_format)
            elif money >= 100000000:
                self.worksheet.write(self.row, MONEY_COL, money, self.large_format)
            elif money >= 10000000:
                self.worksheet.write(self.row, MONEY_COL, money, self.moderate_format)
            elif money >= 1000000:
                self.worksheet.write(self.row, MONEY_COL, money, self.million_format)
            else:
                self.worksheet.write(self.row, MONEY_COL, money, self.money_format)
        else:
            self.worksheet.write(self.row, MONEY_COL, "未披露", self.money_format)

        self.worksheet.write(self.row, URL_COL, url)
        self.data_count = self.row
        self.row += 1

    def write_statistics(self):
        """Write median, average, and sum of the money."""
        self.worksheet.write(self.row, 0, "中位数")
        self.worksheet.write_formula(self.row, MONEY_COL,
                                     '=(MEDIAN(E2:E{}))'.format(self.data_count + 1),
                                     self.money_format)
        self.row += 1

        self.worksheet.write(self.row, 0, "平均值")
        self.worksheet.write_formula(self.row, MONEY_COL,
                                     '=(AVERAGE(E2:E{}))'.format(self.data_count + 1),
                                     self.money_format)
        self.row += 1

        self.worksheet.write(self.row, 0, "总计")
        self.worksheet.write_formula(self.row, MONEY_COL,
                                     '=(SUM(E2:E{}))'.format(self.data_count + 1),
                                     self.money_format)
        self.row += 1

    def write_location_stats_sheet(self, location_stats):
        """Write statistics by location."""
        worksheet_loc = self.workbook.add_worksheet("按地点统计")
        worksheet_loc.set_column(0, 0, 10)
        worksheet_loc.set_column(1, 1, 20)
        worksheet_loc.write(0, 0, "地点")
        worksheet_loc.write(0, 1, "金额")

        l = [(v, k) for k, v in location_stats.items()]
        l.sort(reverse=True)
        row = 1
        for v, k in l:
            worksheet_loc.write(row, 0, k)
            worksheet_loc.write(row, 1, v, self.money_format)
            row += 1

    def write_comments(self):
        """Write comments."""
        self.worksheet.set_column(COMMENT_COL, COMMENT_COL, 25)
        self.worksheet.set_column(TOTAL_COL, TOTAL_COL, 20)

        self.worksheet.write(0, COMMENT_COL, "备注")
        self.worksheet.write(0, COUNT_COL, "数量")
        self.worksheet.write(0, TOTAL_COL, "总金额")

        self.worksheet.write(1, COMMENT_COL, "红色代表原网页金额有误", self.wrong_format)

        range = "E2:E{}".format(self.data_count+1)
        count_template = "=COUNTIFS({0}, \">={1}\", {0}, \"<{2}\")"
        sum_template = "=SUMIFS({0}, {0}, \">={1}\", {0}, \"<{2}\")"

        self.worksheet.write(2, COMMENT_COL, "绿色代表金额超过1亿元", self.large_format)
        self.worksheet.write_formula(2, COUNT_COL, "=COUNTIF({}, \">=100000000\")".format(range))
        self.worksheet.write_formula(2, TOTAL_COL, "=SUMIF({}, \">=100000000\")".format(range), self.money_format)

        count_formula = count_template.format(range, 10000000, 100000000)
        sum_formula = sum_template.format(range, 10000000, 100000000)
        self.worksheet.write(3, COMMENT_COL, "橙色代表金额超过1千万元", self.moderate_format)
        self.worksheet.write_formula(3, COUNT_COL, count_formula)
        self.worksheet.write_formula(3, TOTAL_COL, sum_formula, self.money_format)

        count_formula = count_template.format(range, 1000000, 10000000)
        sum_formula = sum_template.format(range, 1000000, 10000000)
        self.worksheet.write(4, COMMENT_COL, "黄色代表金额超过1百万元", self.million_format)
        self.worksheet.write_formula(4, COUNT_COL, count_formula)
        self.worksheet.write_formula(4, TOTAL_COL, sum_formula, self.money_format)

    def close(self):
        """Close the excel file."""
        self.worksheet.autofilter(0, 0, self.data_count, URL_COL)

        self.workbook.close()
