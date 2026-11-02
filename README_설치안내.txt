BoxOffice Predictor 2차 버전 — GitHub Actions 자동 수집

1) GitHub 저장소 Settings > Secrets and variables > Actions > New repository secret
   Name: KOBIS_API_KEY
   Secret: KOBIS에서 발급받은 API 키 (절대로 채팅이나 공개 저장소에 붙여넣지 마세요)

2) ZIP을 풀어 나온 index.html, data 폴더, scripts 폴더, .github 폴더를
   GitHub 저장소 최상위에 업로드하세요. 기존 index.html은 새 파일로 교체합니다.
   GitHub 웹 업로드에서는 .github 같은 숨김 폴더가 누락되지 않도록 확인하세요.
   README_설치안내.txt는 업로드하지 않아도 됩니다.

3) 저장소 Actions > Update KOBIS daily box office > Run workflow 클릭
   (최초 수집은 약 30일간의 '일별 박스오피스 상위 10위' 데이터를 가져옵니다.)

4) Actions 실행 성공 후 data/history.json이 생성/갱신되었는지 확인하세요.
   GitHub Pages에 변경이 반영되면 웹사이트에서 영화를 선택할 수 있습니다.

참고:
- 매일 한국시간 오후 1시 25분에 실행 예약(실제 실행은 지연될 수 있음)
- API 사용량/공식 데이터 갱신 시점에 따라 실행 오류가 발생할 수 있음
- 공개 API는 상위 10개 영화만 반환하므로 모든 영화를 검색하는 기능은 아직 없음
- 관객 수 예측, 좌석 수, 시간대별 데이터는 아직 구현되지 않음
- 누적 관객 수는 KOBIS 제공 수치이며, 30일 이전의 관객 기록은 보존하지 않음
