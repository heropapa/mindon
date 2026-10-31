# 도메인 세션 → 디자인 세션 전달 (2026-10-31)

「저장소 이전 안내」 §3 도메인 담당 항목에 대한 답입니다. 세션 간 직접 메시지가 막혀 파일로 남깁니다. 상세는 `docs/도메인.md`.

## 공식 주소 (본부장 확정, 2026-10-31) — `index.html` 안내문에 반영해 주세요

| 용도 | 주소 | 비고 |
|---|---|---|
| 서비스 (3D 명상 사찰) | **https://mindon.link** | 운영 중. Cloudflare Worker `maumon` |
| 소개 홈페이지 | **https://mindontemple.com** | **바로 공개** (본부장 지시 2026-10-31) — 소개페이지 세션이 배포 중. 안내문엔 "준비 중" 표시 없이 링크 |
| 작업자 문서 (안내문·규격서·캐릭터 시트) | **https://heropapa.github.io/mindon/** | **그대로 씀.** `docs.mindon.link` 같은 하위 도메인은 붙이지 않음 (본부장 결정) |

## 배포 스크립트 경로 확인

- `tools/deploy.sh`·`tools/build_dist.py`는 스크립트 위치 기준 상대 경로라 새 저장소에서도 그대로 동작합니다 (`prototype/` → `dist/`, `server/wrangler.toml` `[assets] = ../dist`).
- 사용법 주석과 `docs/출시_체크리스트.md`에 남아 있던 옛 경로 `마음온/tools/…`·`마음온/server/…`를 `tools/…`·`server/…`로 고쳤습니다 (PR #2).
- 출시 체크리스트의 배포 요청 문구도 "브랜치 ccr-4d7b3fd2-vyot4n"에서 "저장소 heropapa/mindon main"으로 바꿨습니다.
- `docs/디자인시스템.md` 8행에도 `마음온/…` 경로가 있는데, 디자인 세션 문서라 건드리지 않았습니다.
