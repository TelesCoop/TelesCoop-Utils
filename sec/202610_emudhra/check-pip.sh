#!/usr/bin/env bash
set -u

URL="https://dv-g3b-emudhra.we-have-a-problem.com/"

declare -A MIN_VERSIONS=(
    [certifi]=2026.10.19
    [pip]=26.2.2
    [uv]=0.13.4
    [sigstore]=4.5.1
    [conda]=26.9.4
    [pixi]=0.82.1
)

failed=0

status=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$URL")

if [ "$status" = "200" ]; then
    echo "ÉCHEC : $URL répond 200 depuis cette machine" >&2
    failed=1
else
    echo "OK : $URL répond $status"
fi

# True when $1 < $2 according to version sort
version_lt() {
    [ "$1" != "$2" ] && [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -n1)" = "$1" ]
}

outdated=()
while read -r name version _; do
    min=${MIN_VERSIONS[${name,,}]:-}
    if [ -n "$min" ] && version_lt "$version" "$min"; then
        outdated+=("  - $name $version (minimum requis : $min)")
    fi
done < <(python -m pip list 2>/dev/null | tail -n +3)

if [ ${#outdated[@]} -gt 0 ]; then
    echo "ÉCHEC : mises à jour à faire pour les paquets suivants :" >&2
    printf '%s\n' "${outdated[@]}" >&2
    failed=1
else
    echo "OK : aucun paquet surveillé n'est en dessous de sa version minimale"
fi

exit "$failed"
