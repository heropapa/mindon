"""마음온 배포 폴더 만들기 — prototype/ → dist/ (Cloudflare Pages에 그대로 올림).

prototype/index.html 은 아티팩트 형식(doctype·head 없음)이라 여기서 감싼다.
  python3 마음온/tools/build_dist.py --site https://mindon.link
--site 는 공유 미리보기(og:image)에 쓸 실제 주소. 모르면 비워 두고 나중에 다시 만든다.
"""
import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "prototype"
DIST = ROOT / "dist"

COPY_DIRS = ["audio", "avatar", "buddha", "img"]
# three.js 와 로더는 CDN 대신 우리 서버에서 (CDN 이 느리거나 막혀도 뜨게 — 아티팩트는 그대로 CDN)
VENDOR = ROOT / "vendor"
CDN_TO_LOCAL = {
    "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js": "vendor/three.min.js",
    "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js": "vendor/GLTFLoader.js",
    "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/libs/meshopt_decoder.js": "vendor/meshopt_decoder.js",
}
COPY_FILES = ["privacy.html", "terms.html", "credits.html", "admin.html"]   # admin = 관리자 운영 현황 (검색 제외)

TITLE = "마음온 MindOn · 마음이 쉬어가는 절"
DESC = ("걸어 다니며 소리를 듣고, 합장하고, 108배와 연잎 숨쉬기를 하는 온라인 명상 절. "
        "A quiet temple online — walk, listen, bow and breathe.")

# 배포 서버가 붙이는 보안·캐시 헤더 (Cloudflare Pages `_headers` 형식)
HEADERS = """/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()

/audio/*
  Cache-Control: public, max-age=604800
/avatar/*
  Cache-Control: public, max-age=86400, stale-while-revalidate=604800
/buddha/*
  Cache-Control: public, max-age=86400, stale-while-revalidate=604800
/img/*
  Cache-Control: public, max-age=86400, stale-while-revalidate=604800
/vendor/*
  Cache-Control: public, max-age=2592000, immutable
"""
# 파일 이름에 버전이 없어서 오래 묵히지 않는다: 고친 모델·그림은 하루 안에 퍼짐 (소리는 안 바뀌어 일주일)

ROBOTS = "User-agent: *\nAllow: /\n"


def head(site: str, body_title: str) -> str:
    og_img = f"{site}/img/og.jpg" if site else "img/og.jpg"
    url = f'<meta property="og:url" content="{site}/">\n<link rel="canonical" href="{site}/">\n' if site else ""
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{body_title}</title>
<meta name="description" content="{DESC}">
<meta name="theme-color" content="#121419">
<meta name="maumon:ws" content="/ws">
<meta property="og:type" content="website">
<meta property="og:site_name" content="마음온 MindOn">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
{url}<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{DESC}">
<meta name="twitter:image" content="{og_img}">
<style>html,body{{margin:0;height:100%;background:#121419}}</style>
</head>
<body>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="", help="배포 주소 (예: https://mindon.link)")
    site = ap.parse_args().site.rstrip("/")

    # 폴더는 두고 안만 비운다 (wrangler dev 가 지켜보는 폴더가 사라지지 않게)
    DIST.mkdir(exist_ok=True)
    for c in DIST.iterdir():
        shutil.rmtree(c) if c.is_dir() else c.unlink()

    page = (SRC / "index.html").read_text(encoding="utf-8")
    m = re.match(r"\s*<title>(.*?)</title>\s*", page)
    body_title = TITLE
    if m:  # 아티팩트용 <title> 은 head 로 바꿔 넣는다
        page = page[m.end():]
    # 맨 앞의 <meta>·<link>(아이콘·글꼴)는 head 로 옮기고, 아티팩트 전용 meta 는 뺀다
    lead = []
    while True:
        m = re.match(r"\s*(<(?:meta|link)\b[^>]*>)", page)
        if not m:
            break
        if "claude:" not in m.group(1):
            lead.append(m.group(1))
        page = page[m.end():]
    for cdn, local in CDN_TO_LOCAL.items():
        assert cdn in page, f"index.html 에 {cdn} 이 없음 — CDN_TO_LOCAL 을 맞출 것"
        page = page.replace(cdn, local)
    html = head(site, body_title).replace("</head>", "\n".join(lead) + "\n</head>")
    (DIST / "index.html").write_text(html + page.lstrip() + "\n</body>\n</html>\n", encoding="utf-8")

    for d in COPY_DIRS:
        shutil.copytree(SRC / d, DIST / d)
    shutil.copytree(VENDOR, DIST / "vendor")
    for f in COPY_FILES:
        shutil.copy2(SRC / f, DIST / f)
    (DIST / "_headers").write_text(HEADERS, encoding="utf-8")
    (DIST / "robots.txt").write_text(ROBOTS, encoding="utf-8")

    total = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file())
    count = sum(1 for p in DIST.rglob("*") if p.is_file())
    print(f"dist/ 완성: 파일 {count}개, {total / 1e6:.1f}MB"
          + ("" if site else "  (--site 없음: og:image 가 상대 주소)"))


if __name__ == "__main__":
    main()
