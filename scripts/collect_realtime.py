"""Collect KOBIS public real-time ticketing snapshots (no login required).

Requires verification of the eight-column table before enabling a schedule.
No secrets, cookies, or raw HTML are written to the repository.
"""
import datetime as dt
import http.cookiejar
from html.parser import HTMLParser
import json
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

URL = "https://www.kobis.or.kr/kobis/business/stat/boxs/findRealTicketList.do"
OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "realtime.json"


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.token = None
        self.rows = []
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("name") == "CSRFToken":
            self.token = attrs.get("value")
        if tag == "tr":
            self.row = []
        if tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join(" ".join(self.cell).split()))
            self.cell = None
        if tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None


def fetch(opener, data=None):
    for attempt in range(3):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; BoxOfficePredictor/1.0)"}
            if data is not None:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            req = urllib.request.Request(URL, data=data, headers=headers)
            with opener.open(req, timeout=25) as resp:
                if resp.status != 200:
                    raise RuntimeError("Unexpected HTTP status")
                return resp.read().decode("utf-8", errors="replace")
        except (TimeoutError, urllib.error.URLError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def integer(value):
    value = value.replace(",", "").strip()
    if not re.fullmatch(r"\d+", value):
        raise ValueError("Not an unsigned integer")
    return int(value)


def parse_films(body):
    parser = PageParser()
    parser.feed(body)
    films = []
    for row in parser.rows:
        # KOBIS: rank, film, release date, booking rate, booking revenue,
        # cumulative revenue, advance audience, cumulative audience.
        if len(row) != 8 or not re.fullmatch(r"\d+", row[0]):
            continue
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row[2]):
            continue
        if not re.fullmatch(r"\d+(?:\.\d+)?%", row[3]):
            raise ValueError("Unexpected booking rate format")
        films.append({
            "rank": integer(row[0]),
            "movieNm": row[1],
            "openDt": row[2],
            "bookingRate": float(row[3].rstrip("%")),
            "bookingAudience": integer(row[6]),
            "cumulativeAudience": integer(row[7]),
        })
    if len(films) < 1 or not films[0]["movieNm"]:
        raise ValueError("No validated eight-column film rows; nothing saved")
    ranks = [x["rank"] for x in films]
    # KOBIS uses competition ranking: tied films legitimately share a rank.
    if ranks[0] != 1 or any(a > b for a, b in zip(ranks, ranks[1:])):
        raise ValueError("Unexpected non-monotonic film ranking; nothing saved")
    if len({(x["movieNm"], x["openDt"]) for x in films}) != len(films):
        raise ValueError("Duplicate film and release-date rows; nothing saved")
    return films


def main():
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )
    page = PageParser()
    page.feed(fetch(opener))
    if not page.token:
        raise RuntimeError("Missing CSRF token")
    params = {
        "CSRFToken": page.token, "loadEnd": "0", "repNationCd": "",
        "areaCd": "", "repNationSelected": "", "totIssuAmtRatioOrder": "",
        "totIssuAmtOrder": "", "addTotIssuAmtOrder": "",
        "totIssuCntOrder": "", "totIssuCntRatioOrder": "",
        "addTotIssuCntOrder": "", "dmlMode": "search",
        "allMovieYn": "Y", "sMultiChk": "",
    }
    films = parse_films(fetch(opener, urllib.parse.urlencode(params).encode()))
    now = dt.datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    content = {"source": "KOBIS public real-time booking", "snapshots": []}
    if OUT.exists():
        content = json.loads(OUT.read_text(encoding="utf-8"))
    snapshots = content.setdefault("snapshots", [])
    snapshots.append({"collectedAtKST": now, "films": films})
    # Keep 14 days of hourly snapshots, including any extra manual runs.
    cutoff = dt.datetime.now(ZoneInfo("Asia/Seoul")) - dt.timedelta(days=14)
    content["snapshots"] = [
        s for s in snapshots
        if dt.datetime.fromisoformat(s["collectedAtKST"]) >= cutoff
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Saved", len(films), "films at", now, "snapshots:", len(content["snapshots"]))
    print("First film:", films[0]["movieNm"], "booking:", films[0]["bookingAudience"],
          "cumulative:", films[0]["cumulativeAudience"])


if __name__ == "__main__":
    main()
