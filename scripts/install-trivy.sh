#!/bin/sh
# Install a fixed Trivy release, verified by SHA-256 before it ever runs.
# No floating install script and no third-party GitHub Action.
set -eu
version=0.75.0
checksum=c6e65abddb348e25f10549df887045629cf28cc72453cd1c63acb717316b3f3f
[ "$(uname -s)-$(uname -m)" = Linux-x86_64 ] || { echo 'Scanner install supports Linux x86_64 only' >&2; exit 1; }
destination="${TRIVY_BIN_DIR:-.tools/trivy}"
mkdir -p "$destination"
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
asset="trivy_${version}_Linux-64bit.tar.gz"
curl --fail --location --silent --show-error --retry 3 --max-time 180 \
  "https://github.com/aquasecurity/trivy/releases/download/v${version}/${asset}" \
  -o "$temporary/$asset"
printf '%s  %s\n' "$checksum" "$temporary/$asset" | sha256sum --check
tar -xzf "$temporary/$asset" -C "$destination" trivy
"$destination/trivy" --version
