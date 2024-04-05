
# :comet: CoMeT: Count-Min Sketch-based Aggressor Row Tracking to Mitigate RowHammer at Low Cost

<p align=center>
<a href="https://doi.org/10.5281/zenodo.10120298"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.10120298.svg" alt="DOI"></a>
<img src="https://img.shields.io/badge/Origin-Academic%20Code-C1ACA0.svg" alt="Academic Code">
<a href="https://isocpp.org/std/the-standard"><img src="https://img.shields.io/badge/Made%20with-C/C++-blue.svg" alt="Language Badge"></a>
<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
<img src="https://img.shields.io/badge/Contributions-welcome-lightgray.svg" alt="Contributions Welcome">
<a href="https://arxiv.org/pdf/2402.18769.pdf"><img src="https://img.shields.io/badge/cs.AR-2402.18769-b31b1b?logo=arxiv&logoColor=red" alt="Preprint: arXiv"> </a>
</p>

This repository contains the source code of CoMeT, our [HPCA'24 paper](https://arxiv.org/pdf/2402.18769.pdf). 

CoMeT is a new RowHammer mitigation mechanism, that prevents RowHammer bitflips with low area, performance, and energy costs in DRAM-based systems at very low RowHammer thresholds. The key idea of CoMeT is to use low-cost and scalable hash-based counters to track DRAM rows and thus, reduce the overhead of expensive tag-based counters.

> F. Nisa Bostanci, Ismail Emir Yuksel, Ataberk Olgun, Konstantinos Kanellopoulos, Yahya Can Tugrul, A. Giray Yaglikci, Mohammad Sadrosadati, and Onur Mutlu. "CoMeT: Count-Min-Sketch-based Row Tracking to Mitigate RowHammer at Low Cost", HPCA 2024.

Please use the following citation to cite CoMeT if the repository is useful for you.

```
@inproceedings{bostanci2024comet,
  title={{CoMeT: Count-Min-Sketch-based Row Tracking to Mitigate RowHammer at Low Cost}},
  author={F. Nisa Bostanci, Ismail Emir Yuksel, Ataberk Olgun, Konstantinos Kanellopoulos, Yahya Can Tugrul, A. Giray Yaglikci, Mohammad Sadrosadati, and Onur Mutlu},
  booktitle={HPCA},
  year={2024}
}
```

## 1. Installation Guide with Docker:

### Software Requirements for Docker-based installation:
``` 
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

> :warning: The Docker images contain all the necessary software to compile and run Ramulator experiments, therefore no additional system-level installation step is required.

## 2. Installation Guide without Docker:

> :warning: Provided `build.sh` script installs all dependencies and automatically runs by the `run_artifact_without_docker.sh` script. 

The reader can also install each dependency manually.

### Dependencies :
- G++ version above 8.4 (tested with 9.4.0 & 11.3.0)
- CMake 3.10+ (tested with 3.16.3, 3.22.1)
- Python with pandas, seaborn, and ipython


## 3. Reproducing Key Results for Artifact Evaluation

The following instructions assume the reader is using Docker. If the reader is not using Docker, please refer to the instructions at the end of the section (:fast_forward:).

:warning: We suggest using ```tmux``` or similar tools that enable persistent bash sessions to avoid any interruptions during the execution of the `run_artifact.sh` script.

### ***Slurm-based execution***
We strongly suggest using a Slurm-based infrastructure to enable running experiments in bulk. Use the following command to **(1)** fetch the Docker image, **(2)** compile Ramulator inside Docker, **(3)** fetch CPU traces, and **(4)** queue Slurm jobs for experiments. 


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

---
:fast_forward: The reader can also run experiments **without Docker** by using `run_artifact_without_docker.sh` script. This script automatically installs all dependencies, fetches CPU traces. It runs `genrunsp_cluster.py` script and generates all Slurm jobs/bash scripts for native execution given the `--slurm` or `--native` flag. The reader can modify `genrunsp_cluster.py` to comment out some configurations to run a subset of experiments at once.

### ***Experiment completion***

Each experiment for provided configurations takes at most 24 hours. Executing all jobs can take 1.5-2 days in a compute cluster, depending on the cluster load. The reader can check the results and statistics generated by the experiments by checking the ```ae-results/``` directory. Each experiment generates a file that contains its statistics (```ae-results/<config>/<workload>/DDR4stats.stats```) when it is completed.  

### ***Obtaining figures and key results***
To plot all figures at once using a docker image, the reader can use the ```plot_docker.sh``` script.

``` bash
$ ./plot_docker.sh docker
```

This script pulls a Docker image with the Python dependencies. It then plots all figures and saves the results mentioned in the paper under ```plots/``` directory.

This command creates the following plots and their related results that are mentioned in the paper:

1. ```comet-singlecore.pdf```: Figure 10
2. ```comet-singlecore-energy.pdf```: Figure 11
3. ```comet-singlecore-comparison.pdf```: Figure 12
4. ```comet-singlecore-energy-comparison.pdf```: Figure 13
5. ```comet-k-evaluation.pdf```: Figure 9
6. ```comet-motiv.pdf```: Figure 3
7. ```comet-ctsweep-1k.pdf```: Figure 6a
8. ```comet-ctsweep-125.pdf```: Figure 6b
9. ```comet-ratsweep.pdf```: Figure 7

Alternatively, to plot all figures at once the reader can use the python script ```create_all_plots.py``` under ```scripts/artifact/fast-forward/``` given all dependencies are installed:

```bash 
$ cd scripts/artifact/fast-forward/
$ python3 -W ignore create_all_results.py 
```

The reader can specify a result directory with command line argument  ```-r results_dir```. By default, the script looks for statistics under ```ae-results/```.

Our artifact also includes separate Jupyter notebooks to obtain the key figures and results under ```scripts/artifact/```. The reader can also execute all cells in each Jupyter notebook to obtain the same results.

## 4. Example Usage for Additional Experiments

We provide example configurations under ```configs/```. Any of them can be given to ```ramulator``` combined with a CPU trace (or a set of traces). Please examine a configuration file for possible experiment configurations (e.g., which mechanism to model, which RowHammer threshold to test for, which CPU trace(s) to run, additional mitigation method knobs per mechanism, etc.).

``` bash
$ ./ramulator -c configs/CoMeT-k/CoMeT1000-3.yaml # runs ramulator with CoMeT1000-3.yaml config
```

## 5. Contact
Nisa Bostanci (nisa.bostanci [at] safari [dot] ethz [dot] ch)
