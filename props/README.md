# 소품 (props)

| 파일 | 내용 | 노드 | 크기 |
| --- | --- | --- | --- |
| `mindon-pungyeong.glb` | 불이문 처마 풍경(風磬): 청동 종(녹 띠) + 추 + 사슬 + 놋쇠 물고기 바람판 | `pung_bell`(원점 = 맨 위 고리, 피벗) → 자식 `pung_fish`(종 아래 고리, 로컬 (0, −0.30, 0)) | 높이 0.61 m, 종 지름 0.22 m, 삼각형 2,496, 58 KB |

- 단위 m, Y 위, 앞 −Z(캐릭터 규격과 같음). 텍스처 없음, 재질 색만(청동 #7a6442 metallic 0.75 / 녹 #6f8a78 / 놋쇠 #b08d52 / 추 #3a3128).
- 흔들림은 코드에서: `pung_bell.rotation`(x·z 소폭, 느린 박자)과 `pung_fish.rotation`(더 큰 폭, 빠른 박자)을 따로 준다. 예: bell x = 0.05·sin(t·1.1), fish z = 0.25·sin(t·2.3)+0.08·sin(t·5.1).
- 소스: `src/build_pungyeong.py` (Blender 5.2 bpy). `python3 build_pungyeong.py <out> [--no-render]`.
