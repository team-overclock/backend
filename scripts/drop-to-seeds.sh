#!/usr/bin/with-contenv bash

source ./functions.sh

set -e

WARNING "!!! 3초 후 모든 데이터를 삭제하고 다시 생성합니다 !!!"
INFO "중단하려면 Ctrl+C를 누르세요."

sleep 3

INFO "작업을 시작합니다."
echo
INFO "--- drop-tables ---"
drop-tables --yes
INFO "--- insert-data ---"
insert-data
INFO "--- insert-seeds ---"
insert-seeds
