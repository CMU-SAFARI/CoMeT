# CoMeT: Count-Min Sketch-based Aggressor Row Tracking to Mitigate RowHammer at Low Cost

This repository contains the source code of CoMeT, a Count-Min Sketch-based Aggressor Row Tracking to Mitigate RowHammer at Low Cost accepted at HPCA 2024. 

## 1. Installation Guide with Docker:
----
### Software Requirements for Docker-based installation:
``` cpp
- Docker
- curl
- tar
- Debian-based Linux distribution
```
Tested versions and distributions:
```
- Docker version 20.10.23, build 7155243
- Podman 3.4.4
- curl 7.81.0   
- tar (GNU tar) 1.34
- Kernel: 5.15.0-56-generic 
- Dist: Ubuntu SMP 22.04.1 LTS (Jammy Jellyfish)
                    
```

### Tested hardware infrastructure:
``` cpp
1) Nodes used:  Intel(R) Xeon(R) Gold 5118 CPU @ 2.30GHz 
2) Slurm version: slurm-wlm 21.08.5
```

The Docker images contain all the necessary software to compile and run Ramulator experiments, therefore no additional system-level installation step is required.

## 2. Installation Guide Without Docker:
----

### Prerequisites:
- G++ version above 8.4 (tested with 9.4.0 & 11.3.0)
- CMake 3.10+ (tested with 3.16.3, 3.22.1)
- Python with pandas, seaborn, and ipython
- [Optional] Slurm 

### Installation steps:
- Run `./build.sh` to install all required packages and compile Ramulator
- Run `./get_cputraces.sh` to fetch CPU traces and place them under `CoMeT_Path/cputraces/`.

## 3. Reproducing Key Results for Artifact Evaluation
----
### ***Slurm-based execution***
We strongly suggest using a Slurm-based infrastructure to enable running experiments in bulk. Use the following command to **(1)** fetch the Docker image, **(2)** compile Ramulator inside Docker, **(3)** fetch CPU traces, and **(4)** queue Slurm jobs for experiments. 

We suggest using ```tmux``` or similar tools that enable persistent bash sessions when submitting jobs to Slurm to avoid any interruptions during the execution of this script.

```bash
$ ./run_artifact.sh --slurm docker 
```

This script creates a directory per configuration under the ```ae-results/``` directory to collect statistics of each experiment.

### ***Native execution*** 
Use the following command to **(1)** fetch the Docker image, **(2)** compile Ramulator inside Docker, **(3)** fetch CPU traces, and **(4)** run all experiments.

Given that this script will run all experiments simultaneously, the reader can modify ```genrunsp_docker.py``` to comment out some configurations to run a subset of experiments at once.

```bash
$ ./run_artifact.sh --native docker 
```
This script creates a directory per configuration under the ```ae-results/``` directory to collect statistics of each experiment.

### ***Experiment completion***

Each experiment for provided configurations take at most 24 hours. Executing all jobs can take 1.5-2 days in a compute cluster, depending on the cluster load. The reader can check the results and statistics generated by the experiments by checking the ```ae-results/``` directory. Each experiment generates a file that contains its statistics (```ae-results/<config>/<workload>/DDR4stats.stats```) when it is completed.  

### ***Obtaining figures and key results***

To plot all figures at once use the python script ```create_all_plots.py``` under ```scripts/artifact/fast-forward/```:

```bash 
$ cd scripts/artifact/fast-forward/
$ python3 create_all_results.py -W ignore
```

The reader can specify a result directory with command line argument  ```-r results_dir```. By default, the script looks for statistics under ```ae-results/```.

This command creates the following plots and their related results that are mentioned in the paper:

1. ```comet-singlecore.pdf```: Figure 8
2. ```comet-singlecore-energy.pdf```: Figure 9
3. ```comet-singlecore-comparison.pdf```: Figure 10
4. ```comet-singlecore-energy-comparison.pdf```: Figure 11
5. ```comet-k-evaluation.pdf```: Figure 17
6. ```comet-motiv.pdf```: Figure 3
7. ```comet-ctsweep-1k.pdf```: Figure 6a
8. ```comet-ctsweep-125.pdf```: Figure 6b
9. ```comet-ratsweep.pdf```: Figure 7

Our artifact also includes separate Jupyter notebooks to obtain the key figures and results under ```scripts/artifact/```. The reader can also execute all cells in each Jupyter notebook to obtain the same results.

## 4. Example Usage for Additional Experiments
----
We provide example configurations under ```configs/```. Any of them can be given to ```ramulator``` combined with a CPU trace (or a set of traces). Please examine a configuration file for possible experiment configurations (e.g., which mechanism to model, which RowHammer threshold to test for, which CPU trace(s) to run, additional mitigation method knobs per mechanism, etc.).

``` bash
$ ./ramulator -c configs/CoMeT-k/CoMeT1000-3.yaml # runs ramulator with CoMeT1000-3.yaml config
```
