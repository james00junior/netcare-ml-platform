#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-netcareai}"
REGION="${REGION:-us-central1}"
REPOSITORY="${REPOSITORY:-netcare}"
SERVICE="${SERVICE:-netcare-readmission-api}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE}:${IMAGE_TAG}"

printf 'Project: %s\nRegion: %s\nService: %s\nImage: %s\n' \
  "$PROJECT_ID" "$REGION" "$SERVICE" "$IMAGE"

gcloud config set project "$PROJECT_ID" >/dev/null

gcloud builds submit \
  --tag "$IMAGE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  .

gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --platform managed \
  --port 8080 \
  --cpu 1 \
  --memory 512Mi \
  --concurrency 20 \
  --timeout 60 \
  --min 0 \
  --max 3 \
  --allow-unauthenticated
