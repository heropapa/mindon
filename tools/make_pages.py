"""마음온 안내 페이지(출처·개인정보처리방침·이용약관)를 prototype/ 에 만든다.
출처 페이지는 prototype/CREDITS.md 의 표를 그대로 옮긴다. CREDITS.md 를 고치면 다시 실행:
    python3 tools/make_pages.py
운영자 정보는 아래 기본값(2026-10-30 본부장 제공)으로 채워짐 — 바뀌면 기본값을 고치거나 --operator 등으로 덮어씀.
"""
import argparse, html, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent / 'prototype'

STYLE = """
:root { --ink: #121419; --paper: #f1eadc; --dim: rgba(241,234,220,.68); --line: rgba(241,234,220,.16); --gold: #d7b25b; color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--ink); color: var(--paper); font: 15px/1.7 "Gowun Dodum", "Apple SD Gothic Neo", "Malgun Gothic", system-ui, sans-serif; }
main { max-width: 760px; margin: 0 auto; padding: 32px 16px 64px; }
h1 { font-family: "Gowun Batang", serif; font-size: 26px; margin: 0 0 4px; }
h2 { font-family: "Gowun Batang", serif; font-size: 19px; margin: 32px 0 8px; }
h3 { font-size: 16px; margin: 20px 0 4px; }
p, li { color: var(--paper); } .dim, small { color: var(--dim); }
a { color: var(--gold); word-break: break-all; }
.back { display: inline-block; margin-bottom: 20px; text-decoration: none; }
.tbl { overflow-x: auto; } table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { border-bottom: 1px solid var(--line); padding: 8px 6px; text-align: left; vertical-align: top; } th { color: var(--dim); font-weight: 400; }
.todo { background: rgba(215,178,91,.15); border-radius: 4px; padding: 0 4px; }
.box { border: 1px solid var(--line); border-radius: 12px; padding: 12px 16px; margin: 16px 0; }
hr { border: 0; border-top: 1px solid var(--line); margin: 40px 0; }
"""

def page(title, body):
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · 마음온</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gowun+Batang:wght@700&family=Gowun+Dodum&display=swap">
<style>{STYLE}</style></head>
<body><main>
<a class="back" href="./">← 마음온으로 돌아가기 · Back to MindOn</a>
{body}
</main></body></html>
"""

def md_inline(t):
    t = html.escape(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    t = re.sub(r'(https?://[^\s|<]+)', r'<a href="\1" rel="noopener">원문</a>', t)
    return t

def credits():
    lines = (ROOT / 'CREDITS.md').read_text(encoding='utf-8').splitlines()
    out, rows = [], []
    def flush():
        if rows:
            head, *data = rows
            out.append('<div class="tbl"><table><tr>' + ''.join(f'<th>{md_inline(c)}</th>' for c in head) + '</tr>')
            out.extend('<tr>' + ''.join(f'<td>{md_inline(c)}</td>' for c in r) + '</tr>' for r in data)
            out.append('</table></div>'); rows.clear()
    for ln in lines:
        if ln.startswith('|'):
            cells = [c.strip() for c in ln.strip('|').split('|')]
            if not all(re.fullmatch(r'-+', c) for c in cells): rows.append(cells)
            continue
        flush()
        if ln.startswith('# '): out.append(f'<h1>출처 · Credits</h1><p class="dim">마음온에 쓰인 소리·그림·3D·글꼴·코드의 출처입니다. 출처 표기가 이용 조건인 저작물이 있어 모두 밝힙니다. Sources of the sounds, images, 3D models, fonts and code used in MindOn.</p>')
        elif ln.startswith('## '): out.append(f'<h2>{md_inline(ln[3:])}</h2>')
        elif ln.strip(): out.append(f'<p class="dim">{md_inline(ln)}</p>')
    flush()
    return page('출처', '\n'.join(out))

PRIVACY = """
<h1>개인정보처리방침</h1>
<p class="dim">시행일: <span class="todo">[YYYY-MM-DD]</span> · 운영: <span class="todo">[운영자 이름/상호]</span></p>
<div class="box">요약: 마음온은 <strong>회원가입 없이</strong> 이용하며, 이름·연락처 같은 개인정보를 받지 않습니다. 기록은 내 기기에만 저장됩니다.</div>

<h2>1. 받는 정보와 쓰는 곳</h2>
<ul>
  <li><strong>내 기기에만 저장되는 기록</strong> — 오늘 절한 수·명상 시간, 소리 크기, 조이스틱 위치, 익명 이름 번호. 브라우저 저장 공간(localStorage)에만 있고 서버로 보내지 않습니다. 브라우저 기록을 지우면 사라집니다.</li>
  <li><strong>함께 있기</strong> — 접속하는 동안 내 오리의 위치·방향·동작(걷기·합장·절 등)과 <strong>익명 이름</strong>을 같은 방에 있는 사람들에게 실시간으로 보냅니다. 익명 이름은 자연에서 따온 108개 이름(예: 작은산새) 중 하나가 무작위로 정해지며, 실명·연락처는 받지 않습니다. 같은 방 사람이 합장하면 그 익명 이름으로 소식이 뜹니다. 저장하지 않고, 나가면 바로 사라집니다.</li>
  <li><strong>입장 통계</strong> — ‘마음 켜기’로 들어온 횟수와 동시에 함께 있는 사람 수를 숫자로만 셉니다. 누구인지는 알 수 없습니다.</li>
  <li><strong>접속 기록</strong> — 서비스를 안전하게 운영하기 위해 서버(Cloudflare)가 IP 주소·접속 시간·브라우저 정보를 보안 목적으로 잠시 처리할 수 있습니다.</li>
  <li><strong>방문 통계</strong> — Cloudflare Web Analytics로 방문 수·머문 시간 같은 통계를 봅니다. 쿠키를 쓰지 않고 개인을 알아보지 않습니다.</li>
</ul>

<h2>2. 처리를 맡기는 곳</h2>
<ul>
  <li>Cloudflare, Inc. — 웹 호스팅, 실시간 서버, 방문 통계</li>
  <li>Google Fonts — 글꼴 전송 (글꼴을 받을 때 IP 주소가 전달될 수 있음)</li>
  <li>cdnjs · jsDelivr — 화면에 쓰는 공개 코드 전송</li>
</ul>
<p>개인정보를 다른 곳에 팔거나 넘기지 않습니다.</p>

<h2>3. 보관 기간</h2>
<p>기기 기록은 내 기기에만 있으며 직접 지울 수 있습니다. 함께 있기 정보는 저장하지 않습니다. 접속 기록은 해당 서비스의 보관 기간을 따릅니다.</p>

<h2>4. 아동</h2>
<p>마음온은 개인정보를 받지 않으므로 나이를 묻지 않습니다.</p>

<h2>5. 유료 기능</h2>
<p>앞으로 유료 회원·연등 달기 같은 기능을 열면, 결제와 로그인에 필요한 최소한의 정보만 받고 그 전에 이 방침을 고쳐 알립니다.</p>

<h2>6. 문의 · 개인정보 보호책임자</h2>
<p><span class="todo">[이름]</span> · <span class="todo">[이메일]</span></p>

<hr>
<h1>Privacy Policy</h1>
<p class="dim">Effective: <span class="todo">[YYYY-MM-DD]</span> · Operator: <span class="todo">[name]</span></p>
<div class="box">In short: MindOn needs <strong>no sign-up</strong> and does not collect names or contact details. Your records stay on your device.</div>
<ul>
  <li><strong>On-device records</strong> — today's bows and meditation minutes, sound levels, joystick position and your anonymous name number are kept in your browser's localStorage only. Nothing is sent to our servers.</li>
  <li><strong>Being together</strong> — while you are here, your duck's position, direction and motion, and an <strong>anonymous name</strong> (one of 108 nature names, e.g. Little Mountain Bird, picked at random) are shared live with people in the same room. We never ask for your real name or contact details. When someone in your room joins palms, others see a short note with that anonymous name. Nothing is stored, and it disappears when you leave.</li>
  <li><strong>Visit counts</strong> — we count how many times people enter and how many are here at once, as numbers only. We cannot tell who you are.</li>
  <li><strong>Access logs</strong> — our host (Cloudflare) may briefly process IP address, time and browser information for security.</li>
  <li><strong>Analytics</strong> — Cloudflare Web Analytics, cookie-free and not used to identify you.</li>
  <li><strong>Processors</strong> — Cloudflare (hosting, realtime, analytics), Google Fonts (fonts; your IP may reach Google), cdnjs and jsDelivr (public code). We never sell your data.</li>
  <li>Paid features in the future will collect only what payment and login require, and this policy will be updated first.</li>
  <li>Contact: <span class="todo">[email]</span></li>
</ul>
"""

TERMS = """
<h1>이용약관</h1>
<p class="dim">시행일: <span class="todo">[YYYY-MM-DD]</span> · 운영: <span class="todo">[운영자 이름/상호]</span></p>

<div class="box"><strong>마음온은 의료·심리치료를 대신하지 않습니다.</strong><br>
마음이 많이 힘들거나 스스로를 해치고 싶은 생각이 들면 바로 도움을 받으세요.<br>
자살예방상담 <strong>109</strong> · 정신건강위기상담 <strong>1577-0199</strong> (24시간) · 위급하면 <strong>112 / 119</strong></div>

<h2>1. 서비스</h2>
<p>마음온은 온라인 3D 경내를 걷고, 염불을 듣고, 합장·108배·연잎 명상을 하는 쉼의 공간입니다. 지금 모든 기능은 무료이며 회원가입 없이 이용합니다.</p>

<h2>2. 함께 있기</h2>
<p>같은 방에 있는 사람들의 오리가 서로 보입니다. 다른 사람을 방해하거나 서비스를 해치는 행동(자동 프로그램 접속, 과도한 요청 등)은 하지 마세요. 그런 경우 접속이 제한될 수 있습니다.</p>

<h2>3. 콘텐츠와 출처</h2>
<p>염불·자연 소리·불상·불화 등은 공유 저작물을 이용 조건에 따라 쓰고 있으며, <a href="credits.html">출처</a>에 모두 밝힙니다. 마음온의 화면·캐릭터·코드의 권리는 운영자에게 있습니다.</p>

<h2>4. 서비스 변경·중단</h2>
<p>더 나은 서비스를 위해 내용이 바뀌거나, 점검·장애로 잠시 멈출 수 있습니다. 중요한 변경은 미리 알립니다.</p>

<h2>5. 책임</h2>
<p>마음온은 쉼과 명상을 돕는 공간이며, 이용 결과에 대해 의학적·법적 보증을 하지 않습니다. 운영자의 고의·중과실이 없는 한 서비스 이용으로 생긴 손해에 책임을 지지 않습니다.</p>

<h2>6. 유료 기능</h2>
<p>앞으로 유료 기능을 열면 가격·환불 기준을 이 약관에 더하고 미리 알립니다.</p>

<h2>7. 문의 · 준거법</h2>
<p>문의: <span class="todo">[이메일]</span> · 이 약관은 대한민국 법을 따릅니다.</p>

<hr>
<h1>Terms of Use</h1>
<div class="box"><strong>MindOn is not a substitute for medical or psychological care.</strong> If you are struggling or thinking of harming yourself, please reach out now: in Korea call <strong>109</strong> or <strong>1577-0199</strong> (24h), or <strong>112 / 119</strong> in an emergency. Elsewhere, contact your local crisis line.</div>
<ul>
  <li>MindOn is a free, sign-up-free space to walk a 3D temple, listen to chanting, and practise palms together, 108 bows and lotus-leaf breathing.</li>
  <li>Ducks of people in the same room are visible to each other. Do not disturb others or abuse the service (bots, excessive requests); access may be limited.</li>
  <li>Sounds and artworks are used under their licences and credited on the <a href="credits.html">Credits</a> page.</li>
  <li>The service may change or pause for maintenance. MindOn gives no medical or legal guarantee.</li>
  <li>Governing law: Republic of Korea. Contact: <span class="todo">[email]</span></li>
</ul>
"""

ap = argparse.ArgumentParser()
ap.add_argument('--operator', default='에이톤(대표 임지현)')            # 운영(상호·대표) — 한글 페이지
ap.add_argument('--operator-en', default='A-Tone (에이톤), 임지현')     # 영문 페이지의 Operator
ap.add_argument('--officer', default='임지현')                         # 개인정보 보호책임자
ap.add_argument('--email', default='atone@kakao.com')
ap.add_argument('--date', default='2026-10-31')                        # 시행일 (출시일)
args = ap.parse_args()

def fill(t):
    todo = lambda k: r'<span class="todo">\[' + k + r'\]</span>'
    if args.operator:
        t = re.sub(todo('운영자 이름/상호'), lambda m: html.escape(args.operator), t)
        t = re.sub(todo('name'), lambda m: html.escape(args.operator_en or args.operator), t)
        t = re.sub(todo('이름'), lambda m: html.escape(args.officer or args.operator), t)
    if args.email:
        e = html.escape(args.email); t = re.sub(todo(r'(이메일|email)'), lambda m: f'<a href="mailto:{e}">{e}</a>', t)
    if args.date:
        t = re.sub(todo('YYYY-MM-DD'), lambda m: html.escape(args.date), t)
    return t

for name, content in [('credits.html', credits()), ('privacy.html', page('개인정보처리방침', PRIVACY)), ('terms.html', page('이용약관', TERMS))]:
    content = fill(content)
    (ROOT / name).write_text(content, encoding='utf-8')
    left = content.count('class="todo"')
    print('wrote', name, f'(빈칸 {left}개 남음)' if left else '')
