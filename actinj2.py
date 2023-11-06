# basic requirements:
# - the cache size should be scaled per core
# - make sure we are running all traces

import yaml
import os
import random
from argparse import ArgumentParser
import itertools
import random

BASH_HEADER = "#!/bin/bash\n"

# the command line slurm will execute
'''
SBATCH_COMMAND_LINE = "\
    sbatch --cpus-per-task=1 --nodes=1 --ntasks=1 \
    --workdir={ramulator_dir} \
    --output={output_file_name} \
    --error={error_file_name} \
    --partition=slurm_part \
    --job-name='{job_name}' \
    {ramulator_dir}/run_scripts/{config_name}{config_extension}-{workload}.sh"
'''

# the command line slurm will execute
SBATCH_COMMAND_LINE = "\
    sbatch --cpus-per-task=1 --nodes=1 --ntasks=1 \
    --chdir={ramulator_dir} \
    --output={output_file_name} \
    --error={error_file_name} \
    --partition=cpu_part \
    --job-name='{job_name}' \
    {ramulator_dir}/run_scripts/{config_name}{config_extension}-{workload}.sh"

# the script executed by the command line slurm executes
BASE_COMMAND_LINE = "\
    LD_LIBRARY_PATH=/mnt/panzer/aolgun/EXT_LIBS \
    {ramulator_dir}/ramulator "

# nRH sweep all mechanisms
RH32_configs = [
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/CoMeT500-3-RH32.yaml',
  '/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/CoMeT500-3-NM-RH32.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/CoMeT500-RH32.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/Baseline-RH32.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/Graphene500-RH32.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/REGA500-RH32.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/PARA500-RH32.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/Hydra500-RH32.yaml',
]

AH_configs = [
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/CoMeT500-3-AH.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/CoMeT500-AH.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/Baseline-AH.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/Graphene500-AH.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/REGA500-AH.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/PARA500-AH.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/Hydra500-AH.yaml',
]

AAH_configs = [
  '/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/CoMeT500-3-NM-AAH.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/CoMeT500-3-AAH.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/CoMeT500-AAH.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/Baseline-AAH.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/Graphene500-AAH.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/REGA500-AAH.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/PARA500-AAH.yaml',
  #'/mnt/panzer/fatmab/cms-ramulator/configs/ArtifactEvaluation/AttackPresent/Hydra500-AAH.yaml',
]

#AAH_configs = ['/mnt/panzer/fatmab/cms-ramulator/configs/Paragraph/AttackPresent/CMS-refresh-AAH.yaml']
#new_aah = ['/mnt/panzer/aolgun/ramulator/configs/Paragraph/Revision/Paragraph500-PerRank-GrapheneOnly-AAH-Big.yaml']
#new_ah = ['/mnt/panzer/aolgun/ramulator/configs/Paragraph/Revision/Paragraph500-PerRank-GrapheneOnly-AH-Big.yaml']
#new_rh32 = ['/mnt/panzer/aolgun/ramulator/configs/Paragraph/Revision/Paragraph500-PerRank-GrapheneOnly-RH32-Big.yaml']

traces = [
  #"random_10.trace",
  #"stream_10.trace",
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
#]
#traces = [
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
  "wc_8443", # wordcount-8443
  "wc_map0", # wordcount-map0
  "ycsb_abgsave",
  "ycsb_aserver",
  "ycsb_bserver",
  "ycsb_cserver",
  "ycsb_dserver",
  "ycsb_eserver"
]

#traces = ["519.lbm"]

LOW_RBMPKI = ['531.deepsjeng', '502.gcc', '541.leela', '435.gromacs', '481.wrf', '458.sjeng', '445.gobmk', '444.namd', '508.namd', '401.bzip2', '456.hmmer', '403.gcc', '464.h264ref', '526.blender', '447.dealII', '544.nab', '523.xalancbmk', '500.perlbench', '538.imagick', '525.x264', '507.cactuBSSN', '511.povray']
MED_RBMPKI = ['462.libquantum', '473.astar', '510.parest', '482.sphinx3', '505.mcf', '557.xz', '471.omnetpp', '483.xalancbmk', '436.cactusADM']
HIGH_RBMPKI = ['520.omnetpp', '450.soplex', '470.lbm', '519.lbm', '434.zeusmp', '433.milc', '459.GemsFDTD', '549.fotonik3d', '429.mcf', '437.leslie3d']


# @returns SBATCH command used to invoke the ramulator script
def generateExecutionSetup(ramulator_dir, output_dir, trace_dir, adversarial_trace, config, workload_name_list):

  CMD = BASE_COMMAND_LINE.format(
    ramulator_dir = ramulator_dir,
  )

  ramulator_config=None
  with open(config) as f:    
    ramulator_config = yaml.load(f, Loader=yaml.FullLoader)
  bare_config = config.split('/')[-1]

  workload_name_list_dir = [(trace_dir + "/" + x) for x in workload_name_list]
  ramulator_config["processor"]["trace"] = workload_name_list_dir
  #ramulator_config["processor"]["cache"]["L3"]["capacity"] = str(int(len(workload_name_list_dir) * 2)) + "MB"
  ramulator_config["processor"]["cache"]["L3"]["capacity"] = str(int(len(workload_name_list_dir) * 4)) + "MB"
  ramulator_config["memory"]["controller"]["act_injector"]["trace"] = trace_dir + "/" + adversarial_trace
  #ramulator_config["memory"]["controller"]["act_injector"]["trace"] = trace_dir + "/hydra_adv_1K_r500.trace" 
  ramulator_config["memory"]["controller"]["act_injector"]["debug"] = False
  # ramulator_config["memory"]["translation"]["type"] = "None"

  SBATCH_CMD = SBATCH_COMMAND_LINE.format(
    ramulator_dir = ramulator_dir,
    output_file_name = '{output_file_name}',
    error_file_name = '{error_file_name}',
    config_extension = '',
    job_name = '{job_name}',
    config_name = bare_config,
    workload = '{workload}'
  )
  
  prog_list = ""

  length = len(workload_name_list)

  for j in range(length-1):
    prog_list += workload_name_list[j] + '-'
  
  prog_list += workload_name_list[length-1]

  stats_prefix = output_dir + '/' + bare_config + '/' + prog_list + '/'
  ramulator_config["stats"]["prefix"] = stats_prefix
  activate_dump_file_name = output_dir + '/' + bare_config + '/' + prog_list + '/activate_commands.txt'
  period_dump_file_name = output_dir + '/' + bare_config + '/' + prog_list + '/activate_periods.txt'
  ramulator_config["memory"]["controller"]["activation_count_dump_file"] = activate_dump_file_name
  if "refresh_based_defense" in ramulator_config["post_warmup_settings"]["memory"]["controller"]:
    ramulator_config["post_warmup_settings"]["memory"]["controller"]["refresh_based_defense"]["activation_period_file_name"] = period_dump_file_name
    #ramulator_config["post_warmup_settings"]["memory"]["controller"]["refresh_based_defense"]["debug"] = True

  # Finalize CMD
  CMD += "\"" + yaml.dump(ramulator_config) + "\""

  SBATCH_CMD = SBATCH_CMD.format(
    output_file_name = output_dir + '/' + bare_config + '/' + prog_list + '/output.txt',
    error_file_name = output_dir + '/' + bare_config + '/' + prog_list + '/error.txt',
    job_name = prog_list,
    workload = prog_list
  )            

  os.system('mkdir -p ' + output_dir + '/' + bare_config + '/' + prog_list)

  f = open(ramulator_dir + '/run_scripts/' + bare_config + '-' + prog_list + '.sh', 'w')
  f.write(BASH_HEADER)
  f.write(CMD)
  f.close()
  
  return SBATCH_CMD


ramulator_dir = '/mnt/panzer/fatmab/cms-ramulator'
output_dir = '/mnt/panzer/fatmab/cms-ramulator/ae-results'
trace_dir = '/mnt/panzer/fatmab/cms-ramulator/cputraces'

# remove scripts
os.system('rm -r ' + ramulator_dir + '/run_scripts')

os.system('mkdir -p ' + output_dir)
os.system('mkdir -p ' + ramulator_dir + '/run_scripts')

all_sbatch_commands = []
all_sbatch_commands.append(BASH_HEADER)

'''
for config in RH32_configs:
  os.system('mkdir -p ' + output_dir + '/' + config.split('/')[-1])
  
  # single core traces
  for trace in traces:
    print(trace)
    all_sbatch_commands.append(generateExecutionSetup(ramulator_dir, output_dir, trace_dir, "rh32_new.trace", config, [trace]))

  # for workload in traces:
  #   print([workload] * 7)
  #   all_sbatch_commands.append(generateExecutionSetup(ramulator_dir, output_dir, trace_dir, config, [workload] * 7))
  
for config in AH_configs:
  os.system('mkdir -p ' + output_dir + '/' + config.split('/')[-1])
  
  # single core traces
  for trace in traces:
    print(trace)
    all_sbatch_commands.append(generateExecutionSetup(ramulator_dir, output_dir, trace_dir, "hydra_adv_1K_r500_new.trace", config, [trace]))


for config in AAH_configs:
  os.system('mkdir -p ' + output_dir + '/' + config.split('/')[-1])
  
  # single core traces
  for trace in traces:
    print(trace)
    all_sbatch_commands.append(generateExecutionSetup(ramulator_dir, output_dir, trace_dir, "SAC_adv_i32_new.trace", config, [trace]))
'''

for config in  RH32_configs:
  os.system('mkdir -p ' + output_dir + '/' + config.split('/')[-1])
  
  # single core traces
  for trace in traces:
    #print(trace)
    if not os.path.exists(output_dir + '/' + config.split('/')[-1] + '/' + trace + '/DDR4stats.stats'):
      all_sbatch_commands.append(generateExecutionSetup(ramulator_dir, output_dir, trace_dir, "rh32_new.trace", config, [trace]))
      continue
    if os.path.getsize(output_dir + '/' + config.split('/')[-1] + '/' + trace + '/DDR4stats.stats') == 0:
      all_sbatch_commands.append(generateExecutionSetup(ramulator_dir, output_dir, trace_dir, "rh32_new.trace", config, [trace]))
    else:
      continue
      
for config in AH_configs:
  os.system('mkdir -p ' + output_dir + '/' + config.split('/')[-1])
  
  # single core traces
  for trace in traces:
    #print(trace)
    if not os.path.exists(output_dir + '/' + config.split('/')[-1] + '/' + trace + '/DDR4stats.stats'):
      all_sbatch_commands.append(generateExecutionSetup(ramulator_dir, output_dir, trace_dir, "hydra_adv_1K_r500_new.trace", config, [trace]))
      continue
    if os.path.getsize(output_dir + '/' + config.split('/')[-1] + '/' + trace + '/DDR4stats.stats') == 0:
      all_sbatch_commands.append(generateExecutionSetup(ramulator_dir, output_dir, trace_dir, "hydra_adv_1K_r500_new.trace", config, [trace]))
    else:
      continue

for config in AAH_configs:
  os.system('mkdir -p ' + output_dir + '/' + config.split('/')[-1])
  
  # single core traces
  for trace in traces:
    #print(trace)
    if not os.path.exists(output_dir + '/' + config.split('/')[-1] + '/' + trace + '/DDR4stats.stats'):
      #print(output_dir.replace("/mnt/panzer/fatmab/cms-ramulator/","") + '/' + config.split('/')[-1] + '/' + trace + '/DDR4stats.stats')
      all_sbatch_commands.append(generateExecutionSetup(ramulator_dir, output_dir, trace_dir, "comet_adv.trace", config, [trace]))
      #all_sbatch_commands.append(generateExecutionSetup(ramulator_dir, output_dir, trace_dir, config, newlist))
      continue
    if os.path.getsize(output_dir + '/' + config.split('/')[-1] + '/' + trace + '/DDR4stats.stats') == 0:
      # print the path of the empty file
      #print(output_dir.replace("/mnt/panzer/fatmab/cms-ramulator/","") + '/' + config.split('/')[-1] + '/' + trace + '/DDR4stats.stats')
      all_sbatch_commands.append(generateExecutionSetup(ramulator_dir, output_dir, trace_dir, "comet_adv.trace", config, [trace]))
      #all_sbatch_commands.append(generateExecutionSetup(ramulator_dir, output_dir, trace_dir, config, newlist))
    else:
      continue
    #all_sbatch_commands.append(generateExecutionSetup(ramulator_dir, output_dir, trace_dir, "comet_adv.trace", config, [trace]))

with open('run.sh', 'w') as f:
  f.write('\n'.join(all_sbatch_commands))

os.system('chmod uog+x run.sh')
# print("REMEMBER TO CHANGE TRANSLATION")
