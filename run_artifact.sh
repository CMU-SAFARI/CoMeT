#!/bin/bash




print_colorful_text() {
  local text="$1"
  local color_code="$2"
  echo "\e[${color_code}m${text}\e[0m"
}



if [ "$1" = "--slurm" ]; then
      execution_mode_arg="--slurm"
      echo "Running in job-based mode";
elif ([ "$1" = "--native" ]); then
      execution_mode_arg="--native"
      echo "Running in native mode";
else 
      echo "Provide correct execution mode: --slurm or --native"
      exit
fi

if [ -z "$2" ];  then
  echo "Provide container: docker or podman"
  exit
elif [ "$2" = "docker" ]; then
  container="docker"
  echo "Using docker"
elif [ "$2" = "podman" ]; then
  container="podman"
  echo "Using podman"
else 
  echo "Wrong container: provide docker or podman"
fi 

# CREATE ASCII ART SAYING " CoMeT ARTIFACT"


 
echo "==================  Run a container test to make sure container works =================="

${container} run docker.io/hello-world

echo "====================================================================================="

echo "==================  Pulling the Docker image to run the experiments =================="

${container}  pull docker.io/richardluo831/cpp-dev:latest

echo "====================================================================================="

echo "==================  Compiling the simulator =================="

${container} run --rm -v $PWD:/app/ docker.io/richardluo831/cpp-dev:latest /bin/bash -c "cd /app/ && mkdir -p build && sh ./build.sh"


${container} run --rm -v $PWD:/app/ docker.io/richardluo831/cpp-dev:latest /bin/bash -c "./app/ramulator"


${container} run --rm -v $PWD:/app/ docker.io/richardluo831/cpp-dev:latest /bin/bash -c "python3 /app/genrunsp_docker.py ${PWD} ${execution_mode_arg}" 



echo "==================  Decompressing the traces into ./traces =================="

wget "Specify path to traces here"
tar -xzf traces_comet

# echo "====================================================================================="

# echo "================== Launching experiments for Figures 2, 3, 4, 6, 15, 16, 18, 19, 20, 22, 23, 24 =================="

sh ./run.sh 







