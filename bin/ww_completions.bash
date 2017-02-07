_ww_completions()
{
    # remove leading spaces from the full command
    local cmd="$(echo -e "${COMP_WORDS[@]}" | sed -e 's/^[[:space:]]*//')"
    local cur=""
    if [[ "${cmd:${#cmd}-1}" == " " ]]; then
        # we are on the next agument - remove the trailing spaces
        cmd="$(echo -e "${COMP_WORDS[@]}" | sed -e 's/[[:space:]]*$//')"
    else
        # separate out the current word
        cur="${COMP_WORDS[COMP_CWORD]}"
        cmd="$(echo -e "${COMP_WORDS[@]}" | sed -e 's/[[:space:]]*[^[:space:]]*$//')"
    fi

    case "$cmd" in
        "ww")
            # all available commands
            local cmds="repo new rm ls cd pull land"
            COMPREPLY=($(compgen -W "$cmds" -- $cur))
            return 0
            ;;
        "ww rm"|"ww cd"|"ww land")
            # worktree name
            local worktrees="$(ww ls | awk '{ print $1 }')"
            COMPREPLY=($(compgen -W "$worktrees" -- $cur))
            return 0
            ;;
    esac

    COMPREPLY=()
    return 0
}
complete -F _ww_completions ww
