#!/usr/bin/env bash
# Download and install Pastel Spectrum, including its terminal styling.
set -euo pipefail
for dependency in git python3; do
  if ! command -v "$dependency" >/dev/null 2>&1; then
    echo "Required command missing: $dependency" >&2
    exit 1
  fi
done
if ! command -v omarchy >/dev/null 2>&1 && [[ " $* " != *" --no-apply "* ]]; then
  echo 'Pastel Spectrum requires Omarchy.' >&2
  exit 1
fi
pastel_download_dir=$(mktemp -d)
trap 'rm -rf -- "$pastel_download_dir"' EXIT
git clone --quiet --depth 1 https://github.com/stspivey76-byte/omarchy-pastel-spectrum.git "$pastel_download_dir/project"
bash "$pastel_download_dir/project/install.sh" --terminal "$@"
