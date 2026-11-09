#!/usr/bin/env bash
# Download the TWC WARN yearly listings into raw/
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p raw
for y in 2020 2021 2022 2023 2024 2025 2026; do
  curl -fsSL -A "Mozilla/5.0" -o "raw/warn-$y.xlsx" \
    "https://www.twc.texas.gov/sites/default/files/oei/docs/warn-act-listings-$y-twc.xlsx"
done
