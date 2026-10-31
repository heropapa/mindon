#!/usr/bin/env bash
# 마음온 소개 홈페이지 배포 — 클라우드 세션에서 한 번에
#   bash homepage/deploy.sh
# 필요: CLOUDFLARE_API_TOKEN ("Edit Cloudflare Workers" 템플릿, mindontemple.com 을 가진 계정), CLOUDFLARE_ACCOUNT_ID, Node 20+
set -euo pipefail
cd "$(dirname "$0")"                          # homepage/

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  echo "CLOUDFLARE_API_TOKEN 이 없어요 — 클라우드 환경 설정(Edit)에 넣고 새 세션에서 다시 실행하세요." >&2
  exit 1
fi

npx --yes wrangler@4 whoami
npx --yes wrangler@4 deploy 2>&1 | tee /tmp/mindontemple-deploy.log

echo
echo "주소: https://mindontemple.com   (처음 붙일 때 인증서 발급에 몇 분 걸릴 수 있음)"
echo "확인: curl -sI https://mindontemple.com | head -1"
