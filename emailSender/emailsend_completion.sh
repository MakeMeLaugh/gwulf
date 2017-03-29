_show_complete()
{
    local cur prev opts formats
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    __get_opts $1
    opts="${OPTS}"

    case "${prev}" in
        # http://unix.stackexchange.com/a/55622
        "-a"|"--attachment")
        # Unescape space
        cur=${cur//\\ / }
        # Expand tilder to $HOME
        [[ ${cur} == "~/"* ]] && cur=${cur/\~/$HOME}
        # Show completion if path exist (and escape spaces)
        compopt -o filenames
        local files=("${cur}"*)
        [[ -e ${files[0]} ]] && COMPREPLY=( "${files[@]// /\ }" )
        return 0
        ;;
        *)
        ;;
    esac

    compopt +o nospace;

    case "${prev}" in
        "--config") COMPREPLY=( $(compgen -W "$(echo `${1} --list-config` \
        | grep -oP "^.*configs\:\033\[0m\s+\K.*$")" -- ${cur}) ) && return 0
        ;;
        *)
        ;;
    esac

    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
}

__get_opts() {
    OPTS=$(grep -oP "(\(|,\s)\K('-[a-zA-Z0-9_-]*'|'--[a-zA-Z0-9_-]*')" $(which $1) | sed -re "s/'//g" | xargs echo)
    OPTS+=" -h --help"
}

complete -F _show_complete -o nospace emailSend
