#!/usr/bin/env bash
# Regenerate study screenshots with headless Chromium (deterministic: motion off).
#   bash design/observatory/shoot.sh
set -euo pipefail
cd "$(dirname "$0")"
node build.mjs
out=screenshots; mkdir -p "$out"
url="file://$PWD/index.html"
shot() { chromium --headless=new --disable-gpu --hide-scrollbars --window-size="$2" \
  --virtual-time-budget=3000 --screenshot="$out/$1.png" "$url#$3&motion=off" >/dev/null 2>&1; echo "$out/$1.png"; }
D=1440,1000; M=390,1000
for s in d a b c; do
  shot "desktop-$s-quiet"   $D "study=$s&state=quiet&view=map"
  shot "desktop-$s-replay"  $D "study=$s&state=replay&pos=11"
done
shot desktop-d-overlap $D "study=d&state=overlap&view=map&sel=pr:22"
shot desktop-d-list-overlap $D "study=d&state=overlap&view=list&sel=branch:voice-notes"
shot mobile-d-overlap $M "study=d&state=overlap&view=map"
shot mobile-d-quiet $M "study=d&state=quiet&view=map"
shot desktop-a-overlap $D "study=a&state=overlap&view=map&sel=pr:21"
shot desktop-b-overlap $D "study=b&state=overlap&view=map&sel=pr:22"
shot desktop-c-overlap $D "study=c&state=overlap&view=map&sel=overlap:pr:21|pr:22"
shot desktop-b-list-overlap $D "study=b&state=overlap&view=list&sel=branch:voice-notes"
shot desktop-c-overlap-paper $D "study=c&state=overlap&view=map&theme=paper"
shot desktop-sheet 1440,2300 "study=a&state=overlap&view=map"
shot desktop-d-sheet 1440,2100 "study=d&state=overlap&view=map"
shot mobile-a-overlap $M "study=a&state=overlap&view=map"
shot mobile-b-overlap-inspector $M "study=b&state=overlap&view=list&sel=pr:22"
shot mobile-c-overlap-inspector $M "study=c&state=overlap&view=map&sel=pr:22"
shot mobile-c-replay $M "study=c&state=replay&pos=11"
