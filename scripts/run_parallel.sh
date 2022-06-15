#!/bin/bash
for (( i=1; i <= $1; ++i )) do
    python3 ./main.py > /dev/null &
done
wait