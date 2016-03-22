#!/bin/bash

USAGE="
${0}\tSimple file remover using find system tool with mtime predicate

Usage of ${0}:
bash ${0} PATH TYPE [+|-] PERIOD
"

if [[ $# -lt 3 ]];then
    echo -e "${USAGE}"
    exit 2
fi

SEARCH_DIR=$(readlink -e "${1}")
TYPE=$2
DIRECTION=$3
PERIOD=$4
REMOVE="rm -rf "
FIND_COMMAND=$(find "${SEARCH_DIR}" -type "${TYPE}" -mtime "${DIRECTION}""${PERIOD}" -exec ls -lah {} \;)

OUTPUT=`echo "${FIND_COMMAND}"`

if [[ -z ${OUTPUT} ]]; then
    echo -e "Nothing to delete"
    exit 1
fi

echo -e "Search path: ${SEARCH_DIR}"
echo -e "About to remove:"
echo "${OUTPUT}" | awk '{print "file:\t",$9,"\tdate created:\t",$7,$6,$8}'

FILES=`echo "${OUTPUT}" | awk '{print $9}'`

for FILE in "${FILES[@]}";do
    FILE=`echo -en "${FILE}" | sed -re 's/\n/ /g'`
    REMOVE="${REMOVE}${FILE} ";
done

echo -en "Continue removig? [Y/n]\n"
read choice

case ${choice} in
    Y|y) `echo -e "${REMOVE[*]}"`
    exit $?
    ;;
    N|n) exit 1
    ;;
    *) `echo -e "${REMOVE[@]}"`
    exit $?
    ;;
esac

exit $?