# AGENTS.md

## 프로젝트

조세진 ♥ 이지희 결혼식 **모바일 청첩장**을 만드는 프로젝트입니다.

- 예식: 2027년 1월 9일 토요일 오후 6시
- 장소: 메리빌리아더프레스티지 수원, 2층 컨벤션홀 (경기도 수원시 권선구 세화로 116)
- 배포: GitHub Pages — https://seya330.github.io/sejin-jeehee-wedding/
- 저장소: git@github.com:seya330/sejin-jeehee-wedding.git

## 구조

빌드 도구와 의존성이 없는 정적 파일 프로젝트입니다.

```
index.html         # 전체 청첩장 (HTML + CSS + JS + 작은 base64 아이콘, 약 1.1MB / 13,000줄)
assets/            # index.html 에서 빼낸 큰 자산. 비동기로 불러온다.
  bgm.mp3          #   배경음악
  main.jpg         #   메인 사진. og:image 도 이 파일을 절대 URL 로 가리킨다.
  map.jpg          #   오시는 길 약도
  fonts/           #   GowunDodum, 나눔명조, xeicon(아이콘 폰트)
  template/        #   꺼진 섹션의 템플릿 샘플 이미지 (받지 않는다, 아래 참고)
photos/            # 하단 사진 스트립에 쓰는 사진. 줄인 사본만 넣는다 (긴 변 1600px, 장당 500KB 이하)
photos/photos.js   # 사진 목록. update-photos.sh 가 생성한다. 직접 고치지 않는다.
photos_original/   # 사진 원본 보관 (.gitignore 처리, 저장소에 포함하지 않음)
update-photos.sh   # photos/ 를 훑어 photos.js 를 다시 만든다. 한글 파일 이름은 NFC 로 맞춘다.
tools/intro_write/ # 첫 화면 손글씨 SVG 를 만드는 도구. 페이지가 쓰지 않는 개발용 파일이다 (아래 "첫 화면 오버레이")
qr/                # QR 이미지 (.gitignore 처리, 저장소에 포함하지 않음)
```

- 외부 CDN이나 패키지 매니저를 쓰지 않습니다. 자산은 모두 같은 저장소의 파일입니다.
- 확인 방법: 브라우저로 `index.html`을 열고 모바일 뷰포트로 봅니다. 빌드나 서버 실행 단계는 없습니다.
  `file://` 로 열어도 assets/ 의 이미지, 폰트, 음악이 모두 불러와집니다.

## index.html 다루기

통째로 읽으면 컨텍스트가 낭비됩니다.

- base64 줄(5,000자 이상)이 23개 남아 있습니다. 구조를 볼 때는 긴 줄을 걸러냅니다.
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

### 사진 올리는 법

원본을 `photos/` 에 바로 넣지 않습니다. 원본은 장당 수 MB 라서 모바일에서 무겁고,
저장소가 공개라 한 번 커밋하면 지워도 git 기록에 남습니다.

1. 원본을 `photos_original/` 에 넣습니다. 이 폴더는 `.gitignore` 처리되어 저장소에 올라가지 않습니다.
2. 저장소 루트에서 줄인 사본을 `photos/` 에 만듭니다. 긴 변 1600px, JPEG 품질 82 입니다.
   ```bash
   for f in photos_original/*.jpg; do
     sips -Z 1600 -s format jpeg -s formatOptions 82 "$f" --out "photos/$(basename "$f")"
   done
   ```
   새로 넣은 사진만 처리하려면 `photos_original/` 의 해당 파일만 지정합니다.
3. 500KB 를 넘는 파일이 있는지 확인합니다.
   ```bash
   find photos -name '*.jpg' -size +500k
   ```
   나오면 그 파일만 긴 변을 1440px 로 줄이고 품질을 낮춰 다시 만듭니다. 1600px 에서 품질만 58 까지
   내리는 것보다 1440px 품질 66~78 이 눈으로 보기에 낫습니다. 500KB 아래로 내려올 때까지
   `formatOptions` 를 78 → 74 → 70 → 66 순으로 낮춥니다.
   ```bash
   sips -Z 1440 -s format jpeg -s formatOptions 74 "photos_original/<파일명>" --out "photos/<파일명>"
   ```
4. `./update-photos.sh` 를 실행합니다. `photos/photos.js` 가 다시 만들어집니다.
5. 브라우저로 `index.html` 을 열어 사진 섹션과 크게 보기를 확인합니다.
6. `photos/` 와 `photos/photos.js` 를 함께 커밋합니다. push 하면 GitHub Pages 에 반영됩니다.

알아둘 점입니다.

- 노출 순서는 파일 이름 순입니다. 순서를 바꾸려면 `01-...`, `02-...` 처럼 앞에 숫자를 붙입니다.
- 사진을 빼려면 `photos/` 에서 지우고 `./update-photos.sh` 를 다시 실행합니다.
- 카드는 3:4 비율이라 가로 사진은 가운데 기준으로 잘려 보입니다. 크게 보기에서는 전체가 보입니다.
- 한글 파일 이름을 그대로 써도 됩니다. macOS 는 한글 이름을 NFD(자모 분리)로 돌려주고 git 은 NFC 로
  저장하는데, `update-photos.sh` 가 목록을 NFC 로 맞춥니다. 이 처리를 빼면 로컬에서는 보여도
  GitHub Pages 에서 404 가 납니다.
- `photos.js` 는 손으로 고치지 않습니다. 스크립트를 다시 돌리면 덮어씁니다.

### 동작

사진이 없으면 `photos.js` 가 빈 배열이 되고, 섹션은 스켈레톤 카드 3개와
"사진을 준비하고 있습니다" 문구를 보여줍니다. 섹션이 사라지지는 않습니다.

동작은 이렇습니다.

- 하단 가로 스크롤 목록. 카드 폭은 컨테이너의 68%이고 `scroll-snap-align: start` 로 왼쪽에 맞춰 멈춥니다.
  다음 카드가 오른쪽에 걸쳐 보여서 넘길 수 있다는 신호를 줍니다.
- 카드를 누르면 전체 화면 뷰어가 열립니다. 좌우 스와이프로 이동하고 하단에 `3 / 12` 형태로 위치를 보여줍니다.
- 모바일에서는 브라우저 기본 스크롤로 넘깁니다. 데스크톱은 `overflow-x` 컨테이너를 마우스로 끌어도
  브라우저가 스크롤하지 않으므로 `enableMouseDrag()` 로 직접 붙였습니다. 터치 포인터는 건드리지 않습니다.
  끄는 동안에는 `is_dragging` 으로 스냅을 끄고, 손을 떼면 다시 켜지며 가까운 칸에 멈춥니다.
  6px 넘게 끌었으면 이어지는 click 을 막아 드래그가 사진 열기나 닫기로 이어지지 않게 합니다.
- 뷰어에서 사진을 더블탭하면 2.4배 확대되고, 확대 중에는 끌어서 움직입니다. 다시 더블탭하면 원래대로 돌아갑니다.
- 사진 바깥 여백을 누르거나 오른쪽 위 X 를 누르면 닫힙니다. 사진 위를 한 번 누르는 것은 닫기가 아닙니다.
  더블탭 확대와 충돌하기 때문입니다.
- 뷰어 안에서는 현재 사진 기준 앞뒤 한 장만 미리 불러옵니다.
- 카드와 뷰어 슬라이드는 이미지를 받아오기 전까지 스켈레톤과 로딩 로고를 띄웁니다(아래 "비동기 로딩과 스켈레톤").
  `is_loaded` 가 붙으면 멈춥니다. 이미지 로딩에 실패해도 `error` 에서 같은 클래스를 붙여 무한히 돌지 않게 했습니다.

관련 코드 위치입니다.

- CSS: `index.html` 의 마지막 `<style>` 블록, `/* 사진 스트립 (photos/ 폴더 기반) */` 주석 아래
- 마크업: `<section class="section_photos" id="photoStrip">`
- 뷰어와 스크립트: `</html>` 바로 앞. 뷰어는 `#user_wrap` 바깥(body 직계)에 둡니다.
  `#user_wrap` 안에 넣으면 `overflow:hidden` 에 잘립니다.

`photos.js` 는 JSON 이 아니라 `window.WEDDING_PHOTOS` 를 정의하는 스크립트입니다.
`fetch` 를 쓰면 `file://` 에서 CORS 로 막히기 때문에 `<script src>` 로 불러옵니다.
그래서 `index.html` 을 브라우저로 바로 열어도 사진이 보입니다.

## 비동기 로딩과 스켈레톤

예전에는 음악, 사진, 폰트가 전부 base64 로 `index.html`(약 20MB) 안에 들어 있었습니다.
HTML 을 끝까지 받아야 스크립트가 돌았으므로, "배경음악이 준비 되었습니다" 가 뜨기 전까지
페이지가 멈춘 것처럼 보였습니다. 지금은 큰 자산을 `assets/` 로 빼서 HTML 이 약 1.1MB 입니다.

- 배경음악: `<audio preload="none">` 이라 audio 스스로는 미리 받지 않습니다. 페이지 load 뒤에
  `index.html` 맨 끝 스크립트가 fetch 로 받아 blob URL 로 꽂습니다. 템플릿은 자동재생이 막히면
  곧바로 "배경음악이 준비 되었습니다" 를 띄우는데, 이 스크립트가 `bgm.openGuide` 를 감싸서
  다 받은 뒤에 띄웁니다. 그 전에 눌러도 재생은 됩니다(스트리밍).
  iOS Safari 는 누르기 전에 미디어를 미리 받지 않으므로 `canplaythrough` 로 기다리면 안 됩니다.
  `file://` 에서는 fetch 가 막혀서 예전처럼 바로 띄웁니다.
- 메인 사진: head 초반의 `<link rel="preload">` 로 다른 것보다 먼저 받습니다.
- 약도: `loading="lazy"` 입니다.
- 폰트: `@font-face` 의 형식 목록은 그대로 두었습니다. 브라우저는 자기가 쓰는 형식(보통 woff2/woff)만 받습니다.
- 15KB 미만의 작은 아이콘(지도 버튼 로고 등)은 바로 보여야 해서 base64 로 남겨 두었습니다.

이미지를 받기 전에는 반짝이는 스켈레톤 위에 하트 로고와 그 둘레를 도는 로딩 링을 띄웁니다.
메인 사진, 약도, 사진 스트립 카드, 크게 보기 슬라이드가 모두 같은 모양입니다.

- 메인 사진과 약도는 `<span class="img_skel">` 로 감쌉니다. img 의 `onload`/`onerror` 에서
  head 에 둔 `imgReady(this)` 를 불러 `.is_loaded` 를 붙입니다. 실패해도 붙여서 무한히 돌지 않게 합니다.
- img 에 `width`/`height` 를 꼭 적습니다. 그래야 받기 전에도 자리를 잡아 스켈레톤이 보이고 레이아웃이 밀리지 않습니다.
- 하트는 `--heart-img` 변수를 그대로 씁니다. 색을 바꾸면 달력·디데이 하트와 함께 바뀝니다.
- CSS 위치: 마지막 `<style>` 블록, `/* 이미지 스켈레톤` 주석 아래

### 꺼진 섹션의 템플릿 이미지

`assets/template/` 은 꺼진 섹션(갤러리, 공지, 게스트스냅 등)에 들어 있던 템플릿 샘플 사진입니다.
`src` 가 아니라 `data-src` 로 걸어 두어 받지 않습니다. 템플릿의 Swiper 가 숨은 섹션에서도 초기화되면서
`preloadImages` 와 슬라이드 복제로 이미지를 미리 받아버리기 때문입니다.
섹션을 다시 켤 때는 실제 사진으로 바꾸고 `src` 로 되돌립니다.

## 첫 화면 오버레이

처음 열거나 새로고침하면 흰 화면이 전체를 덮고, "We are / getting / married" 를 세 줄로 손글씨처럼 써 나갑니다.

| 시각 | 동작 |
| --- | --- |
| 0.2초 | 첫 획을 쓰기 시작 |
| 2.8초 | 마지막 획을 다 씀 |
| 3.8초 | 1초 그대로 둔 뒤 사라지기 시작 |
| 4.8초 | 다 사라지고 `visibility:hidden` 이 되어 터치를 막지 않음 |

- 스크립트 없이 CSS 애니메이션만 씁니다. 스크립트가 늦거나 죽어도 화면을 가린 채 남지 않습니다.
- 글씨는 메인 사진의 "Our wedding day" 에 맞췄습니다. 사진 속 글씨는 이미지라 원래 폰트를 알 수 없습니다.
  무료 필기체 후보를 렌더링해 비교하고 가장 비슷한 WindSong(OFL, Google Fonts)을 골랐습니다.
  색 rgb(218, 42, 52)는 사진의 획에서 뽑은 값입니다.
- 폰트를 그대로 쓰지 않고, WindSong 획의 중심선을 뽑아 SVG `path` 로 넣었습니다(획 37개, 약 20KB).
  폰트 윤곽선은 획의 양쪽 테두리라서 따라 그리면 테두리를 도는 모양이 됩니다.
  중심선은 굵기가 일정한 펜 선이라 메인 사진의 글씨와도 결이 맞습니다.
- `path` 마다 `style` 에 대시 길이(`stroke-dasharray`/`stroke-dashoffset`)와 시작 시각(`animation-delay`),
  쓰는 시간(`animation-duration`)이 적혀 있습니다. 펜은 일정한 속도로 움직이고, 획 사이에 0.05초, 줄 사이에 0.15초 쉽니다.
- 획 순서는 왼쪽 끝점에서 시작해 갈림길에서 가장 곧게 이어지는 쪽으로 갑니다. `tt` 가로획처럼 남은 획은 그 뒤에 씁니다.
- 배경음악 안내("배경음악이 준비 되었습니다")는 템플릿이 1.5초 뒤 저절로 닫습니다. 오버레이가 덮은 동안 뜨면
  가려진 채 지나가므로, `index.html` 맨 끝 배경음악 스크립트의 `afterIntro()` 가 오버레이가 다 사라진 뒤에 띄웁니다.
- `prefers-reduced-motion: reduce` 에서는 다 쓴 글씨를 바로 보여 주고 1.5초에 사라지기 시작합니다.
- `#user_wrap` 의 `overflow:hidden` 에 잘리지 않도록 마크업은 `<body>` 바로 아래, `#user_wrap` 앞에 둡니다.
- CSS 위치: 마지막 `<style>` 블록 끝, `/* 첫 화면 오버레이` 주석 아래

### 문구나 속도를 바꿀 때

SVG 는 `tools/intro_write/make.sh` 가 만듭니다. 손으로 고치지 않습니다.

1. `make.sh` 위쪽의 `LINES`(줄 단위 문구), `STROKE_WIDTH`, `WRITE_SECONDS`, `START_DELAY` 를 고칩니다.
2. `./tools/intro_write/make.sh` 를 실행합니다. 맥의 Google Chrome 과 python3 가 필요합니다.
   처음 실행하면 `tools/intro_write/.venv` 에 pillow, numpy, scipy, scikit-image 를 설치하고 WindSong 폰트를 받습니다.
   작업 파일은 `tools/intro_write/out/` 에 생기며 둘 다 `.gitignore` 처리되어 있습니다.
3. 마지막 줄에 찍힌 "마지막 획이 끝나는 시각" 을 확인합니다.
4. `index.html` 의 `<svg class="intro_write">` 블록을 `tools/intro_write/out/intro_write.svg` 로 통째로 바꿉니다.
5. CSS 의 숫자를 맞춥니다.
   - `.intro_overlay` 의 `introFade` 지연은 마지막 획이 끝나는 시각에 1초를 더한 값입니다.
   - `.intro_write path` 의 `stroke-width` 는 `STROKE_WIDTH` 와 같아야 합니다. 대시 길이에 굵기만큼 여유를 두었기 때문입니다.
   - `.intro_write` 의 `width` 는 viewBox 가로 × 0.72(px), viewBox 가로 × 0.185(vw) 중 작은 값입니다.
     글자 크기 72px, 좁은 화면에서는 18.5vw 에 해당합니다.

글자를 PIL 로 직접 그리지 않고 크롬으로 그리는 이유가 있습니다. PIL 은 폰트의 문맥 대체 글자(calt)를 적용하지 않아서
브라우저에서 보이는 WindSong 과 모양이 다릅니다. `tt` 의 긴 가로획과 `g` 의 꼬리가 빠집니다.

## 스크롤 등장 효과

섹션이 아래에서 위로 올라오며 서서히 나타나는 효과입니다. 템플릿의 AOS 를 쓰지 않고
직접 구현했습니다. AOS 는 섹션마다 동작이 달라서 `.section4` 는 아예 숨은 채로 남았고,
그걸 `opacity:1!important` 로 가리느라 애니메이션이 죽어 있었습니다.

동작 방식입니다.

- CSS 로 템플릿의 AOS 상태(`[aos]`, `[data-aos]`, 섹션 자체의 `opacity:0`)를 전부 중립화합니다.
- 자바스크립트가 대상 요소에 `.reveal` 을 붙이고 IntersectionObserver 로 관찰합니다.
  화면에 들어오면 `.is_in` 을 붙이고 관찰을 해제합니다. 한 번만 재생됩니다.
- `.reveal` 을 자바스크립트가 붙이므로, 스크립트가 죽어도 내용이 사라지지 않습니다.
- 대상에서는 `aos` / `data-aos` 속성을 떼서 템플릿 AOS 와 같은 속성을 두고 다투지 않게 합니다.
- `prefers-reduced-motion: reduce` 에서는 효과를 끕니다.

묶음과 지연은 `index.html` 하단 스크립트의 `GROUPS` 배열에서 관리합니다. 한 배열이 한 묶음이고,
배열 안 순서대로 `STEP`(90ms)씩 늦게 나타납니다.

| 묶음 | 대상 |
| --- | --- |
| 인사말 | `.section12 .contents` |
| 신랑·신부 소개 | 이름 / 소개 / 혼주 3단 |
| 예식 안내 | 달력 / 디데이 2단 |
| 오시는 길 | 제목 / 장소 / 지도 / 교통 4단 |
| 사진 | 제목 / 안내문 / 목록 3단 |
| 맺음말 | `.section11 .inner` |

메인 사진(section1)은 첫 화면이라 제외했습니다.

## 하트와 z-index 함정

달력 예식일과 디데이 카운터의 하트는 `::before` 에 `z-index: -1` 로 글자 뒤에 깝니다.
이 구조는 **부모가 쌓임 맥락(stacking context)이 아니면 조상의 배경 뒤로 가라앉아 사라집니다.**

실제로 이 문제를 겪었습니다. 등장 효과가 재생되는 동안에는 부모 `opacity` 가 1 미만이라
쌓임 맥락이 생겨 하트가 보이다가, 전이가 끝나 `opacity: 1` 이 되는 순간 쌓임 맥락이 없어지면서
하트가 사라졌습니다. 숫자는 흰색이라 하트가 없으면 흰 배경에 묻혀 같이 안 보입니다.
증상은 "하트가 잠깐 나왔다가 사라진다" 였습니다.

그래서 하트를 올리는 요소에 `isolation: isolate` 를 줍니다. 이걸 지우면 증상이 돌아옵니다.

- `.section4 .d_day .calc span`
- `.section4 .table_wrap table tbody tr td.active`

`filter: drop-shadow` 를 하트에만 걸기 위해 `::before` 를 쓰는 것이라, 배경을 span 자체에
주는 방식으로는 되돌리기 어렵습니다. span 에 filter 를 걸면 숫자와 Days/Hours 라벨까지
그림자가 번집니다.

## 주의

- `마음 전하실 곳`(section9)에는 계좌번호가 들어갑니다. 커밋 전에 실제 계좌 정보가 포함되는지 확인합니다.
- `qr/` 디렉터리는 `.gitignore`에 있습니다. 추적 대상으로 되돌리지 않습니다.
- 지도 아래 길안내 버튼은 네이버 지도 · 카카오 · 티맵 순서의 동그란 로고 버튼입니다(`index.html` 하단 스크립트의 `venue`).
  - 네이버: 네이버 지도 웹 검색으로 엽니다.
  - 카카오: 카카오내비는 앱키(Kakao SDK) 없이 열 수 없어서 카카오맵 자동차 길찾기 링크(`map.kakao.com/link/to/...`)로 엽니다.
  - 티맵: 웹 길안내가 없어서 `tmap://route` 스킴으로 엽니다. 안드로이드는 `intent://` 로 열어 앱이 없으면 스토어로 보냅니다.
    데스크톱에서는 안내 문구만 띄웁니다.
- `photos/` 사진은 저장소에 커밋합니다. GitHub Pages 가 그대로 서빙합니다. 원본을 그대로 올리지 말고
  긴 변 1600px, 장당 500KB 이하로 줄여서 넣습니다.
- 새 섹션에는 `aos` 속성을 붙이지 않습니다. 이 페이지에서 AOS 애니메이션이 제대로 동작하지 않아
  기존 섹션도 `opacity:1!important` 로 강제해 둔 상태입니다.
