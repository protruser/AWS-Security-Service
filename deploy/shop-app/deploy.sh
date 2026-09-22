#!/usr/bin/env bash
set -Eeuo pipefail

readonly CONTAINER_NAME="shop-app"
readonly ENV_DIR="/opt/shop-app"
readonly ENV_FILE="${ENV_DIR}/app.env"
readonly HEALTH_URL="http://127.0.0.1:8443/health"
readonly READY_URL="http://127.0.0.1:8443/ready"

log() {
  printf '[shop-app-deploy] %s\n' "$1"
}

fail() {
  printf '[shop-app-deploy] ERROR: %s\n' "$1" >&2
  exit 1
}

if [[ $# -ne 3 ]]; then
  fail "usage: deploy.sh <image-uri> <aws-region> <shop-db-secret-id>"
fi

readonly IMAGE_URI="$1"
readonly AWS_REGION="$2"
readonly SHOP_DB_SECRET_ID="$3"
readonly ECR_REGISTRY="${IMAGE_URI%%/*}"

for command_name in aws docker jq curl od tr; do
  command -v "$command_name" >/dev/null 2>&1 || fail "required command is unavailable: $command_name"
done

[[ "$ECR_REGISTRY" != "$IMAGE_URI" ]] || fail "image URI must include an ECR registry and repository"

install -d -m 700 "$ENV_DIR"
temporary_env="$(mktemp "${ENV_DIR}/app.env.XXXXXX")"
cleanup() {
  rm -f "$temporary_env"
}
trap cleanup EXIT
chmod 600 "$temporary_env"

secret_key=""
if [[ -f "$ENV_FILE" ]]; then
  while IFS= read -r env_line; do
    case "$env_line" in
      SECRET_KEY=*)
        candidate="${env_line#SECRET_KEY=}"
        if [[ ${#candidate} -ge 32 && "$candidate" != *$'\r'* ]]; then
          secret_key="$candidate"
        fi
        break
        ;;
    esac
  done <"$ENV_FILE"
fi

if [[ -z "$secret_key" ]]; then
  log "Generating the persistent application secret key."
  secret_key="$(od -An -N48 -tx1 /dev/urandom | tr -d ' \n')"
fi

log "Retrieving application configuration from AWS Secrets Manager."
aws secretsmanager get-secret-value \
  --region "$AWS_REGION" \
  --secret-id "$SHOP_DB_SECRET_ID" \
  --query SecretString \
  --output text |
  jq -er '
    if type != "object" then
      error("secret must be a JSON object")
    else
      {
        DB_HOST: (.host // ""),
        DB_PORT: ((.port // "") | tostring),
        DB_NAME: (.database // ""),
        DB_USER: (.username // ""),
        DB_PASSWORD: (.password // "")
      }
    end
    | if all(.[]; type == "string" and length > 0 and (test("[\r\n]") | not))
      then .
      else error("required secret values must be non-empty single-line strings")
      end
    | to_entries[]
    | "\(.key)=\(.value)"
  ' >"$temporary_env"

printf 'SECRET_KEY=%s\n' "$secret_key" >>"$temporary_env"
printf '%s\n' 'FLASK_ENV=lab' 'VULNERABLE_LAB=1' >>"$temporary_env"
mv -f "$temporary_env" "$ENV_FILE"
chmod 600 "$ENV_FILE"

log "Logging in to Amazon ECR and pulling the requested image."
aws ecr get-login-password --region "$AWS_REGION" |
  docker login --username AWS --password-stdin "$ECR_REGISTRY" >/dev/null
docker pull "$IMAGE_URI"

previous_image=""
if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  previous_image="$(docker container inspect --format '{{.Config.Image}}' "$CONTAINER_NAME")"
  log "Stopping the existing container."
  docker stop --time 30 "$CONTAINER_NAME" >/dev/null
  docker rm "$CONTAINER_NAME" >/dev/null
fi

run_container() {
  local image="$1"
  docker run --detach \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    --env-file "$ENV_FILE" \
    -p 8443:5000 \
    "$image" >/dev/null
}

wait_until_healthy() {
  local attempt
  for attempt in $(seq 1 30); do
    if curl --fail --silent --show-error --output /dev/null "$HEALTH_URL" &&
       curl --fail --silent --show-error --output /dev/null "$READY_URL"; then
      return 0
    fi
    sleep 5
  done
  return 1
}

log "Starting the new shop-app container."
if run_container "$IMAGE_URI" && wait_until_healthy; then
  log "Deployment passed liveness and readiness checks."
  exit 0
fi

log "New deployment failed health checks; removing the failed container."
docker rm --force "$CONTAINER_NAME" >/dev/null 2>&1 || true

if [[ -n "$previous_image" ]]; then
  log "Attempting rollback to the previous image."
  if run_container "$previous_image" && wait_until_healthy; then
    fail "deployment failed; rollback to the previous image succeeded"
  fi
  docker rm --force "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fail "deployment failed and rollback did not become healthy"
fi

fail "deployment failed and no previous image was available for rollback"
