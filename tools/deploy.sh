#!/usr/bin/env bash
# 마음온 배포 — 클라우드 세션에서 한 번에 (토큰은 환경 설정에 넣어 둔 것을 읽음, 채팅에 붙여 넣지 않음)
#   bash 마음온/tools/deploy.sh                 # 정식 주소 https://mindon.link 로 빌드·배포 (커스텀 도메인은 wrangler.toml routes 로 자동 연결)
#   bash 마음온/tools/deploy.sh <다른 주소>      # 공유 미리보기 주소를 다르게 (예: workers.dev 로만 시험할 때)
# 필요: CLOUDFLARE_API_TOKEN ("Edit Cloudflare Workers" 템플릿), CLOUDFLARE_ACCOUNT_ID, Node 20+, Python 3
set -euo pipefail
cd "$(dirname "$0")/.."                       # 마음온/
SITE="${1:-https://mindon.link}"

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  echo "CLOUDFLARE_API_TOKEN 이 없어요 — 클라우드 환경 설정(Edit)에 넣고 새 세션에서 다시 실행하세요." >&2
  exit 1
fi
[ -n "${CLOUDFLARE_ACCOUNT_ID:-}" ] || echo "참고: CLOUDFLARE_ACCOUNT_ID 가 없어요 — 계정이 하나면 wrangler 가 알아서 찾음"

build() { python3 tools/build_dist.py ${1:+--site "$1"}; }
deploy() { (cd server && npx wrangler deploy 2>&1) | tee /tmp/mindon-deploy.log; }

build "$SITE"
(cd server && npm install --no-audit --no-fund --loglevel=error)
(cd server && npx wrangler whoami)
deploy

URL=$(grep -oE 'https://[a-z0-9.-]+\.workers\.dev' /tmp/mindon-deploy.log | head -1 || true)
echo
echo "정식 주소: $SITE   (처음 붙일 때 인증서 발급에 몇 분 걸릴 수 있음)"
echo "비상 주소: ${URL:-(workers.dev 주소는 deploy 출력 참고)}"
echo "확인: node tools/check_live.mjs $SITE   (안 되면 몇 분 뒤 다시, 그동안 node tools/check_live.mjs $URL)"
