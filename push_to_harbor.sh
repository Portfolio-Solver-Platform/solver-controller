#!/usr/bin/env bash
HARBOR_URL="${HARBOR_URL:-harbor.local}"

REF="$HARBOR_URL/psp/solver-controller"

docker logout $HARBOR_URL || true
docker login $HARBOR_URL -u admin -p admin

docker build -t solver-controller:latest .
docker tag solver-controller:latest $HARBOR_URL/psp/solver-controller:latest
PUSH_OUT="$(docker push "$REF:latest" 2>&1 | tee /dev/stderr)"
