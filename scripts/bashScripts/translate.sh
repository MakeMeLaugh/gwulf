#!/bin/bash
API_KEY="" # put your Yandex API key here
URL="https://translate.yandex.net/api/v1.5/tr.json/translate"
TRANSLATION='lang=' # Target language (e.g.: lang=en)
data=$(xsel -o)

notify-send "Перевод \"${data}\"" "$(curl -s "${URL}?${API_KEY}&text=\"${data}\"&${TRANSLATION}" | jq  .text[] | sed -re 's/\"//g')" 2>/dev/null