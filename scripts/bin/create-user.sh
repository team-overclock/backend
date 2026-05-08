#!/usr/bin/with-contenv bash

trap "stty echo; exit" INT TERM EXIT

usage() {
	echo "Usage: $0 <email> [username]"
}

if [ -z "$1" ]; then
    usage
    exit 1
fi

EMAIL="$1"
USERNAME="${2:-${EMAIL%@*}}"

stty -echo
printf "Password: "
read -r PASSWORD
stty echo
echo

DATA=$(jq -n \
	--arg un "$USERNAME" \
	--arg em "$EMAIL" \
	--arg pw "$PASSWORD" \
	'{name: $un, email: $em, password: $pw}'
)

RES=$(curl -s \
	-X POST \
	-H "Content-Type: application/json" \
	--connect-timeout 1 \
	--max-time 5 \
	-d "$DATA" \
	http://localhost:${PORT:-8000}/auth/signup
)

echo "$RES" | jq 2> /dev/null || echo "$RES"
