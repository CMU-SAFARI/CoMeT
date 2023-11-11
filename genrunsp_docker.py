import yaml
import os
import random
from argparse import ArgumentParser
import itertools
import random
import sys

BASH_HEADER = "#!/bin/bash\n"

# the command line slurm will execute
comet_path = sys.argv[1]
execution_mode = sys.argv[2]

SBATCH_COMMAND_LINE = "\
    sbatch --cpus-per-task=1 --nodes=1 --ntasks=1 \
    --output={output_file_name} \
    --error={error_file_name} \
    --job-name='{job_name}' \
    ./docker_wrapper.sh \"docker run --rm -v '{comet_dir}':/app/ docker.io/richardluo831/cpp-dev:latest /app/run_scripts/{config_name}{config_extension}-{workload}.sh\""

# the script executed by the command line slurm executes
BASE_COMMAND_LINE = "\
    /app/ramulator "

# nRH sweep all mechanisms
configs = [

    ## DEFAULT CoMeT CONFIGURATIONS ACROSS nRH VALUES (k=3) ##
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-4-512-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT500-4-512-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT250-4-512-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-4-512-128.yaml",

    ## SENSITIVITY ANALYSIS nHASH and nCOUNTERS ##
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-1-128-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-1-256-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-1-512-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-1-1024-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-1-2048-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-2-128-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-2-256-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-2-512-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-2-1024-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-2-2048-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-4-128-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-4-256-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-4-1024-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-4-2048-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-8-128-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-8-256-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-8-512-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-8-1024-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-8-2048-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-16-128-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-16-256-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-16-512-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-16-1024-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-16-2048-128.yaml",

    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-1-128-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-1-256-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-1-512-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-1-1024-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-1-2048-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-2-128-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-2-256-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-2-512-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-2-1024-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-2-2048-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-4-128-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-4-256-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-4-1024-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-4-2048-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-8-128-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-8-256-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-8-512-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-8-1024-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-8-2048-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-16-128-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-16-256-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-16-512-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-16-1024-128.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-16-2048-128.yaml",

    ## SENSITIVITY ANALYSIS nRAT_ENTRIES ##

    "configs/ArtifactEvaluation/CoMeT/CoMeT125-4-512-32.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-4-512-64.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-4-512-256.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT125-4-512-512.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-4-512-32.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-4-512-64.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-4-512-256.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT1000-4-512-512.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT500-4-512-32.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT500-4-512-64.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT500-4-512-256.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT500-4-512-512.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT250-4-512-32.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT250-4-512-64.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT250-4-512-256.yaml",
    "configs/ArtifactEvaluation/CoMeT/CoMeT250-4-512-512.yaml",


    ## COMPARISON POINTS ##
    "configs/ArtifactEvaluation/Others/Baseline.yaml",

    "configs/ArtifactEvaluation/Others/Graphene1000.yaml",
    "configs/ArtifactEvaluation/Others/Graphene500.yaml",
    "configs/ArtifactEvaluation/Others/Graphene250.yaml",
    "configs/ArtifactEvaluation/Others/Graphene125.yaml",

    "configs/ArtifactEvaluation/Others/Hydra1000.yaml",
    "configs/ArtifactEvaluation/Others/Hydra500.yaml",
    "configs/ArtifactEvaluation/Others/Hydra250.yaml",
    "configs/ArtifactEvaluation/Others/Hydra125.yaml",

    "configs/ArtifactEvaluation/Others/PARA1000.yaml",
    "configs/ArtifactEvaluation/Others/PARA500.yaml",
    "configs/ArtifactEvaluation/Others/PARA250.yaml",
    "configs/ArtifactEvaluation/Others/PARA125.yaml",

    "configs/ArtifactEvaluation/Others/REGA1000.yaml",
    "configs/ArtifactEvaluation/Others/REGA500.yaml",
    "configs/ArtifactEvaluation/Others/REGA250.yaml",
    "configs/ArtifactEvaluation/Others/REGA125.yaml",

    ## K=1 EXPERIMENTS ##
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT1000-1.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT500-1.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT250-1.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT125-1.yaml",

    ## K=2 EXPERIMENTS ##

    "configs/ArtifactEvaluation/CoMeT-k/CoMeT1000-2.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT125-2.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT250-2.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT500-2.yaml",

    ## DEFAULT -- K=3 EXPERIMENTS ##
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT1000-3.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT125-3.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT250-3.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT500-3.yaml",

    ## K=4 EXPERIMENTS ##
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT1000-4.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT125-4.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT250-4.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT500-4.yaml",

    ## K=5 EXPERIMENTS ##
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT125-5.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT250-5.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT500-5.yaml",
    "configs/ArtifactEvaluation/CoMeT-k/CoMeT1000-5.yaml",

]

multicore = False  # SET ME FALSE FOR SINGLE CORE!!!!


traces = [
    "401.bzip2",
    "403.gcc",
    "429.mcf",
    "433.milc",
    "434.zeusmp",
    "435.gromacs",
    "436.cactusADM",
    "437.leslie3d",
    "444.namd",
    "445.gobmk",
    "447.dealII",
    "450.soplex",
    "456.hmmer",
    "458.sjeng",
    "459.GemsFDTD",
    "462.libquantum",
    "464.h264ref",
    "470.lbm",
    "471.omnetpp",
    "473.astar",
    "481.wrf",
    "482.sphinx3",
    "483.xalancbmk",
    "500.perlbench",
    "502.gcc",
    "505.mcf",
    "507.cactuBSSN",
    "508.namd",
    "510.parest",
    "511.povray",
    "519.lbm",
    "520.omnetpp",
    "523.xalancbmk",
    "525.x264",
    "526.blender",
    "531.deepsjeng",
    "538.imagick",
    "541.leela",
    "544.nab",
    "549.fotonik3d",
    "557.xz",
    "bfs_dblp",
    "bfs_cm2003",
    "bfs_ny",
    "grep_map0",
    "h264_decode",
    "h264_encode",
    "jp2_decode",
    "jp2_encode",
    "tpcc64",
    "tpch17",
    "tpch2",
    "tpch6",
    "wc_8443",  # wordcount-8443
    "wc_map0",  # wordcount-map0
    "ycsb_abgsave",
    "ycsb_aserver",
    "ycsb_bserver",
    "ycsb_cserver",
    "ycsb_dserver",
    "ycsb_eserver"
]


LOW_RBMPKI = ['531.deepsjeng', '502.gcc', '541.leela', '435.gromacs', '481.wrf', '458.sjeng', '445.gobmk', '444.namd', '508.namd', '401.bzip2', '456.hmmer',
              '403.gcc', '464.h264ref', '526.blender', '447.dealII', '544.nab', '523.xalancbmk', '500.perlbench', '538.imagick', '525.x264', '507.cactuBSSN', '511.povray']
MED_RBMPKI = ['462.libquantum', '473.astar', '510.parest', '482.sphinx3',
              '505.mcf', '557.xz', '471.omnetpp', '483.xalancbmk', '436.cactusADM']
HIGH_RBMPKI = ['520.omnetpp', '450.soplex', '470.lbm', '519.lbm', '434.zeusmp',
               '433.milc', '459.GemsFDTD', '549.fotonik3d', '429.mcf', '437.leslie3d']

if (multicore):
    traces = [
        "401.bzip2-401.bzip2-401.bzip2-401.bzip2-401.bzip2-401.bzip2-401.bzip2-401.bzip2",
        "403.gcc-403.gcc-403.gcc-403.gcc-403.gcc-403.gcc-403.gcc-403.gcc",
        "429.mcf-429.mcf-429.mcf-429.mcf-429.mcf-429.mcf-429.mcf-429.mcf",
        "433.milc-433.milc-433.milc-433.milc-433.milc-433.milc-433.milc-433.milc",
        "434.zeusmp-434.zeusmp-434.zeusmp-434.zeusmp-434.zeusmp-434.zeusmp-434.zeusmp-434.zeusmp",
        "435.gromacs-435.gromacs-435.gromacs-435.gromacs-435.gromacs-435.gromacs-435.gromacs-435.gromacs",
        "436.cactusADM-436.cactusADM-436.cactusADM-436.cactusADM-436.cactusADM-436.cactusADM-436.cactusADM-436.cactusADM",
        "437.leslie3d-437.leslie3d-437.leslie3d-437.leslie3d-437.leslie3d-437.leslie3d-437.leslie3d-437.leslie3d",
        "444.namd-444.namd-444.namd-444.namd-444.namd-444.namd-444.namd-444.namd",
        "445.gobmk-445.gobmk-445.gobmk-445.gobmk-445.gobmk-445.gobmk-445.gobmk-445.gobmk",
        "447.dealII-447.dealII-447.dealII-447.dealII-447.dealII-447.dealII-447.dealII-447.dealII",
        "450.soplex-450.soplex-450.soplex-450.soplex-450.soplex-450.soplex-450.soplex-450.soplex",
        "456.hmmer-456.hmmer-456.hmmer-456.hmmer-456.hmmer-456.hmmer-456.hmmer-456.hmmer",
        "458.sjeng-458.sjeng-458.sjeng-458.sjeng-458.sjeng-458.sjeng-458.sjeng-458.sjeng",
        "459.GemsFDTD-459.GemsFDTD-459.GemsFDTD-459.GemsFDTD-459.GemsFDTD-459.GemsFDTD-459.GemsFDTD-459.GemsFDTD",
        "462.libquantum-462.libquantum-462.libquantum-462.libquantum-462.libquantum-462.libquantum-462.libquantum-462.libquantum",
        "464.h264ref-464.h264ref-464.h264ref-464.h264ref-464.h264ref-464.h264ref-464.h264ref-464.h264ref",
        "470.lbm-470.lbm-470.lbm-470.lbm-470.lbm-470.lbm-470.lbm-470.lbm",
        "471.omnetpp-471.omnetpp-471.omnetpp-471.omnetpp-471.omnetpp-471.omnetpp-471.omnetpp-471.omnetpp",
        "473.astar-473.astar-473.astar-473.astar-473.astar-473.astar-473.astar-473.astar",
        "481.wrf-481.wrf-481.wrf-481.wrf-481.wrf-481.wrf-481.wrf-481.wrf",
        "482.sphinx3-482.sphinx3-482.sphinx3-482.sphinx3-482.sphinx3-482.sphinx3-482.sphinx3-482.sphinx3",
        "483.xalancbmk-483.xalancbmk-483.xalancbmk-483.xalancbmk-483.xalancbmk-483.xalancbmk-483.xalancbmk-483.xalancbmk",
        "500.perlbench-500.perlbench-500.perlbench-500.perlbench-500.perlbench-500.perlbench-500.perlbench-500.perlbench",
        "502.gcc-502.gcc-502.gcc-502.gcc-502.gcc-502.gcc-502.gcc-502.gcc",
        "505.mcf-505.mcf-505.mcf-505.mcf-505.mcf-505.mcf-505.mcf-505.mcf",
        "507.cactuBSSN-507.cactuBSSN-507.cactuBSSN-507.cactuBSSN-507.cactuBSSN-507.cactuBSSN-507.cactuBSSN-507.cactuBSSN",
        "508.namd-508.namd-508.namd-508.namd-508.namd-508.namd-508.namd-508.namd",
        "510.parest-510.parest-510.parest-510.parest-510.parest-510.parest-510.parest-510.parest",
        "511.povray-511.povray-511.povray-511.povray-511.povray-511.povray-511.povray-511.povray",
        "519.lbm-519.lbm-519.lbm-519.lbm-519.lbm-519.lbm-519.lbm-519.lbm",
        "520.omnetpp-520.omnetpp-520.omnetpp-520.omnetpp-520.omnetpp-520.omnetpp-520.omnetpp-520.omnetpp",
        "523.xalancbmk-523.xalancbmk-523.xalancbmk-523.xalancbmk-523.xalancbmk-523.xalancbmk-523.xalancbmk-523.xalancbmk",
        "525.x264-525.x264-525.x264-525.x264-525.x264-525.x264-525.x264-525.x264",
        "526.blender-526.blender-526.blender-526.blender-526.blender-526.blender-526.blender-526.blender",
        "531.deepsjeng-531.deepsjeng-531.deepsjeng-531.deepsjeng-531.deepsjeng-531.deepsjeng-531.deepsjeng-531.deepsjeng",
        "538.imagick-538.imagick-538.imagick-538.imagick-538.imagick-538.imagick-538.imagick-538.imagick",
        "541.leela-541.leela-541.leela-541.leela-541.leela-541.leela-541.leela-541.leela",
        "544.nab-544.nab-544.nab-544.nab-544.nab-544.nab-544.nab-544.nab",
        "549.fotonik3d-549.fotonik3d-549.fotonik3d-549.fotonik3d-549.fotonik3d-549.fotonik3d-549.fotonik3d-549.fotonik3d",
        "557.xz-557.xz-557.xz-557.xz-557.xz-557.xz-557.xz-557.xz",
        "bfs_dblp-bfs_dblp-bfs_dblp-bfs_dblp-bfs_dblp-bfs_dblp-bfs_dblp-bfs_dblp",
        "bfs_cm2003-bfs_cm2003-bfs_cm2003-bfs_cm2003-bfs_cm2003-bfs_cm2003-bfs_cm2003-bfs_cm2003",
        "bfs_ny-bfs_ny-bfs_ny-bfs_ny-bfs_ny-bfs_ny-bfs_ny-bfs_ny",
        "grep_map0-grep_map0-grep_map0-grep_map0-grep_map0-grep_map0-grep_map0-grep_map0",
        "h264_decode-h264_decode-h264_decode-h264_decode-h264_decode-h264_decode-h264_decode-h264_decode",
        "h264_encode-h264_encode-h264_encode-h264_encode-h264_encode-h264_encode-h264_encode-h264_encode",
        "jp2_decode-jp2_decode-jp2_decode-jp2_decode-jp2_decode-jp2_decode-jp2_decode-jp2_decode",
        "jp2_encode-jp2_encode-jp2_encode-jp2_encode-jp2_encode-jp2_encode-jp2_encode-jp2_encode",
        "tpcc64-tpcc64-tpcc64-tpcc64-tpcc64-tpcc64-tpcc64-tpcc64",
        "tpch17-tpch17-tpch17-tpch17-tpch17-tpch17-tpch17-tpch17",
        "tpch2-tpch2-tpch2-tpch2-tpch2-tpch2-tpch2-tpch2",
        "tpch6-tpch6-tpch6-tpch6-tpch6-tpch6-tpch6-tpch6",
        "wc_8443-wc_8443-wc_8443-wc_8443-wc_8443-wc_8443-wc_8443-wc_8443",
        "wc_map0-wc_map0-wc_map0-wc_map0-wc_map0-wc_map0-wc_map0-wc_map0",
        "ycsb_abgsave-ycsb_abgsave-ycsb_abgsave-ycsb_abgsave-ycsb_abgsave-ycsb_abgsave-ycsb_abgsave-ycsb_abgsave",
        "ycsb_aserver-ycsb_aserver-ycsb_aserver-ycsb_aserver-ycsb_aserver-ycsb_aserver-ycsb_aserver-ycsb_aserver",
        "ycsb_bserver-ycsb_bserver-ycsb_bserver-ycsb_bserver-ycsb_bserver-ycsb_bserver-ycsb_bserver-ycsb_bserver",
        "ycsb_cserver-ycsb_cserver-ycsb_cserver-ycsb_cserver-ycsb_cserver-ycsb_cserver-ycsb_cserver-ycsb_cserver",
        "ycsb_dserver-ycsb_dserver-ycsb_dserver-ycsb_dserver-ycsb_dserver-ycsb_dserver-ycsb_dserver-ycsb_dserver",
        "ycsb_eserver-ycsb_eserver-ycsb_eserver-ycsb_eserver-ycsb_eserver-ycsb_eserver-ycsb_eserver-ycsb_eserver"
    ]

# @returns SBATCH command used to invoke the ramulator script


def generateExecutionSetup(ramulator_dir, output_dir, trace_dir, config, workload_name_list):

    CMD = BASE_COMMAND_LINE.format(
        ramulator_dir=ramulator_dir,
    )

    ramulator_config = None
    with open("/app/"+config) as f:
        ramulator_config = yaml.load(f, Loader=yaml.FullLoader)
    bare_config = config.split('/')[-1]

    workload_name_list_dir = [(trace_dir + "/" + x)
                              for x in workload_name_list]
    ramulator_config["processor"]["trace"] = workload_name_list_dir
    if (not multicore):
        ramulator_config["processor"]["cache"]["L3"]["capacity"] = "8MB"
    else:
        ramulator_config["processor"]["cache"]["L3"]["capacity"] = str(
            int(len(workload_name_list_dir) * 2)) + "MB"
    # ramulator_config["memory"]["translation"]["type"] = "None"

    SBATCH_CMD = SBATCH_COMMAND_LINE.format(
        ramulator_dir=ramulator_dir,
        output_file_name='{output_file_name}',
        error_file_name='{error_file_name}',
        config_extension='',
        job_name='{job_name}',
        config_name=bare_config,
        workload='{workload}',
        comet_dir=comet_path
    )

    prog_list = ""

    length = len(workload_name_list)

    for j in range(length-1):
        prog_list += workload_name_list[j] + '-'

    prog_list += workload_name_list[length-1]

    stats_prefix = output_dir + '/' + bare_config + '/' + prog_list + '/'
    ramulator_config["stats"]["prefix"] = stats_prefix
    activate_dump_file_name = output_dir + '/' + \
        bare_config + '/' + prog_list + '/activate_commands.txt'
    period_dump_file_name = output_dir + '/' + bare_config + \
        '/' + prog_list + '/activate_periods.txt'
    ramulator_config["memory"]["controller"]["activation_count_dump_file"] = activate_dump_file_name
    if "refresh_based_defense" in ramulator_config["post_warmup_settings"]["memory"]["controller"]:
        ramulator_config["post_warmup_settings"]["memory"]["controller"][
            "refresh_based_defense"]["activation_period_file_name"] = period_dump_file_name
        # ramulator_config["post_warmup_settings"]["memory"]["controller"]["refresh_based_defense"]["debug"] = True

    # Finalize CMD
    CMD += "\"" + yaml.dump(ramulator_config) + "\""

    SBATCH_CMD = SBATCH_CMD.format(
        output_file_name=output_dir + '/' + bare_config + '/' + prog_list + '/output.txt',
        error_file_name=output_dir + '/' + bare_config + '/' + prog_list + '/error.txt',
        job_name=prog_list,
        workload=prog_list
    )

    if (execution_mode == "--native"):
        of_name =output_dir + '/' + bare_config + '/' + prog_list + '/output.txt'
        ef_name =output_dir + '/' + bare_config + '/' + prog_list + '/error.txt'
        temp = SBATCH_CMD.split("docker_wrapper.sh")[1]
        SBATCH_CMD = "echo \"Running: " + bare_config + " " + prog_list +"\" & ./docker_wrapper.sh " + temp + ' > ' + of_name + ' 2> ' + ef_name
        #print(SBATCH_CMD)

    os.system('mkdir -p ' + output_dir + '/' + bare_config + '/' + prog_list)

    # add write permission to the output file
    os.system('chmod uog+wr ' + output_dir + '/' + bare_config + '/' + prog_list)

    f = open("/app/run_scripts/" +
             bare_config + '-' + prog_list + '.sh', 'w')
    f.write(BASH_HEADER)
    f.write(CMD)
    f.close()

    # chmod +x /app/run_scripts/{config_name}{config_extension}-{workload}.sh
    os.system('chmod uog+x /app/run_scripts/' +
              bare_config + '-' + prog_list + '.sh')
    return SBATCH_CMD


ramulator_dir = '.'
output_dir = '/app/ae-results'
trace_dir = '/app/cputraces'

# remove scripts
os.system('rm -r ' + "/app/"+"run_scripts")

os.system('mkdir -p ' + output_dir)
os.system('mkdir -p ' + '/app/run_scripts')

all_sbatch_commands = []
all_sbatch_commands.append(BASH_HEADER)

for config in configs:
    os.system('mkdir -p ' + output_dir + '/' + config.split('/')[-1])

    for trace in traces:
        newlist = trace.split('-')
        # check if output_dir/config/trace/DDR4stats.stats is empty
        # if not, then skip
        if not os.path.exists(output_dir + '/' + config.split('/')[-1] + '/' + trace + '/DDR4stats.stats'):
            all_sbatch_commands.append(generateExecutionSetup(
                ramulator_dir, output_dir, trace_dir, config, newlist))
        elif os.path.getsize(output_dir + '/' + config.split('/')[-1] + '/' + trace + '/DDR4stats.stats') == 0:
            all_sbatch_commands.append(generateExecutionSetup(
                ramulator_dir, output_dir, trace_dir, config, newlist))
        else:
            continue


with open('/app/run.sh', 'w') as f:
    f.write('\n'.join(all_sbatch_commands))

os.system('chmod uog+x /app/run.sh')
