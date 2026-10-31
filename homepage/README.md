# homepage — mindontemple.com 소개 페이지

`mindontemple.com`은 마음온(MindOn)을 처음 보는 사람에게 어떤 곳인지 보여 주는 **소개 페이지**예요 (본부장 결정, 2026-10-31). 실제 명상 사찰은 `https://mindon.link`이고, 소개를 끝까지 본 뒤 맨 아래 "마음온 들어가기"로만 들어가요.

- 담당: 소개 페이지 세션 (`session_01WfU8g7xJvFvkaEuW8pzZme`)
- 이 폴더만 씁니다. `prototype/`·`server/`·`brand/`는 읽기만 합니다.
- 2026-10-31 `heropapa/my_automation`의 `마음온/intro/`(PR #17)에서 옮겨 왔어요.

## 파일

| 경로 | 내용 |
|---|---|
| `site/index.html` | 소개 페이지 한 장. 한국어·English 전환, 모바일 우선, 3D 없음. 스타일·스크립트가 모두 이 파일 안에 있음 |
| `site/assets/mindon-*.svg` | `brand/logo/`의 같은 파일을 복사 (배포 사이트가 작업 저장소·Pages에 기대지 않게). 원본이 바뀌면 같이 바꿀 것 |
| `site/assets/img/` | 경내 스크린숏(webp), 컨셉 보드 「심덕」에서 자른 심덕이 대표 그림·도반 친구들, 공유 이미지 `og.jpg` |
| `site/404.html`, `robots.txt`, `sitemap.xml` | 없는 주소 안내, 검색 허용 |
| `wrangler.toml` | 정적 파일만 내는 Worker `mindontemple-site`, 커스텀 도메인 `mindontemple.com`·`www.mindontemple.com` (배포 때 DNS·인증서 자동, DNS 레코드를 손으로 만들지 말 것) |
| `deploy.sh` | 배포 한 번에: `bash homepage/deploy.sh` (환경 변수 `CLOUDFLARE_API_TOKEN`·`CLOUDFLARE_ACCOUNT_ID` 필요) |

## 내용 원칙 (기획 세션 정리, 2026-10-31)

- 이름 **마음온 · MindOn**, 부제 "마음이 쉬어가는 절 · a quiet temple online". 한자·종단 상징 없음.
- 넣지 않는 것: 결제·후원·가격·출시일, "AI 스님/부처님", 다른 서비스 비교, 사람 수 부풀리기. 영인스님 염불은 이 페이지에서 틀거나 내려받게 하지 않음.
- 준비 중으로만 소개: 도반 고르기(여우 스님·고양이·사슴·거북이·참새), 연등 마당, 찻방, 연등 달기·기와쓰기, **마음 길잡이(AI 대화)** — 답하는 방식·안전 약속·예시 대화.
- 꼭 넣는 것: 안전 고지(109·1577-0199), 운영자(에이톤, 대표 임지현, atone@kakao.com), 개인정보·약관·출처 링크(mindon.link), 불상·불화 출처.
- "지금 n명이 경내에 있어요"는 `https://mindon.link/stats`의 `online_now` 실제 값. 0이면 "지금은 조용한 시간이에요".
- 들어가기 버튼은 `https://mindon.link/?lang=ko|en`. 쿠키·방문 분석 없음.

## 연락

다른 세션에 보낼 일은 `docs/핸드오프/`에 파일로 남기거나 이 폴더를 고치는 PR에 댓글로 남깁니다.
