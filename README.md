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

06/16/20 (조호성)
---
- result.html, top10.html, similar.html prototype 만듦 (카테고리 만듦)
- main.css에 result, top10, similar html에 쓰인 class 추가함
- result.html에 success와 fail을 어떻게 띄울지 모르겠음.. result1,2로 html 두개 만드는지 아니면 그냥 클래스 두개 만드나..? 물어보기

06/16/20 (이채준)
---
- result.html에서 successful, fail을 구분하는 기능을 만듦
- tfidf와 cossimil에서 분석에 걸린 시간을 추가했음
- (요청사항) result.html에서 successful과 fail 구분할 수 있도록 구현
- (요청사항) tfidf와 cossimil에서 분석에 걸린 시간을 출력할 수 있도록 구현

06/20/20 (이채준)
---
- 돌리다 보니 port를 8000으로 설정해줬음에도 불구하고 브라우저에서는 11932 등의 엉뚱한 포트로 접속하는 것을 발견함.
- 우리 html들은 직접적으로 주소를 정해주는 방식이기 때문에 port 번호가 조금이라도 바뀌면 서비스가 돌아가질 않음,,
- 컴퓨터 껐다 키니까 나아졌긴한데,, 혹시라도 문제가 또 생기면 port를 기본 port인 5000으로 설정해야될 것 같음.

06/24/20 (이세은)
---
- top10.html, css 수정시작
- result.html에서 url을 파일로 넣으면 어떻게 할지 정하기
- design top10.html 아직 정렬 미완성

06/25/20 (이채준)
---
- tfidf 시간 향상 시킴(test.py에서 대대적 수리 과정을 거침)
- html 상에서 표시되는 url 들을 \<a\>를 이용해 하이퍼링크로 만듦
- 전반적인 backend 코드 정리함
- 이제 쉘 스크립트만 만들면 될

06/25/20 (이세은)
---
- top10.html, main.css 정렬, 글자 등등 수정...
- 리스트 디자인은 일단 나중에 손보기
- top3.html 어떻게 할지 생각하기.
