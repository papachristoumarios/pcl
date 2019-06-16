#!/bin/bash

# Lexer tests

LEXTEST=`ls examples/*.pcl | xargs -n 1 cat | ./pcl -l | echo $?`

if [ $LEXTEST -ne 0 ]; then
    echo "Error with lexer" 
    exit 1
fi
