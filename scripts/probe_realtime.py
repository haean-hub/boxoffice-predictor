"""Probe the public KOBIS real-time booking page without logging in.

Diagnostic only: does not claim that a page view equals a successful data capture.
"""
import datetime as dt
import html
import re
import urllib.request
from zoneinfo import ZoneInfo

URL = "https://www.kobis.or.kr/kobis/business/stat/boxs/findRealTicketList.do"


def main():
    req = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; BoxOfficePredictor/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        body = response.read().decode("utf-8", errors="replace")
        print("HTTP status:", response.status)
        print("Response bytes:", len(body.encode("utf-8")))
    # Do not persist HTML, cookies, or any credentials.
    print("Checked at (KST):", dt.datetime.now(ZoneInfo("Asia/Seoul")).isoformat())
    print("Contains cumulative audience heading:", "누적관객수" in body)
    print("Contains advance-booking heading:", "예매관객수" in body)
    print("Contains empty-results message:", "검색된 데이터가 존재하지 않습니다" in body)
    print("Contains apparent movie data rows:", bool(re.search(r"<tr[^>]*>\\s*<td", body, re.I)))
    if "누적관객수" not in body or "예매관객수" not in body:
        raise SystemExit("FAIL: expected column headings not found")
    if "검색된 데이터가 존재하지 않습니다" in body:
        raise SystemExit("INCONCLUSIVE: KOBIS returned no rows; do not save fabricated data")
    print("Page reachable. Still need to identify and validate actual film values.")


if __name__ == "__main__":
    main()
