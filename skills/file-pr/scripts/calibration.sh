#!/usr/bin/env bash
# Operator shortcuts for local-review calibration. Approving and paid steps need explicit flags or
# confirmation. Only `usage` reads the key, and it sends it to OpenRouter alone.
set -euo pipefail
umask 077

OP="${FILE_PR_OPERATOR_DIR:-$HOME/.local/state/file-pr-operator}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
RUNNER="$HERE/local-review/dist/cli.js"
KEY="$OP/openrouter.key"

usage() {
  cat <<EOF
Usage: calibration.sh COMMAND [options]

  new --route bedrock|vertex --approved-by NAME --confirm-privacy [--hours 48]
        Prepare the next calibration-N and write its approved calibration approval.
        --confirm-privacy states you enabled ZDR and disabled logging in OpenRouter.
  run [ID] [--builder-model anthropic/claude-opus-5.5] [--yes]
        Paid, one-shot calibration run (asks before spending unless --yes).
  status [ID]      Summarize a run: status, reason, per-case cost and lens reasons.
  usage            OpenRouter usage for the dedicated key (never prints the key).
  grade [ID] [--judgments PATH]
  qualify [ID] --records PATH [--judgments PATH]
  hash             Current runtime hash for rollout signoff.

ID defaults to the newest calibration-N in $OP.
Judgments default to $OP/ID-judgments.json.
EOF
}
die() { echo "calibration.sh: $*" >&2; exit 2; }
latest() {
  local n
  n=$(find "$OP" -maxdepth 1 -type d -name 'calibration-[0-9]*' 2>/dev/null | sed 's/.*calibration-//' | grep -E '^[0-9]+$' | sort -n | tail -1)
  [ -n "$n" ] || die "no calibration-N in $OP; run: calibration.sh new"
  echo "calibration-$n"
}
pick_id() { if [ -n "${1:-}" ] && [ "${1#--}" = "$1" ]; then echo "$1"; else latest; fi; }

cmd_new() {
  local route="" by="" hours=48 confirmed=false upstream provider
  while [ $# -gt 0 ]; do
    case "$1" in
      --route) route="${2:-}"; shift 2 ;;
      --approved-by) by="${2:-}"; shift 2 ;;
      --hours) hours="${2:-}"; shift 2 ;;
      --confirm-privacy) confirmed=true; shift ;;
      *) die "unknown option $1" ;;
    esac
  done
  case "$route" in
    bedrock) upstream="amazon-bedrock"; provider="Amazon Bedrock" ;;
    vertex) upstream="google-vertex/global"; provider="Google" ;;
    *) die "--route must be bedrock or vertex (the routes on OpenRouter's ZDR list within price limits)" ;;
  esac
  [ -n "$by" ] || die "--approved-by NAME is required"
  [[ "$hours" =~ ^[0-9]+$ ]] && [ "$hours" -ge 1 ] || die "--hours must be a positive integer"
  $confirmed || die "pass --confirm-privacy only after enabling ZDR and disabling input/output logging in OpenRouter settings"
  [ -f "$KEY" ] || die "missing key file $KEY"

  mkdir -p "$OP"  # umask 077 makes every created level 0700
  local n=1
  while [ -e "$OP/calibration-$n" ]; do n=$((n + 1)); done
  local id="calibration-$n" exp
  node "$RUNNER" calibrate prepare --root "$OP/$id" --id "$id" >/dev/null
  node "$RUNNER" calibrate draft --root "$OP/$id" > "$OP/$id-draft.json"
  exp=$(( ($(date +%s) + hours * 3600) * 1000 ))
  jq --arg by "$by" --argjson exp "$exp" --arg key "$KEY" --arg up "$upstream" --arg prov "$provider" '
    .approvedBy=$by | .expiresAt=$exp
    | .requestedUpstream=$up | .reportedProvider=$prov
    | .sourceExport=true | .keyFileRead=true | .keyPath=$key
    | .privacy.zdr=true | .privacy.consent=true | .privacy.accountLoggingDisabled=true
    | .calibrationBudget.expiresAt=$exp
    | .status="approved"' "$OP/$id-draft.json" > "$OP/$id-approval.json"
  echo "Prepared $id, approved by $by"
  echo "  route:   $upstream ($provider)"
  echo "  expires: $(date -r $((exp / 1000)) 2>/dev/null || date -d "@$((exp / 1000))")"
  jq -r '.calibrationBudget | "  budget:  max $\(.maxCostUsd), \(.maxRequests) requests, \(.maxDurationMs / 60000) minutes"' "$OP/$id-approval.json"
  echo "Next: calibration.sh run"
}

cmd_run() {
  local id builder="anthropic/claude-opus-5.5" yes=false
  id=$(pick_id "${1:-}"); [ "${1:-}" = "$id" ] && shift
  while [ $# -gt 0 ]; do
    case "$1" in
      --builder-model) builder="${2:-}"; shift 2 ;;
      --yes) yes=true; shift ;;
      *) die "unknown option $1" ;;
    esac
  done
  local approval="$OP/$id-approval.json"
  [ -f "$approval" ] || die "missing $approval; run: calibration.sh new"
  [ -e "$OP/$id/collection.json" ] && die "$id already ran (one-shot); see: calibration.sh status $id"
  if ! $yes; then
    printf 'Start paid one-shot run %s via %s (max $%s)? [y/N] ' "$id" "$(jq -r .requestedUpstream "$approval")" "$(jq -r .calibrationBudget.maxCostUsd "$approval")"
    read -r answer; [ "$answer" = y ] || [ "$answer" = Y ] || die "not started"
  fi
  local code=0
  node "$RUNNER" calibrate run --root "$OP/$id" --approval "$approval" --builder-model "$builder" || code=$?
  echo; cmd_status "$id"
  return "$code"
}

cmd_status() {
  local id; id=$(pick_id "${1:-}")
  local root="$OP/$id"
  [ -f "$root/collection.json" ] || { echo "$id: prepared, not run"; return 0; }
  jq -r --arg id "$id" '"\($id): \(.status)\(if .reason then " — \(.reason)" else "" end)",
    "  cases run: \(.results | length)/12, reserved: $\(.reservedUsd)"' "$root/collection.json"
  jq -r '.results[] | "\(.id)\t\(.reportFile)\t\(.wallMs)\t\(.costUsd // "unknown")"' "$root/collection.json" |
  while IFS=$'\t' read -r case file wall cost; do
    echo "  $case: ${wall}ms, cost \$$cost"
    jq -r '.body.lenses[] | "    \(.lens): \(.status)\(if .reason then " — \(.reason)" else "" end)"' "$root/$file"
  done
}

cmd_usage() {
  [ -f "$KEY" ] || die "missing key file $KEY"
  # printf is a builtin, so the key never appears in a process argument list.
  printf 'Authorization: Bearer %s\n' "$(tr -d '[:space:]' < "$KEY")" |
    curl -sS --fail-with-body -H @- https://openrouter.ai/api/v1/key |
    jq '.data | {usage, usage_daily, limit, limit_remaining}'
}

cmd_grade() {
  local id judgments; id=$(pick_id "${1:-}"); [ "${1:-}" = "$id" ] && shift
  judgments="$OP/$id-judgments.json"
  while [ $# -gt 0 ]; do
    case "$1" in --judgments) judgments="${2:-}"; shift 2 ;; *) die "unknown option $1" ;; esac
  done
  node "$RUNNER" calibrate grade --root "$OP/$id" --judgments "$judgments"
}

cmd_qualify() {
  local id judgments records=""; id=$(pick_id "${1:-}"); [ "${1:-}" = "$id" ] && shift
  judgments="$OP/$id-judgments.json"
  while [ $# -gt 0 ]; do
    case "$1" in
      --judgments) judgments="${2:-}"; shift 2 ;;
      --records) records="${2:-}"; shift 2 ;;
      *) die "unknown option $1" ;;
    esac
  done
  [ -n "$records" ] || die "--records PATH is required"
  node "$RUNNER" calibrate qualify --root "$OP/$id" --judgments "$judgments" --records "$records"
}

cmd_hash() {
  node --input-type=module -e 'const { implementationIdentity } = await import(process.argv[1]); console.log((await implementationIdentity()).runtimeHash);' "$HERE/local-review/dist/review.js"
}

command="${1:-help}"; [ $# -gt 0 ] && shift
case "$command" in
  new|run|status|usage|grade|qualify|hash) "cmd_$command" "$@" ;;
  help|-h|--help) usage ;;
  *) usage >&2; exit 2 ;;
esac
