# 마음온 에셋 (Maum On assets)

마음온(온라인 명상 사찰)의 브랜드·캐릭터 에셋 저장소. 작업자는 이 저장소를 `git pull` 해서 최신 파일을 받고, 자기 작업은 PR로 올린다.

| 폴더 | 내용 |
| --- | --- |
| `brand/logo/` | 붓글씨 전원 마크(먹·한지·금), 낙관 인장, 파비콘 SVG |
| `brand/tokens.json` | 색·글꼴·간격·모서리·그림자·동작 토큰 |
| `brand/icons/` | 행동 바·패널용 선 아이콘 14개 + sprite.svg |
| `characters/` | 심덕이와 도반 친구들 GLB (원본 `maumon-<species>.glb`, 라이트 `-lite.glb`), 렌더, Blender 소스 |
| `loader/` | `duck-glb.js` (three.js r128 로더·동작 제어), `viewer.html` (확인용 뷰어), `duck.js` (도형 폴백) |
| `docs/` | 디자인 시스템 브랜드북, 경내 아트 디렉션, **모델링 규격서**, 핸드오프 메모 |
| `site/` | 캐릭터 시트(index.html)와 규격서(spec.html) 웹페이지 |

## 모델링 작업자는 먼저
1. `docs/모델링_규격서.md` 를 읽는다 (노드 이름·피벗·생김새·용량·검수 체크리스트).
2. `loader/viewer.html` 과 같은 폴더에 GLB를 두고 `python -m http.server` 로 열어 여섯 동작을 확인한다.
3. 납품은 `characters/` 규칙대로 파일 이름을 맞춰 PR로 올린다.

## 로더 사용
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script src="loader/duck-glb.js"></script>
```
```js
const duck = new MaumDuckGLB('characters/maumon-simdeok.glb', d => scene.add(d.root));
duck.setPose('stand' | 'walk' | 'sit' | 'breathe' | 'hapjang' | 'bow', instant?, onDone?);
duck.update(dt); // 매 프레임, 초 단위
```

## 문서 링크 (아티팩트, 공유 설정 후 열림)
- 디자인 시스템: https://claude.ai/artifact/BruQXcFyFpAWnVX2iwvPsJ
- 캐릭터 시트·뷰어: https://claude.ai/artifact/2WbQLUevXo9ua1ucB9tkQN
- 모델링 규격서: https://claude.ai/artifact/FBbSs1puLa8vyLK47XPp4H

기준은 언제나 컨셉 보드 「심덕」이다. 문서와 보드가 다르면 보드가 맞다.
