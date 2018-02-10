import json
import os
import urllib


class BidEntry(object):
    """Bidding information: description, url, date, and buyer."""
    def __init__(self):
        super(BidEntry, self).__init__()
        self.desc = None
        self.link = None
        self.date = None
        self.buyer = None
        self.file_path = ''

    def __str__(self):
        return "desc: {}\nlink: {}\ndate: {}\nbuyer: {}\npath: {}".format(
            self.desc, self.link, self.date, self.buyer, self.file_path)

    def get_html_name(self):
        html_path = urllib.parse.urlparse(self.link).path
        html_name = os.path.basename(html_path)
        return html_name

    def load_html(self):
        if not os.path.isfile(self.file_path):
            return None

        doc = None
        with open(self.file_path) as htlm_file:
            doc = htlm_file.read()
        return doc

    def to_list(self):
        return [self.desc, self.link, self.date, self.buyer, self.file_path]

    def from_list(self, l):
        self.desc = l[0]
        self.link = l[1]
        self.date = l[2]
        self.buyer = l[3]
        self.file_path = l[4]


class BidInfo(object):
    """A collection of biddings."""
    def __init__(self):
        super(BidInfo, self).__init__()
        self.entries = []
        self.next_page = 1

    def __str__(self):
        return "\n".join([str(entry) for entry in self.entries])

    def extend_page(self, li):
        self.entries.extend(li)
        self.next_page += 1

    def load(self, filename):
        with open(filename) as json_file:
            data = json.load(json_file)
            self.from_dict(data)

    def save(self, filename):
        with open(filename, 'w') as outfile:
            json.dump(self.to_dict(), outfile, sort_keys=True, indent=4)

    def to_dict(self):
        return {"next_page": self.next_page,
                "entries": [entry.to_list() for entry in self.entries]}

    def from_dict(self, d):
        self.next_page = d["next_page"]
        self.entries.clear()
        for e in d["entries"]:
            entry = BidEntry()
            entry.from_list(e)
            self.entries.append(entry)
