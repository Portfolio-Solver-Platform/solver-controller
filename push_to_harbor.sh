#!/usr/bin/env bash
HARBOR_URL="${HARBOR_URL:-harbor.local}"
export COSIGN_PASSWORD="lol" # Disclaimer only used for local testing
META="$(mktemp)"

REF="$HARBOR_URL/psp/solver-controller"

docker logout $HARBOR_URL || true
docker login $HARBOR_URL -u admin -p admin

docker build -t solver-controller:latest .
docker tag solver-controller:latest $HARBOR_URL/psp/solver-controller:latest
PUSH_OUT="$(docker push "$REF:latest" 2>&1 | tee /dev/stderr)"
DIGEST="$(printf "%s\n" "$PUSH_OUT" | awk '/digest:/ {print $3}')"


cosign sign --key cosign-dev.key "$REF@$DIGEST" -y


