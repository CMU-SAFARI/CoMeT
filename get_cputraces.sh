#!/bin/bash

echo "================== Downloading the CPU traces =================="

wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=18BAvuQybyKT-RRHeAUFOsMAttG4xWlj-' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=18BAvuQybyKT-RRHeAUFOsMAttG4xWlj-" -O cputraces.tar.bz2 && rm -rf /tmp/cookies.txt

echo "================== Decompressing the traces into ./cputraces =================="
tar -xvf cputraces.tar.bz2