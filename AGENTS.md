# AGENTS.md

## 프로젝트

조세진 ♥ 이지희 결혼식 **모바일 청첩장**을 만드는 프로젝트입니다.

- 예식: 2027년 1월 9일 토요일 오후 6시
- 장소: 메리빌리아더프레스티지 수원, 2층 컨벤션홀 (경기도 수원시 권선구 세화로 116)
- 배포: GitHub Pages — https://seya330.github.io/sejin-jeehee-wedding/
- 저장소: git@github.com:seya330/sejin-jeehee-wedding.git

## 구조

빌드 도구와 의존성이 없는 **단일 정적 파일** 프로젝트입니다.

```
index.html         # 전체 청첩장 (HTML + CSS + JS + base64 이미지, 약 20MB / 13,000줄)
photos/            # 하단 사진 스트립에 쓰는 사진 (여기에 넣는다)
photos/photos.js   # 사진 목록. update-photos.sh 가 생성한다. 직접 고치지 않는다.
update-photos.sh   # photos/ 를 훑어 photos.js 를 다시 만든다.
qr/                # QR 이미지 (.gitignore 처리, 저장소에 포함하지 않음)
```

- 외부 CDN이나 패키지 매니저를 쓰지 않습니다. 이미지와 폰트는 모두 base64로 `index.html` 안에 인라인되어 있습니다.
- 확인 방법: 브라우저로 `index.html`을 열고 모바일 뷰포트로 봅니다. 빌드나 서버 실행 단계는 없습니다.

## index.html 다루기

파일이 커서 통째로 읽으면 컨텍스트가 낭비됩니다.

- base64 줄(5,000자 이상)이 83개 있습니다. 구조를 볼 때는 긴 줄을 걸러냅니다.
  ```bash
  awk 'length($0)<300' index.html | grep -nE '<section|<h2|var='
  ```
- 수정할 위치를 먼저 `grep -n`으로 찾고, `sed -n 'A,Bp'`로 해당 범위만 읽습니다.
- base64 데이터 URI는 절대 출력하거나 재작성하지 않습니다.

## 섹션 규칙

각 블록은 `<section class="sectionN" var="useXxx">` 형태입니다.

- 사용하지 않는 섹션은 삭제하지 않고 `style="display:none!important" hidden aria-hidden="true"`로 숨깁니다. 기존 코드가 이 방식을 따르므로 유지합니다.
- 텍스트 요소에 붙은 `var="..."` 속성은 템플릿 식별자입니다. 임의로 바꾸거나 지우지 않습니다.

### 현재 켜져 있는 섹션

인사말(section12), 신랑·신부 소개(section3), 예식 안내·캘린더(section4), 오시는 길(section6),
사진 스트립(section_photos).

### 현재 꺼져 있는 섹션

시(section2), 웨딩 인터뷰(section14), 게스트스냅(section19), 갤러리(section5), 타임라인(section18), 공지(section17), 안내(section7), 참석 여부(section8), 마음 전하실 곳(section9), 방명록(section10), 첫 방문(section13).

## 사진 스트립 (section_photos)

오시는 길과 맺음말 사이에 들어가는 직접 만든 섹션입니다. 템플릿 기본 갤러리(section5)와는 별개이고,
Swiper 같은 외부 라이브러리를 쓰지 않습니다.

사진을 넣는 순서는 이렇습니다.

1. `photos/` 에 이미지를 넣는다.
2. `./update-photos.sh` 를 실행한다.
3. `photos/photos.js` 가 다시 만들어진다. 파일 이름 순으로 노출된다.

사진이 없으면 `photos.js` 가 빈 배열이 되고 섹션 전체가 숨겨집니다.

동작은 이렇습니다.

- 하단 가로 스크롤 목록. 카드 폭은 컨테이너의 68%이고 `scroll-snap-align: start` 로 왼쪽에 맞춰 멈춥니다.
  다음 카드가 오른쪽에 걸쳐 보여서 넘길 수 있다는 신호를 줍니다.
- 카드를 누르면 전체 화면 뷰어가 열립니다. 좌우 스와이프로 이동하고 하단에 `3 / 12` 형태로 위치를 보여줍니다.
- 뷰어에서 사진을 더블탭하면 2.4배 확대되고, 확대 중에는 끌어서 움직입니다. 다시 더블탭하면 원래대로 돌아갑니다.
- 사진 바깥 여백을 누르거나 오른쪽 위 X 를 누르면 닫힙니다. 사진 위를 한 번 누르는 것은 닫기가 아닙니다.
  더블탭 확대와 충돌하기 때문입니다.
- 뷰어 안에서는 현재 사진 기준 앞뒤 한 장만 미리 불러옵니다.

관련 코드 위치입니다.

- CSS: `index.html` 의 마지막 `<style>` 블록, `/* 사진 스트립 (photos/ 폴더 기반) */` 주석 아래
- 마크업: `<section class="section_photos" id="photoStrip">`
- 뷰어와 스크립트: `</html>` 바로 앞. 뷰어는 `#user_wrap` 바깥(body 직계)에 둡니다.
  `#user_wrap` 안에 넣으면 `overflow:hidden` 에 잘립니다.

`photos.js` 는 JSON 이 아니라 `window.WEDDING_PHOTOS` 를 정의하는 스크립트입니다.
`fetch` 를 쓰면 `file://` 에서 CORS 로 막히기 때문에 `<script src>` 로 불러옵니다.
그래서 `index.html` 을 브라우저로 바로 열어도 사진이 보입니다.

## 주의

- `마음 전하실 곳`(section9)에는 계좌번호가 들어갑니다. 커밋 전에 실제 계좌 정보가 포함되는지 확인합니다.
- `qr/` 디렉터리는 `.gitignore`에 있습니다. 추적 대상으로 되돌리지 않습니다.
- 지도 버튼은 TMap·카카오내비를 숨기고 네이버 지도 검색으로만 연결합니다(`index.html` 하단 스크립트).
- `photos/` 사진은 저장소에 커밋합니다. GitHub Pages 가 그대로 서빙합니다. 원본을 그대로 올리지 말고
  긴 변 1600px, 장당 500KB 이하로 줄여서 넣습니다.
- 새 섹션에는 `aos` 속성을 붙이지 않습니다. 이 페이지에서 AOS 애니메이션이 제대로 동작하지 않아
  기존 섹션도 `opacity:1!important` 로 강제해 둔 상태입니다.
