# osp_project
2020S Open Source Programming Final Project

06/07/20 (이채준)
---
- url 입력 인터페이스 구현
- 17번줄, 19번줄에 있는 df_to_html에 입력 받은 주소가 저장돼있음(크롤링할 때 여기에 저장된 주소 사용하면 됨)
- 디자인할 때는 버튼을 만들어 단일 입력과 파일 입력 중 하나만 입력받을 수 있게 해야할 듯. 두 개 다 입력하면 텍스트만 남음.

06/09/20 (조호성)
---
- 크롤링 구현 완료
- 33번줄부터 있던 select들을, body tag 하나만 select 하도록 변경. 정상 작동됨.

06/09/20 (이세은)
---
- elasticsearch 구현 완료.
- **elasticsearch 실행 : shell script에 적기.**

06/09/20 (이채준)
---
- tfidf 구현 완료
- 대부분의 함수와 변수에 주석 달았음
- tfidf 기반 top 10을 리턴할 수 있음
- tfidf를 여러 개의 url input에 대해서도 가

06/10/20 (조호성)
---
- main.html과 main_css.css의 prototype을 만듦.
- main_css.css를 통해 main.html을 디자인함.
- **전체 디자인에 대해 팀원들과 상의해보기** -> *very good(이채준)*
- url.html을 만들고, url.html에 쓰이는 class들을 main_css.css에 추가함.

06/10/20 (이세은)
---
- text.html의 prototype 작성
- main.css 로 text.html 디자인

06/11/20 (이채준)
---
- tfidf로 top10 조회 가능하도록 구현함
- cossimil 버튼은 만들었지만 아직 기능은 구현 못함 ㅎㅎ 내일 할 예정
- 크롤링은 빠른데 tfidf 구하는데 시간이 많이 걸려서 로딩 시간이 불필요하게 길어짐. 최적화 하려고 시도 중임. ~하지만 터짐~

06/13/20 (이채준)
---
- cossimil 기능 구현 완료
- 크롤링과 tfidf를 분리해냄. sent_list를 데이터 베이스에 저장하는 것으로 결정함. 처음 데이터베이스에 저장할 때는 시간 좀 걸리는 듯
- 중복 및 크롤링 실패에 대한 처리 완료. 중복에는 "duplicated link"라고 출력하게 했음. 실패한 크롤링에는 "Webcrawling Failed"를 출력하게 했음.
- css를 적용함. Flask에서 css 파일을 이용하기 위해서는 static 폴더 안에 넣어야 함. 따라서 모든 html에서의 css 경로는 "../static/main.css"여야함.
