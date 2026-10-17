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
index.html   # 전체 청첩장 (HTML + CSS + JS + base64 이미지, 약 20MB / 12,700줄)
qr/          # QR 이미지 (.gitignore 처리, 저장소에 포함하지 않음)
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

인사말(section12), 신랑·신부 소개(section3), 예식 안내·캘린더(section4), 오시는 길(section6).

### 현재 꺼져 있는 섹션

시(section2), 웨딩 인터뷰(section14), 게스트스냅(section19), 갤러리(section5), 타임라인(section18), 공지(section17), 안내(section7), 참석 여부(section8), 마음 전하실 곳(section9), 방명록(section10), 첫 방문(section13).

## 주의

- `마음 전하실 곳`(section9)에는 계좌번호가 들어갑니다. 커밋 전에 실제 계좌 정보가 포함되는지 확인합니다.
- `qr/` 디렉터리는 `.gitignore`에 있습니다. 추적 대상으로 되돌리지 않습니다.
- 지도 버튼은 TMap·카카오내비를 숨기고 네이버 지도 검색으로만 연결합니다(`index.html` 하단 스크립트).
