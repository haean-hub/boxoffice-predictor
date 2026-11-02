"""Test public KOBIS real-time search with a fresh anonymous CSRF token.

Diagnostic only. No credentials or cookies are logged or persisted.
"""
import datetime as dt
import html
from html.parser import HTMLParser
import http.cookiejar
import re
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

URL = "https://www.kobis.or.kr/kobis/business/stat/boxs/findRealTicketList.do"


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.token = None
        self.rows = 0
        self.in_tr = False
        self.in_td = False
        self.cell_text = []
        self.row_cells = []
        self.samples = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("name") == "CSRFToken":
            self.token = attrs.get("value")
        if tag == "tr":
            self.in_tr = True
            self.row_cells = []
        if tag == "td" and self.in_tr:
            self.in_td = True
            self.cell_text = []

    def handle_data(self, data):
        if self.in_td:
            self.cell_text.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.in_td:
            self.row_cells.append(" ".join(" ".join(self.cell_text).split()))
            self.in_td = False
        if tag == "tr" and self.in_tr:
            if len(self.row_cells) >= 5:
                self.rows += 1
                if len(self.samples) < 2:
                    self.samples.append(self.row_cells[:3])
            self.in_tr = False


def request(opener, data=None):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; BoxOfficePredictor/1.0)"}
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(URL, data=data, headers=headers)
    with opener.open(req, timeout=30) as response:
        body = response.read().decode("utf-8", errors="replace")
        print("HTTP:", response.status, "bytes:", len(body.encode("utf-8")))
        return body


def main():
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    initial = request(opener)
    parser = FormParser()
    parser.feed(initial)
    if not parser.token:
        raise SystemExit("INCONCLUSIVE: CSRFToken not found in initial HTML")
    print("CSRF token obtained (value withheld)")
    params = {
        "CSRFToken": parser.token,
        "loadEnd": "0",
        "repNationCd": "",
        "areaCd": "",
        "repNationSelected": "",
        "totIssuAmtRatioOrder": "",
        "totIssuAmtOrder": "",
        "addTotIssuAmtOrder": "",
        "totIssuCntOrder": "",
        "totIssuCntRatioOrder": "",
        "addTotIssuCntOrder": "",
        "dmlMode": "search",
        "allMovieYn": "Y",
        "sMultiChk": "",
    }
    result = request(opener, urllib.parse.urlencode(params).encode())
    parsed = FormParser()
    parsed.feed(result)
    print("Checked at KST:", dt.datetime.now(ZoneInfo("Asia/Seoul")).isoformat())
    print("Cumulative audience heading:", "누적관객수" in result)
    print("Advance audience heading:", "예매관객수" in result)
    print("No-results message:", "검색된 데이터가 존재하지 않습니다" in result)
    print("Candidate HTML table rows:", parsed.rows)
    print("Sample first 3 cells (not validated):", parsed.samples)
    if parsed.rows == 0:
        raise SystemExit("INCONCLUSIVE: POST returned no identifiable film rows")
    print("POST returned rows; film/metric parsing must be validated before hourly collection.")


if __name__ == "__main__":
    main()
