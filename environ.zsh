#!/usr/bin/zsh

PATH='$PATH:$(dirname "$0")/bin'
PATH='$PATH:$(dirname "$0")/shell'
PATH='$PATH:$(dirname "$0")/python'

alias python='python $@ 2> >(tee >(cat | grep "^ *File" | sed "s/ *File/vim/g" | sed "s/, line / +/g" | sed "s/, in .*//g" | sed -E  "s: \"([^/]): \"$PWD/\1:g" 1>! /tmp/python.breakpoints))'
bindkey -s "^l" " pybp ^m"
