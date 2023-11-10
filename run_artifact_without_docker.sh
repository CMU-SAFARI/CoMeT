#!/bin/bash

print_colorful_text() {
  local text="$1"
  local color_code="$2"
  echo -e "\e[${color_code}m${text}\e[0m"
}

if [ "$1" = "--slurm" ]; then
  execution_mode_arg="slurm"
  echo "Running in job-based mode"
elif [ "$1" = "--native" ]; then
  execution_mode_arg="native"
  echo "Running in native mode"
else 
  echo "Provide correct execution mode: --slurm or --native"
  exit
fi

# CREATE ASCII ART SAYING " CoMeT ARTIFACT"
# Assuming you have an ASCII art generator command or script
 ./generate_ascii_art.sh 

echo "==================  Compiling the simulator =================="
sh ./build.sh

echo "==================  Generating run scripts =================="
python3 ./genrunsp_cluster.py -wd $PWD -od ae-results -td $PWD/cputraces --exec $execution_mode_arg


# check if cputraces/ directory is empty
if [ "$(ls -A cputraces/)" ]; then
  echo "==================  cputraces/ directory is not empty =================="
else
  echo "==================  cputraces/ directory is empty =================="
  echo "==================  Downloading the traces into ./cputraces =================="
  wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=18BAvuQybyKT-RRHeAUFOsMAttG4xWlj-' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=18BAvuQybyKT-RRHeAUFOsMAttG4xWlj-" -O cputraces.tar.bz2 && rm -rf /tmp/cookies.txt

  tar -xvf cputraces.tar.bz2
fi

# echo "==================  Decompressing the traces into ./cputraces =================="
# wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=18BAvuQybyKT-RRHeAUFOsMAttG4xWlj-' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=18BAvuQybyKT-RRHeAUFOsMAttG4xWlj-" -O cputraces.tar.bz2 && rm -rf /tmp/cookies.txt

# tar -xvf cputraces.tar.bz2

echo "==================  Launching experiments =================="
sh ./run.sh
