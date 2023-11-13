#!/bin/bash
if [ -z "$1" ];  then
  echo "Provide container: docker or podman"
  exit
elif [ "$1" = "docker" ]; then
  container="docker"
  echo "Using docker"
elif [ "$1" = "podman" ]; then
  container="podman"
  echo "Using podman"
else 
  echo "Wrong container: provide docker or podman"
fi 

echo "====================================================================================="

echo "==================  Pulling the Docker image to create plots =================="

${container} pull docker.io/kanell21/artifact_evaluation:victima_ptwcp_v1.1

echo "================================================================================"
echo "==================  Creating Plots =================="
pwd
${container} run --rm -v $PWD:/app/ docker.io/kanell21/artifact_evaluation:victima_ptwcp_v1.1 /bin/bash -c "python3 -W ignore  scripts/artifact/fast-forward/create_all_plots.py -r ae-results/"

echo "================================================================================"
echo "==================  Plots and Results  =================="
ls -l plots/