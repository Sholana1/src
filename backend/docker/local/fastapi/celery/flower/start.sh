#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

FLOWER_CMD="celery \
    -A backend.app.core.celery_app \
    flower \
    --address=0.0.0.0 \
    --port=5555 \
    --basic_auth=${CELERY_FLOWER_BASIC_AUTH}:${CELERY_FLOWER_PASSWORD}"


exec watchfiles \
    --filter pthon \
    --ignore-paths '.venv,.git,__pycache__,*.pyc' \
    "${FLOWER_CMD}"
