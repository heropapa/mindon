# 기획(시제품) 세션 안내 — 저장소 통합 (2026-10-31)

사용자 결정으로 마음온 작업을 **저장소 하나(`heropapa/mindon`, 옛 이름 maumon-assets)**로 통일한다. 영문 이름은 **MindOn**(한 단어)으로 확정. "Maum On" 표기는 쓰지 않는다.

- `prototype/` `server/` `tools/` `vendor/` `docs/기획서.md` 등은 `my_automation` 브랜치 `ccr-4d7b3fd2-vyot4n`의 `마음온/`에서 그대로 가져왔다(2026-10-31 시점). 그 뒤 바뀐 것이 있으면 여기에 다시 올려 달라.
- 브랜드·캐릭터 파일 접두어가 `maumon-` → `mindon-`으로 바뀌었다 (`characters/mindon-simdeok.glb` 등). 시제품에서 쓰는 .gltf.json 변환본도 이름만 맞춰 주면 된다.
- 로더 `loader/duck-glb.js`는 그대로. `MindOnDuck`이라는 별칭을 추가했다(`MaumDuckGLB`와 같음).
- 앞으로 시제품 작업은 이 저장소에서 새 세션을 열어 진행한다. `my_automation`의 `마음온/`은 더 이상 갱신하지 않는다.
- 워드마크는 "마음온 · MindOn". 패널·현판의 영문 병기도 MindOn 기준.
