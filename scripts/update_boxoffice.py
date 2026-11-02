"""Collect KOBIS daily box office without exposing the API key."""
import datetime as dt
import json
import os
import pathlib
import time
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data' / 'history.json'
API = 'https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json'


def fetch(day, key):
    params = urllib.parse.urlencode({'key': key, 'targetDt': day})
    req = urllib.request.Request(API + '?' + params, headers={'User-Agent': 'BoxOfficePredictor/2.0'})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = json.load(response)
    if 'faultInfo' in data:
        raise RuntimeError('KOBIS API error: ' + str(data['faultInfo'].get('message', 'unknown')))
    result = data['boxOfficeResult']
    rows = []
    for item in result['dailyBoxOfficeList']:
        rows.append({
            'movieCd': item['movieCd'],
            'movieNm': item['movieNm'],
            'rank': int(item['rank']),
            'openDt': item.get('openDt', ''),
            'audiCnt': int(item['audiCnt']),
            'audiAcc': int(item['audiAcc']),
            'scrnCnt': int(item.get('scrnCnt', 0)),
            'showCnt': int(item.get('showCnt', 0)),
        })
    return rows


def main():
    key = os.environ.get('KOBIS_API_KEY', '').strip()
    if not key:
        raise SystemExit('Missing KOBIS_API_KEY GitHub Actions secret')
    today = dt.datetime.now(ZoneInfo('Asia/Seoul')).date()
    yesterday = today - dt.timedelta(days=1)
    if OUTPUT.exists():
        content = json.loads(OUTPUT.read_text(encoding='utf-8'))
    else:
        content = {'source': 'KOBIS daily box office top 10', 'days': {}}
    days = content.setdefault('days', {})
    # First run: backfill the last 30 complete days. Subsequent runs: refresh
    # the last three days to accommodate delayed official updates.
    count = 30 if not days else 3
    for offset in range(count - 1, -1, -1):
        date = yesterday - dt.timedelta(days=offset)
        stamp = date.strftime('%Y%m%d')
        days[stamp] = fetch(stamp, key)
        print('Collected', stamp, len(days[stamp]))
        time.sleep(0.15)
    content['days'] = dict(sorted(days.items()))
    content['lastCollectedKST'] = dt.datetime.now(ZoneInfo('Asia/Seoul')).isoformat(timespec='seconds')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(content, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Saved', len(content['days']), 'days')


if __name__ == '__main__':
    main()
