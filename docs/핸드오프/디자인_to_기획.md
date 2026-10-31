# 디자인 세션 → 기획(시제품) 세션 전달 (2026-10-31)

세션 간 직접 메시지가 막혀(신뢰 기기 확인 필요) 파일로 남깁니다. 기획 세션은 `git fetch origin claude/vibrant-hawking-c60e8c` 후 이 파일과 `마음온/brand/avatar/characters/`를 보면 됩니다.

## 도반 캐릭터 6종 최종본 (컨셉 보드의 동물 친구 다섯 + 심덕이)

| species | 이름 | 특징 |
| --- | --- | --- |
| simdeok | 심덕이 (오리) | 크림 몸, 큰 눈, 주황 부리·물갈퀴, 잔털 3·꽁지깃 3, 회색 승복 |
| deerdeer | 디어디어 (사슴) | 연갈색 몸, 크림 주둥이, 큰 귀, 작은 뿔, 발굽, 따뜻한 회색 승복 |
| fox | 여우 스님 | 주황 몸, 흰 주둥이, 끝이 검은 큰 귀, 염주, 갈색 승복 |
| cat | 고양이 도반 | 회색 몸, 흰 입가, 분홍 코, 수염, 연회색 승복 |
| turtle | 거북이 도반 | 초록 몸, 연두 입가, 걸망 대신 등딱지, 뭉툭한 발, 회녹색 승복 |
| sparrow | 참새 도반 | 갈색 몸, 크림 턱, 주황 부리, 가는 다리·발가락 셋, 연회색 승복 |

- 파일: `characters/maumon-<species>.glb` (원본 2.2~2.4MB) + `maumon-<species>-lite.glb` (정점 약 2.1만, 700KB, 다른 방문자용). `avatar/maumon-duck.glb`·`-lite.glb`는 simdeok와 같은 파일.
- 노드 이름(hips·torso·neck·wingL/R·legL/R·eyeL/R)·피벗·크기가 전부 같아 `blender/duck-glb.js`(MaumDuckGLB) 하나로 6종 모두 걷기·가부좌·연잎 숨쉬기·합장(반배)·큰절이 된다. .gltf.json(base64 BIN) 변환도 지금 방식 그대로.
- 이번 변경: 깃·동정·가방끈·멜빵을 턱 아래 어깨선으로 내려 옷이 턱에서 튀어나오지 않게 함(6종 공통). 심덕이는 눈을 키우고 꽁지깃을 넣음. 이름은 '심덕이'로 확정.
- 소스: `characters/character.py <species> <out> [--no-render]` (Blender 5.2 bpy). 라이트 판: `blender/make_lite.py`. 렌더: `characters/renders/`.
- 뷰어: https://claude.ai/artifact/2WbQLUevXo9ua1ucB9tkQN

## 채택하지 않은 것
사용자분이 받은 trimesh 기반 6종 zip(토끼·곰·판다 포함)은 뼈대 노드 아래에 메시가 매달려 있지 않아 큰절·가부좌가 안 되고, 발이 전부 오리 발이며, 보드의 동물 구성과 달라 채택하지 않았다. 큰 눈·꽁지깃만 심덕이에 반영.

## 요청
- 시제품의 심덕이 GLB를 새 `maumon-simdeok.glb`(+lite)로 교체.
- 나머지 캐릭터는 사용자분이 원할 때 NPC 또는 아바타 선택지로 투입.
