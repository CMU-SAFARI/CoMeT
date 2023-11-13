### READ RESULTS INTO PANDAS DATAFRAME
import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
import argparse
import sys 
import re

parser = argparse.ArgumentParser()

# -rd resultsdir -v verbose -s saveSummary 
parser.add_argument('-r', '--resultsdir', help='Results directory', required=False, default='../../../ae-results/')
parser.add_argument('-v', '--verbose', help='Verbose', action='store_true', default=False)
parser.add_argument('-s', '--saveSummary', help='save summaries as csv files', action='store_true', default=False)

args = parser.parse_args()

resultsdir = args.resultsdir # This needs to be updated if the results are not in the same directory 
print('[INFO] Reading results from: {}'.format(resultsdir))
print('[INFO] Plots and results will be saved to: ./plots/')
# create plots directory
if not os.path.exists('plots'):
    os.makedirs('plots')

print('[INFO] Plotting single-core performance evaluation plots.')

# list all directories in resultsdir
configs = ['Baseline.yaml',
            'CoMeT125-3.yaml',
            'CoMeT250-3.yaml',
            'CoMeT500-3.yaml',
            'CoMeT1000-3.yaml',
        ]
# print found configs
#print('Found configs: {}'.format(configs))
# list all directories under all configs
workloads = []
for c in configs:
    workloads.append([d for d in os.listdir(os.path.join(resultsdir, c)) if os.path.isdir(os.path.join(resultsdir, c, d))])
# find only the intersection of all workloads
workloads = list(set.intersection(*map(set, workloads)))
# print found workloads
#print('Found workloads: {}'.format(workloads))

stats_per_config_workload = []

# for every config + workload directory
for c in configs:
    for w in workloads:
        # find all files in the directory
        files = [f for f in os.listdir(os.path.join(resultsdir, c, w)) if os.path.isfile(os.path.join(resultsdir, c, w, f))]
        # find the stats file
        stat_files = [f for f in files if f.endswith('.stats')]
        # if there is a stats file
        if stat_files:
            for stat_file in stat_files:
                # if the stats_file has less than three lines skip it
                if len(open(os.path.join(resultsdir, c, w, stat_file)).readlines()) < 3:
                    continue
                
                # print the name of the stats_file
                if args.verbose:
                  print('Found stats file: {}'.format(os.path.join(os.path.join(resultsdir, c, w, stat_file))))

                extension = ''
                # if stats_file file name itself does not start with DDR4, parse it a bit
                if not stat_file.startswith('DDR4'):
                    # get the config name from the stats_file name
                    extension = '_'.join(stat_file.split('_')[:-1])
                    # prepend underscore to extension
                    extension = '_' + extension

                # read the stats file, name columns: 'name', 'value', 'description'
                df = pd.read_csv(os.path.join(resultsdir, c, w, stat_file), header=None).T
                df.columns = df.iloc[0]
                df.drop(0,inplace=True)
                # add a new column called 'config' with the config name
                df['config'] = c + extension
                # add a new column called 'workload' with the workload name
                df['workload'] = w
                # print the stats file
                # print('Config: {}, Workload: {}, Stats: {}'.format(c, w, df))
                # append the stats to the list
                df.reset_index(inplace=True, drop=True)
                stats_per_config_workload.append(df)
        else:
            if args.verbose:
              print('Config: {}, Workload: {}, Stats: No stats file found'.format(c, w))

# concatenate all stats into one dataframe
stats = pd.concat(stats_per_config_workload)

# find elements where workload does not contain '-'
# these are multi core workloads
stats = stats[~stats['workload'].str.contains('-')]

# remove these two workloads: stream_10.trace and random_10.trace
stats = stats[~stats['workload'].isin(['stream10_200.trace', 'random10_200.trace'])]
# also from workloads
workloads = [w for w in workloads if not w in ['stream10_200', 'random10_200.trace']]

#remove configs that has RH32, AH and AAH in the name
stats = stats[~stats['config'].str.contains('RH32')]
stats = stats[~stats['config'].str.contains('AH')]
stats = stats[~stats['config'].str.contains('AAH')]

# replace 'Baseline' with 'Baseline0'
stats['config'] = stats['config'].str.replace('ae-results/', '')
stats['config'] = stats['config'].str.replace('../results/', '')
stats['config'] = stats['config'].str.replace('Baseline', 'Baseline0')
stats['config'] = stats['config'].str.replace('-4-512-128', '')
stats['config'] = stats['config'].str.replace('-2', '')
stats['config'] = stats['config'].str.replace('-3', '')
stats['config'] = stats['config'].str.replace('-1', '')
stats['config'] = stats['config'].str.replace('-m25', '')

# add a new column that stores in integer the number in the config name
stats['nrh'] = stats['config'].str.extract('(\d+)').astype(int)

# remove numbers from config names
stats['config'] = stats['config'].str.replace('\d+', '')

# remove yaml from config names
stats['config'] = stats['config'].str.replace('.yaml', '')

stats_copy = stats.copy()

# use seaborn-deep style
sns.set(font_scale=1.0)
sns.set_style("whitegrid")
sns.set_palette("pastel", n_colors=4)

stats = stats_copy.copy()



# instructions per cycle (IPC) is record_cycles_insts_0 / record_cycs_core_0
stats['ramulator.ipc'] = stats['ramulator.record_insts_core_0'] / stats['ramulator.record_cycs_core_0']


stats['ramulator.rbmpki'] = (stats['ramulator.row_conflicts_channel_0_core'] + stats['ramulator.row_misses_channel_0_core']) /\
                            stats['ramulator.record_insts_core_0'] * 1000


# copy the IPC of the baseline config as to all configs
baseline = stats[stats['config'] == 'Baseline0']
baseline = baseline[['workload', 'ramulator.ipc', 'ramulator.read_latency_avg_0', 'ramulator.rbmpki', 'ramulator.window_full_stall_cycles_core_0']]
# baseline
baseline.columns = ['workload', 'ramulator.baseline_ipc', 'ramulator.baseline_read_latency_avg_0', 'ramulator.baseline_rbmpki', 'ramulator.baseline_stall_cycles']

stats = pd.merge(stats, baseline, on='workload')


stats['ramulator.normalized_ipc'] = stats['ramulator.ipc'] / stats['ramulator.baseline_ipc']
stats['ramulator.normalized_read_latency'] = stats['ramulator.read_latency_avg_0'] / stats['ramulator.baseline_read_latency_avg_0']
stats['ramulator.normalized_stall_cycles'] = stats['ramulator.window_full_stall_cycles_core_0'] / stats['ramulator.baseline_stall_cycles']
stats['ramulator.normalized_rbmpki'] = stats['ramulator.rbmpki'] / stats['ramulator.baseline_rbmpki']


# add the geometric normalized ipc average as a new workload to every config
geometric_mean = stats.groupby(['config','nrh'])['ramulator.normalized_ipc'].apply(lambda x: x.prod()**(1.0/len(x))).reset_index()
geometric_mean['workload'] = 'GeoMean'


stats = pd.concat([stats, geometric_mean])

stats_clean = stats.copy()

# create a copy of stats with the columns config, workload, normalized_ipc
stats_summary = stats[['config', 'workload', 'ramulator.normalized_ipc','nrh']].copy()

if args.saveSummary:
    # print to csv fiile
    stats_summary.to_csv('singlecore-summary.csv', index=False)

order = ['GeoMean', 'h264_encode', '511.povray', '481.wrf', '541.leela', '538.imagick', '444.namd', '447.dealII', '464.h264ref', '456.hmmer', '403.gcc', '526.blender', '544.nab', '525.x264', '508.namd', 'grep_map0', '531.deepsjeng', '458.sjeng', '435.gromacs', '445.gobmk', '401.bzip2', '507.cactuBSSN', '502.gcc', 'ycsb_abgsave', 'tpch6', '500.perlbench', '523.xalancbmk', 'ycsb_dserver', 'ycsb_cserver', '510.parest', 'ycsb_bserver', 'ycsb_eserver', 'tpcc64', 'ycsb_aserver', '557.xz', '482.sphinx3', 'jp2_decode', '505.mcf', 'wc_8443', 'wc_map0', '436.cactusADM', '471.omnetpp', '473.astar', 'jp2_encode', 'tpch17', '483.xalancbmk', '462.libquantum', 'tpch2', '433.milc', '520.omnetpp', '437.leslie3d', '450.soplex', '459.GemsFDTD', '549.fotonik3d', '434.zeusmp', '519.lbm', '470.lbm', '429.mcf', 'h264_decode', 'bfs_ny', 'bfs_cm2003', 'bfs_dblp']

stats['workload'] = pd.Categorical(stats['workload'], categories=order, ordered=True)


# add comet's palette 
comet_palette = [ '#785EF0', '#DC267F', '#FE6100', '#FFB000']
sns.set_palette(comet_palette, n_colors=4)

#barplot of normalized IPC, also draw edges around bars
fig, ax = plt.subplots(figsize=(15, 4))
if args.saveSummary:
    stats_summary.to_csv('singlecore-fullresults.csv', index=False)

LOW_RBMPKI = ['531.deepsjeng', '502.gcc', '541.leela', '435.gromacs', '481.wrf', '458.sjeng', '445.gobmk', '444.namd', '508.namd', '401.bzip2', '456.hmmer', '403.gcc', '464.h264ref', '526.blender', '447.dealII', '544.nab', '523.xalancbmk', '500.perlbench', '538.imagick', '525.x264', '507.cactuBSSN', '511.povray']
order = ['GeoMean', 'h264_encode', '511.povray', '481.wrf', '541.leela', '538.imagick', '444.namd', '447.dealII', '464.h264ref', '456.hmmer', '403.gcc', '526.blender', '544.nab', '525.x264', '508.namd', 'grep_map0', '531.deepsjeng', '458.sjeng', '435.gromacs', '445.gobmk', '401.bzip2', '507.cactuBSSN', '502.gcc', 'ycsb_abgsave', 'tpch6', '500.perlbench', '523.xalancbmk', 'ycsb_dserver', 'ycsb_cserver', '510.parest', 'ycsb_bserver', 'ycsb_eserver', 'tpcc64', 'ycsb_aserver', '557.xz', '482.sphinx3', 'jp2_decode', '505.mcf', 'wc_8443', 'wc_map0', '436.cactusADM', '471.omnetpp', '473.astar', 'jp2_encode', 'tpch17', '483.xalancbmk', '462.libquantum', 'tpch2', '433.milc', '520.omnetpp', '437.leslie3d', '450.soplex', '459.GemsFDTD', '549.fotonik3d', '434.zeusmp', '519.lbm', '470.lbm', '429.mcf', 'h264_decode', 'bfs_ny', 'bfs_cm2003', 'bfs_dblp']
# remove the workloads that are not in LOW_RBMPKI
order = [x for x in order if not (x in LOW_RBMPKI)]

stats['workload'] = pd.Categorical(stats['workload'], categories=order, ordered=True)

# create a stats copy
stats_reduced = stats.copy()

# remove workloads that are not in MED RBMPKI and HIGH RBMPKI
stats_reduced = stats_reduced[~stats_reduced['workload'].isin(LOW_RBMPKI)]


#set color palette
#sns.set_palette("viridis", n_colors=4)

# add comet's palette '#648FFF',
comet_palette = [ '#785EF0', '#DC267F', '#FE6100', '#FFB000']
sns.set_palette(comet_palette, n_colors=4)

#barplot of normalized IPC, also draw edges around bars
fig, ax = plt.subplots(figsize=(10, 4))

ax = sns.barplot(x='workload', y='ramulator.normalized_ipc', hue='nrh', data=stats_reduced[(stats_reduced['config']!='Baseline0')], edgecolor='black', linewidth=0.5)


#stats[(stats['config'] == 'CMS1000-100-c')].to_csv('cms_performance_single_core.csv', index=False)

ax.set_xlabel('Workload')
ax.set_ylabel('Normalized IPC')
# move ylabel down
ax.yaxis.set_label_coords(-0.045,0.45)
# draw a red line at y = 1.0, label it as baseline IPC
ax.axhline(y=1.0, color='r', linestyle='--')
# write above the red line 'baseline IPC' using the same pastel red color
#ax.text(0.01, 0.7, 'baseline IPC', color='#e74c3c', transform=ax.transAxes, fontsize=15)
# extend the y axis to 1.2
ax.set_ylim(0.6, 1.1)
# color the 5th y tick red
#ax.get_yticklabels()[3].set_color('#e74c3c')
# rotate x axis ticks
ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
# make axis tick font bigger
ax.tick_params(axis='both', which='major', labelsize=11)
ax.tick_params(axis='y', which='major', labelsize=12)

ax.axvline(x=0.5, color='grey', linestyle='-', linewidth=0.5)


# make x and y axis labels bigger
ax.xaxis.label.set_size(16)
#ax.yaxis.label.set_fontweight('bold')
ax.yaxis.label.set_size(16)
#ax.xaxis.label.set_fontweight('bold')

# put the legend on top of the plot
ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1), ncol=4, fancybox=False, shadow=False, framealpha=1, fontsize=12)
# prepend "nRH" to legend names
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, ['$N_{RH}$ = ' + label for label in labels], loc='upper center', bbox_to_anchor=(0.5, 1.1), ncol=6, fancybox=True, shadow=False, framealpha=1, fontsize=12)

# highlight the geometric mean ax label
ax.get_xticklabels()[0].set_fontweight('bold')

plt.tight_layout()
plt.show()

# save figure
fig.savefig('plots/comet-singlecore.pdf', bbox_inches='tight')

print('[INFO] Plot available: comet-singlecore.pdf (Figure 8)')

# print numbers for the paper
stats_copy = stats.copy()

print('[INFO] Printing single-core performance numbers to singlecore-performance-numbers.txt')

# redirect stdout to a file
sys.stdout = open('plots/singlecore-performance-numbers.txt', 'w')

print("====\nnRH=1k, CoMeT\'s AVERAGE Performance Overhead (%):")
print((1-(stats_clean[(stats_clean['config']=='CoMeT1000') & (stats_clean['nrh']==1000) & (stats_clean['workload']=='GeoMean')]['ramulator.normalized_ipc'].values[0]))*100)

print("====\nnRH=1k, CoMeT\'s MAXIMUM Performance Overhead (%):")
print((1-(stats_clean[(stats_clean['config']=='CoMeT1000') & (stats_clean['nrh']==1000)]['ramulator.normalized_ipc'].min()))*100)

print("====\nnRH=125, CoMeT\'s AVERAGE Performance Overhead (%):")
print((1-(stats_clean[(stats_clean['config']=='CoMeT125') & (stats_clean['nrh']==125) & (stats_clean['workload']=='GeoMean')]['ramulator.normalized_ipc'].values[0]))*100)
print("====\nnRH=125, CoMeT\'s MAXIMUM Performance Overhead (%):")
print((1-(stats_clean[(stats_clean['config']=='CoMeT125') & (stats_clean['nrh']==125)]['ramulator.normalized_ipc'].min()))*100)


print("====\nnRH=1k, CoMeT\'s AVERAGE Normalized Read Latency at nRH=1k (%):")
print(((stats_clean[(stats_clean['config']=='CoMeT1000') & (stats_clean['nrh']==1000)]['ramulator.normalized_read_latency']).mean()-1)*100)
print("====\nnRH=1k, CoMeT\'s AVERAGE Normalized Read Latency at nRH=125 (%):")
print(((stats_clean[(stats_clean['config']=='CoMeT125') & (stats_clean['nrh']==125)]['ramulator.normalized_read_latency']).mean()-1)*100)

# redirect stdout back to terminal
sys.stdout = sys.__stdout__

print('[INFO] Numbers available: singlecore-performance-numbers.txt')
print("=======================================")
print('[INFO] Plotting single-core performance comparison plot. This may take a while.')

configs = ['Baseline.yaml',
            'CoMeT125-3.yaml',
            'CoMeT250-3.yaml',
            'CoMeT500-3.yaml',
            'CoMeT1000-3.yaml',
            'Graphene1000.yaml',
            'Graphene500.yaml',
            'Graphene250.yaml',
            'Graphene125.yaml',
            'Hydra1000.yaml',
            'Hydra500.yaml',
            'Hydra250.yaml',
            'Hydra125.yaml',
            'REGA1000.yaml',
            'REGA500.yaml',
            'REGA250.yaml',
            'REGA125.yaml',
            'PARA1000.yaml',
            'PARA500.yaml',
            'PARA250.yaml',
            'PARA125.yaml',
        ]
#configs = ['Baseline.yaml', 'CMS1000-100.yaml', 'Graphene1000.yaml', 'CMS1000-100-c.yaml']
# list all directories under all configs
workloads = []
for c in configs:
    workloads.append([d for d in os.listdir(os.path.join(resultsdir, c)) if os.path.isdir(os.path.join(resultsdir, c, d))])
# find only the intersection of all workloads
workloads = list(set.intersection(*map(set, workloads)))

stats_per_config_workload = []

# for every config + workload directory
for c in configs:
    for w in workloads:
        # find all files in the directory
        files = [f for f in os.listdir(os.path.join(resultsdir, c, w)) if os.path.isfile(os.path.join(resultsdir, c, w, f))]
        # find the stats file
        stat_files = [f for f in files if f.endswith('.stats')]
        # if there is a stats file
        if stat_files:
            for stat_file in stat_files:
                # if the stats_file has less than three lines skip it
                if len(open(os.path.join(resultsdir, c, w, stat_file)).readlines()) < 3:
                    continue
                
                if args.verbose:
                    # print the name of the stats_file
                    print('Found stats file: {}'.format(os.path.join(os.path.join(resultsdir, c, w, stat_file))))

                extension = ''
                # if stats_file file name itself does not start with DDR4, parse it a bit
                if not stat_file.startswith('DDR4'):
                    # get the config name from the stats_file name
                    extension = '_'.join(stat_file.split('_')[:-1])
                    # prepend underscore to extension
                    extension = '_' + extension

                # read the stats file, name columns: 'name', 'value', 'description'
                df = pd.read_csv(os.path.join(resultsdir, c, w, stat_file), header=None).T
                df.columns = df.iloc[0]
                df.drop(0,inplace=True)
                # add a new column called 'config' with the config name
                df['config'] = c + extension
                # add a new column called 'workload' with the workload name
                df['workload'] = w
                # print the stats file
                # print('Config: {}, Workload: {}, Stats: {}'.format(c, w, df))
                # append the stats to the list
                df.reset_index(inplace=True, drop=True)
                stats_per_config_workload.append(df)
        else:
            if args.verbose:
                print('Config: {}, Workload: {}, Stats: No stats file found'.format(c, w))

# concatenate all stats into one dataframe
stats = pd.concat(stats_per_config_workload)

# find elements where workload does not contain '-'
# these are multi core workloads
stats = stats[~stats['workload'].str.contains('-')]

# remove these two workloads: stream_10.trace and random_10.trace
stats = stats[~stats['workload'].isin(['stream10_200.trace', 'random10_200.trace'])]
# also from workloads
workloads = [w for w in workloads if not w in ['stream10_200', 'random10_200.trace']]

#remove configs that has RH32, AH and AAH in the name
stats = stats[~stats['config'].str.contains('RH32')]
stats = stats[~stats['config'].str.contains('AH')]
stats = stats[~stats['config'].str.contains('AAH')]

# replace 'Baseline' with 'Baseline0'
stats['config'] = stats['config'].str.replace('ae-results/', '')
stats['config'] = stats['config'].str.replace('../results/', '')
stats['config'] = stats['config'].str.replace('Baseline', 'Baseline0')
stats['config'] = stats['config'].str.replace('-4-512-128', '')
stats['config'] = stats['config'].str.replace('-3', '')
stats['config'] = stats['config'].str.replace('-1', '')
stats['config'] = stats['config'].str.replace('-2', '')
stats['config'] = stats['config'].str.replace('-m25', '')

# add a new column that stores in integer the number in the config name
stats['nrh'] = stats['config'].str.extract('(\d+)').astype(int)

# remove numbers from config names
stats['config'] = stats['config'].str.replace('\d+', '')

# remove yaml from config names
stats['config'] = stats['config'].str.replace('.yaml', '')

stats_copy = stats.copy()

# use seaborn-deep style
sns.set(font_scale=1.0)
sns.set_style("whitegrid")
sns.set_palette("pastel", n_colors=4)

stats = stats_copy.copy()

# instructions per cycle (IPC) is record_cycles_insts_0 / record_cycs_core_0
stats['ramulator.ipc'] = stats['ramulator.record_insts_core_0'] / stats['ramulator.record_cycs_core_0']


stats['ramulator.rbmpki'] = (stats['ramulator.row_conflicts_channel_0_core'] + stats['ramulator.row_misses_channel_0_core']) /\
                            stats['ramulator.record_insts_core_0'] * 1000


# copy the IPC of the baseline config as to all configs
baseline = stats[stats['config'] == 'Baseline0']
baseline = baseline[['workload', 'ramulator.ipc', 'ramulator.read_latency_avg_0', 'ramulator.rbmpki', 'ramulator.window_full_stall_cycles_core_0']]
# baseline
baseline.columns = ['workload', 'ramulator.baseline_ipc', 'ramulator.baseline_read_latency_avg_0', 'ramulator.baseline_rbmpki', 'ramulator.baseline_stall_cycles']

stats = pd.merge(stats, baseline, on='workload')


stats['ramulator.normalized_ipc'] = stats['ramulator.ipc'] / stats['ramulator.baseline_ipc']
stats['ramulator.normalized_read_latency'] = stats['ramulator.read_latency_avg_0'] / stats['ramulator.baseline_read_latency_avg_0']
stats['ramulator.normalized_stall_cycles'] = stats['ramulator.window_full_stall_cycles_core_0'] / stats['ramulator.baseline_stall_cycles']
stats['ramulator.normalized_rbmpki'] = stats['ramulator.rbmpki'] / stats['ramulator.baseline_rbmpki']


# add the geometric normalized ipc average as a new workload to every config
geometric_mean = stats.groupby(['config','nrh'])['ramulator.normalized_ipc'].apply(lambda x: x.prod()**(1.0/len(x))).reset_index()
geometric_mean['workload'] = 'GeoMean'

stats = pd.concat([stats, geometric_mean])

# create a copy of stats with the columns config, workload, normalized_ipc
stats_summary = stats[['config', 'workload', 'ramulator.normalized_ipc','nrh']].copy()
if args.saveSummary:
    # print to csv fiile
    stats_summary.to_csv('singlecore-comparison-summary.csv', index=False)


order = ['GeoMean', 'h264_encode', '511.povray', '481.wrf', '541.leela', '538.imagick', '444.namd', '447.dealII', '464.h264ref', '456.hmmer', '403.gcc', '526.blender', '544.nab', '525.x264', '508.namd', 'grep_map0', '531.deepsjeng', '458.sjeng', '435.gromacs', '445.gobmk', '401.bzip2', '507.cactuBSSN', '502.gcc', 'ycsb_abgsave', 'tpch6', '500.perlbench', '523.xalancbmk', 'ycsb_dserver', 'ycsb_cserver', '510.parest', 'ycsb_bserver', 'ycsb_eserver', 'tpcc64', 'ycsb_aserver', '557.xz', '482.sphinx3', 'jp2_decode', '505.mcf', 'wc_8443', 'wc_map0', '436.cactusADM', '471.omnetpp', '473.astar', 'jp2_encode', 'tpch17', '483.xalancbmk', '462.libquantum', 'tpch2', '433.milc', '520.omnetpp', '437.leslie3d', '450.soplex', '459.GemsFDTD', '549.fotonik3d', '434.zeusmp', '519.lbm', '470.lbm', '429.mcf', 'h264_decode', 'bfs_ny', 'bfs_cm2003', 'bfs_dblp']

stats['workload'] = pd.Categorical(stats['workload'], categories=order, ordered=True)

sns.set(font_scale=1.0)
sns.set_style("whitegrid")
#sns.set_palette("viridis", n_colors=5)

# sns set color palette
comet_palette = ['#648FFF', '#785EF0', '#DC267F', '#FE6100', '#FFB000']
sns.set_palette(comet_palette, n_colors=5)

# drop all configs except the ones with CMS 
stats_no_baseline = stats[stats['config'].str.contains('CoMeT')]
stats_comparison = stats[~stats['config'].str.contains('CoMeT')]


# change all configs with name starting with CMS to CMS
stats_no_baseline['config'] = stats_no_baseline['config'].apply(lambda x: 'CoMeT' if re.search(r'CoMeT\d+', x) else x)

# remove all config integers from stats_comparison
stats_comparison['config'] = stats_comparison['config'].apply(lambda x: re.sub(r'\d+', '', x))


# merge stats_comparison and stats_no_baseline
stats_new = pd.concat([stats_comparison, stats_no_baseline])

# remove config Baseline0 from stats_no_baseline
stats_new = stats_new[~stats_new['config'].str.contains('Baseline')]


stats_new['nrh'] = pd.Categorical(stats_new['nrh'], categories=[1000,500,250,125], ordered=True)

# order config in this order: CMS, Graphene
stats_new['config'] = pd.Categorical(stats_new['config'], categories=['Graphene','CoMeT', 'Hydra', 'REGA', 'PARA'], ordered=True)

#boxplot of normalized IPC
fig, ax = plt.subplots(figsize=(10, 4))
# show mean values as well
ax = sns.boxplot(x="nrh", y="ramulator.normalized_ipc", hue="config", data=stats_new, showmeans=True,
                  meanprops={"marker":"o","markerfacecolor":"white", "markeredgecolor":"black"}, showfliers=True, 
                  flierprops={'marker': 'x', 'markerfacecolor': 'black', 'markeredgecolor': 'black'})
ax.set_xlabel('RowHammer Threshold')
ax.set_ylabel('Normalized\nIPC Distribution')
# draw a red line at y = 1.0, label it as baseline IPC
ax.axhline(y=1.0, color='r', linestyle='--')
# extend the y axis to 1.2
ax.set_ylim(0, 1.1)
# make axis tick font bigger
ax.tick_params(axis='both', which='major', labelsize=14)
# draw vertical lines to separate the rowhammer threshold values
ax.axvline(x=0.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=1.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=2.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=3.5, color='grey', linestyle='-', alpha=0.5)
# make x and y axis labels bigger
ax.xaxis.label.set_size(16)
ax.yaxis.label.set_size(16)

# Customize the whiskers and borders
ax.lines[0].set_color('black')  # Set the color of the whiskers\

ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2), ncol=5, fancybox=False, shadow=False, fontsize=12, framealpha=1)

plt.tight_layout()
plt.show()

# save figure
fig.savefig('plots/comet-singlecore-comparison.pdf', bbox_inches='tight')
print('[INFO] Plot available: comet-singlecore-comparison.pdf (Figure 10)')

if args.saveSummary:
    # export data to csv
    stats_no_baseline.to_csv('singlecore-comparison-fullresults.csv', index=False)

print('[INFO] Printing single-core performance comparison numbers to singlecore-comparison-numbers.txt')

# redirect stdout to a file
sys.stdout = open('plots/singlecore-comparison-numbers.txt', 'w')

stats_copy = stats.copy()
stats = stats_new.copy()
comet_1k = (stats[(stats['config']=='CoMeT') & (stats['nrh']==1000) & (stats['workload']=='GeoMean')]['ramulator.normalized_ipc'])
graphene_1k = (stats[(stats['config']=='Graphene') & (stats['nrh']==1000) & (stats['workload']=='GeoMean')]['ramulator.normalized_ipc'])
hydra_1k =((stats[(stats['config']=='Hydra') & (stats['nrh']==1000) & (stats['workload']=='GeoMean')]['ramulator.normalized_ipc']))
rega_1k = ((stats[(stats['config']=='REGA') & (stats['nrh']==1000) & (stats['workload']=='GeoMean')]['ramulator.normalized_ipc']))
para_1k = ((stats[(stats['config']=='PARA') & (stats['nrh']==1000) & (stats['workload']=='GeoMean')]['ramulator.normalized_ipc']))
comet_125 = ((stats[(stats['config']=='CoMeT') & (stats['nrh']==125) & (stats['workload']=='GeoMean')]['ramulator.normalized_ipc']))
graphene_125 =((stats[(stats['config']=='Graphene') & (stats['nrh']==125) & (stats['workload']=='GeoMean')]['ramulator.normalized_ipc']))
hydra_125 = (stats[(stats['config']=='Hydra') & (stats['nrh']==125) & (stats['workload']=='GeoMean')]['ramulator.normalized_ipc'])
rega_125 = (stats[(stats['config']=='REGA') & (stats['nrh']==125)& (stats['workload']=='GeoMean')]['ramulator.normalized_ipc'])
para_125 = ((stats[(stats['config']=='PARA') & (stats['nrh']==125) & (stats['workload']=='GeoMean')]['ramulator.normalized_ipc']))

print("nRH=125, REGA performance overhead (%): " + str((1-(rega_125.values[0]))*100))
# get the normalized ipc value of comet_1k
print("nRH=1k, CoMeT/Graphene (%): " + str((1-(comet_1k.values[0]/graphene_1k.values[0]))*100))
print("nRH=125, CoMeT/Graphene (%): " + str((1-(comet_125.values[0]/graphene_125.values[0]))*100))

c125 = stats[(stats['config']=='CoMeT') & (stats['nrh']==1000) & (stats['workload']=='GeoMean')]['ramulator.normalized_ipc']
h125 = stats[(stats['config']=='Hydra') & (stats['nrh']==1000) & (stats['workload']=='GeoMean')]['ramulator.normalized_ipc']
#print('------\nCoMeT nrh=1k AVERAGE Performance Overhead:\n' + str((1-c125.values[0])*100))
print('nrh=1k, Hydra AVERAGE Performance Overhead (%):' + str((1-h125.values[0])*100))

c125 = stats[(stats['config']=='CoMeT') & (stats['nrh']==125) & (stats['workload']=='GeoMean')]['ramulator.normalized_ipc']
h125 = stats[(stats['config']=='Hydra') & (stats['nrh']==125) & (stats['workload']=='GeoMean')]['ramulator.normalized_ipc']
#print('------\nCoMeT nrh=125 AVERAGE Performance Overhead:\n' + str((1-c125.values[0])*100))
print('nrh=125, Hydra AVERAGE Performance Overhead (%):' + str((1-h125.values[0])*100))


comet_w_15 = ((stats[(stats['config']=='CoMeT')& (stats['nrh']==125) ]['ramulator.normalized_ipc'].min()))
hydra_w_15 = ((stats[(stats['config']=='Hydra')& (stats['nrh']==125) ]['ramulator.normalized_ipc'].min()))
#print('CoMeT min normalized ipc: ' + str(comet_w_15))
#print('Hydra min normalized ipc: ' + str(hydra_w_15))
print('Hydra/CoMeT: ' + str((1-hydra_w_15/comet_w_15)*100))

preventive_refresh_125 = (stats[(stats['config']=='Graphene')& (stats['nrh'] == 125)]['ramulator.preventive_refreshes_channel_0_core']).mean()
preventive_refresh_1k = (stats[(stats['config']=='Graphene')& (stats['nrh'] == 1000)]['ramulator.preventive_refreshes_channel_0_core']).mean()
#print("Preventive refresh for Graphene: ", preventive_refresh_125)
preventive_refresh_125_comet = (stats[(stats['config']=='CoMeT') & (stats['nrh'] == 125)]['ramulator.preventive_refreshes_channel_0_core']).mean()
print("Preventive refresh for CoMeT125 (normalized to Graphene): ", (preventive_refresh_125_comet/preventive_refresh_125-1)*100)
preventive_refresh_1k_comet = (stats[(stats['config']=='CoMeT') & (stats['nrh'] == 1000)]['ramulator.preventive_refreshes_channel_0_core']).mean()
print("Preventive refresh for CoMeT1000 (normalized to Graphene): ", (preventive_refresh_1k_comet/preventive_refresh_1k-1)*100)

preventive_refres_125_hydra = (stats[(stats['config']=='Hydra') & (stats['nrh'] == 125)]['ramulator.preventive_refreshes_channel_0_core']).mean()
print("Preventive refresh for Hydra125 (normalized to Graphene): ", preventive_refres_125_hydra/preventive_refresh_125)
preventive_refres_1k_hydra = (stats[(stats['config']=='Hydra') & (stats['nrh'] == 1000)]['ramulator.preventive_refreshes_channel_0_core']).mean()
print("Preventive refresh for Hydra1000 (normalized to Graphene): ", preventive_refres_1k_hydra/preventive_refresh_1k)

rbmpki = (stats[(stats['config']=='Hydra')]['ramulator.normalized_rbmpki']).mean()
rbmpki_c = (stats[(stats['config']=='CoMeT')]['ramulator.normalized_rbmpki']).mean()
rbmpki_g = (stats[(stats['config']=='Graphene')]['ramulator.normalized_rbmpki']).mean()
print("RBMPKI Hydra125: ", rbmpki)
print("RBMPKI Graphene125: ", rbmpki_g)
print("RBMPKI CoMeT125: ", rbmpki_c)


latency_h = (stats[(stats['config']=='Hydra')]['ramulator.read_latency_avg_0']).mean()
latency_c = (stats[(stats['config']=='CoMeT')]['ramulator.read_latency_avg_0']).mean()
latency_g = (stats[(stats['config']=='Graphene')]['ramulator.read_latency_avg_0']).mean()
print("Read Latency Hydra125: ", latency_h)
print("Read Latency Graphene125: ",latency_g)
print("Read Latency CoMeT125: ",latency_c)

# redirect stdout back to terminal
sys.stdout = sys.__stdout__

print('[INFO] Numbers available: singlecore-comparison-numbers.txt')


print("=======================================")
print('[INFO] Plotting single-core DRAM energy consumption.')

configs = ['Baseline.yaml',
            'CoMeT125-3.yaml',
            'CoMeT250-3.yaml',
            'CoMeT500-3.yaml',
            'CoMeT1000-3.yaml',
            'Graphene1000.yaml',
            'Graphene500.yaml',
            'Graphene250.yaml',
            'Graphene125.yaml',
            'Hydra1000.yaml',
            'Hydra500.yaml',
            'Hydra250.yaml',
            'Hydra125.yaml',
            'REGA1000.yaml',
            'REGA500.yaml',
            'REGA250.yaml',
            'REGA125.yaml',
            'PARA1000.yaml',
            'PARA500.yaml',
            'PARA250.yaml',
            'PARA125.yaml',]

# list all directories under all configs
workloads = []
for c in configs:
    workloads.append([d for d in os.listdir(os.path.join(resultsdir, c)) if os.path.isdir(os.path.join(resultsdir, c, d))])
# find only the intersection of all workloads
workloads = list(set.intersection(*map(set, workloads)))

stats_per_config_workload = []

# for every config + workload directory
for c in configs:
    for w in workloads:
        # find all files in the directory
        files = [f for f in os.listdir(os.path.join(resultsdir, c, w)) if os.path.isfile(os.path.join(resultsdir, c, w, f))]
        # find the stats file
        stat_files = [f for f in files if f.endswith('output.txt')]
        # if there is a stats file
        if stat_files:
            for stat_file in stat_files:
                # if the stats_file has less than three lines skip it
                if len(open(os.path.join(resultsdir, c, w, stat_file)).readlines()) < 3:
                    continue
                
                if args.verbose:
                    # print the name of the stats_file
                    print('Found stats file: {}'.format(os.path.join(os.path.join(resultsdir, c, w, stat_file))))

                lines = open(os.path.join(resultsdir, c, w, stat_file)).readlines()
                total_energy = 0
                for l in lines:
                    # if line contains nJ, add l.split()[-2] to total_energy
                    if 'Total Idle energy:' in l:
                        continue
                    if 'nJ' in l:
                        total_energy += float(l.split()[-2])

                # create a df with the config, workload and total_energy
                df = pd.DataFrame({'config': [c], 'workload': [w], 'total_energy': [total_energy]})
                df.reset_index(inplace=True, drop=True)
                stats_per_config_workload.append(df)
        else:
            if args.verbose:
                print('Config: {}, Workload: {}, Stats: No stats file found'.format(c, w))

# concatenate all stats into one dataframe
stats = pd.concat(stats_per_config_workload)

# find elements where workload does not contain '-'
# these are multi core workloads
stats = stats[~stats['workload'].str.contains('-')]

# remove these two workloads: stream_10.trace and random_10.trace
stats = stats[~stats['workload'].isin(['stream10_200m.trace', 'random10_200m.trace'])]
# also from workloads
workloads = [w for w in workloads if not w in ['stream10_200m.trace', 'random10_200m.trace']]

# remove "-16DR" from config names
stats['config'] = stats['config'].str.replace('-16DR', '')

# replace 1K with 1000 in config names
stats['config'] = stats['config'].str.replace('1K', '1000')

# replace 'Baseline' with 'Baseline0'
stats['config'] = stats['config'].str.replace('Baseline', 'Baseline0')

# add a new column that stores in integer the number in the config name
stats['nrh'] = stats['config'].str.extract('(\d+)').astype(int)

# remove numbers from config names
stats['config'] = stats['config'].str.replace('\d+', '')
stats['config'] = stats['config'].str.replace('-3', '')

# remove yaml from config names
stats['config'] = stats['config'].str.replace('.yaml', '')

# increasing order of rbmpki
#order = ['511.povray', '481.wrf', '541.leela', '538.imagick', '444.namd', '447.dealII', '464.h264ref', '456.hmmer', '403.gcc', '526.blender', '544.nab', '525.x264', '508.namd', '531.deepsjeng', '458.sjeng', '435.gromacs', '445.gobmk', '401.bzip2', '507.cactuBSSN', '502.gcc', '500.perlbench', '523.xalancbmk', '510.parest', '557.xz', '482.sphinx3', '505.mcf', '436.cactusADM', '471.omnetpp', '473.astar', '483.xalancbmk', '462.libquantum', '433.milc', '520.omnetpp', '437.leslie3d', '450.soplex', '459.GemsFDTD', '549.fotonik3d', '434.zeusmp', '519.lbm', '470.lbm', '429.mcf']
order = ['h264_encode', '511.povray', '481.wrf', '541.leela', '538.imagick', '444.namd', '447.dealII', '464.h264ref', '456.hmmer', '403.gcc', '526.blender', '544.nab', '525.x264', '508.namd', 'grep_map0', '531.deepsjeng', '458.sjeng', '435.gromacs', '445.gobmk', '401.bzip2', '507.cactuBSSN', '502.gcc', 'ycsb_abgsave', 'tpch6', '500.perlbench', '523.xalancbmk', 'ycsb_dserver', 'ycsb_cserver', '510.parest', 'ycsb_bserver', 'ycsb_eserver', 'stream_10.trace', 'tpcc64', 'ycsb_aserver', '557.xz', '482.sphinx3', 'jp2_decode', '505.mcf', 'wc_8443', 'wc_map0', '436.cactusADM', '471.omnetpp', '473.astar', 'jp2_encode', 'tpch17', '483.xalancbmk', '462.libquantum', 'tpch2', '433.milc', '520.omnetpp', '437.leslie3d', '450.soplex', '459.GemsFDTD', '549.fotonik3d', '434.zeusmp', '519.lbm', '470.lbm', '429.mcf', 'random_10.trace', 'h264_decode', 'bfs_ny', 'bfs_cm2003', 'bfs_dblp']

# order workloads according to the order
stats['workload'] = pd.Categorical(stats['workload'], categories=order, ordered=True)

sns.set(font_scale=1.0)
sns.set_style("whitegrid")

# sns set color palette '#648FFF',
comet_palette = [ '#785EF0', '#DC267F', '#FE6100', '#FFB000']
sns.set_palette(comet_palette, n_colors=4)

# remove numbers from config names
stats['config'] = stats['config'].str.replace('\d+', '')
stats['config'] = stats['config'].str.replace('Baseline0', 'Baseline')
stats['config'] = stats['config'].str.replace('1000', '')
stats['config'] = stats['config'].str.replace('500', '')
stats['config'] = stats['config'].str.replace('250', '')
stats['config'] = stats['config'].str.replace('125', '')

# copy the IPC of the baseline config as to all configs
baseline = stats[stats['config'] == 'Baseline']
baseline = baseline[['workload', 'total_energy']]
# baseline
baseline.columns = ['workload', 'baseline_energy']
stats = pd.merge(stats, baseline, on='workload')

stats['normalized_energy'] = stats['total_energy'] / stats['baseline_energy']


# add the geometric normalized ipc average as a new workload to every config
geometric_mean = stats.groupby(['config','nrh'])['normalized_energy'].apply(lambda x: x.prod()**(1.0/len(x))).reset_index()
geometric_mean['workload'] = 'GeoMean'

stats = pd.concat([stats, geometric_mean])

order = ['GeoMean', 'h264_encode', '511.povray', '481.wrf', '541.leela', '538.imagick', '444.namd', '447.dealII', '464.h264ref', '456.hmmer', '403.gcc', '526.blender', '544.nab', '525.x264', '508.namd', 'grep_map0', '531.deepsjeng', '458.sjeng', '435.gromacs', '445.gobmk', '401.bzip2', '507.cactuBSSN', '502.gcc', 'ycsb_abgsave', 'tpch6', '500.perlbench', '523.xalancbmk', 'ycsb_dserver', 'ycsb_cserver', '510.parest', 'ycsb_bserver', 'ycsb_eserver', 'tpcc64', 'ycsb_aserver', '557.xz', '482.sphinx3', 'jp2_decode', '505.mcf', 'wc_8443', 'wc_map0', '436.cactusADM', '471.omnetpp', '473.astar', 'jp2_encode', 'tpch17', '483.xalancbmk', '462.libquantum', 'tpch2', '433.milc', '520.omnetpp', '437.leslie3d', '450.soplex', '459.GemsFDTD', '549.fotonik3d', '434.zeusmp', '519.lbm', '470.lbm', '429.mcf', 'h264_decode', 'bfs_ny', 'bfs_cm2003', 'bfs_dblp']

stats_full = stats.copy()

print('[INFO] Printing single-core energy numbers to singlecore-energy-numbers.txt')

# redirect stdout to a file
sys.stdout = open('plots/singlecore-energy-numbers.txt', 'w')


# print the number of workloads per config and nrh
#print(stats.groupby(['config', 'nrh'])['workload'].count())
#print the normalized ipc of CMS for the geomean at nrh=1000
print("====\nnRH=1k, CoMeT\'s AVERAGE Energy Overhead (%):")
print(((stats[(stats['config']=='CoMeT') & (stats['nrh']==1000) & (stats['workload']=='GeoMean')]['normalized_energy'].values[0])-1)*100)
#print(((stats[(stats['config']=='CoMeT') & (stats['nrh']==1000)]['normalized_energy']).mean()-1)*100)
print("====\nnRH=1k, CoMeT\'s MAX Energy Overhead (%):")
print(((stats[(stats['config']=='CoMeT') & (stats['nrh']==1000)]['normalized_energy'].max())-1)*100)
print("====\nnRH=125, CoMeT\'s AVERAGE Energy Overhead (%):")

print(((stats[(stats['config']=='CoMeT') & (stats['nrh']==125) & (stats['workload']=='GeoMean')]['normalized_energy'].values[0])-1)*100)
print("====\nnRH=125, CoMeT\'s MAX Energy Overhead (%):")
print(((stats[(stats['config']=='CoMeT') & (stats['nrh']==125)]['normalized_energy'].max())-1)*100)

# redirect stdout back to terminal
sys.stdout = sys.__stdout__

print('[INFO] Numbers available: singlecore-energy-numbers.txt')

stats = stats[~stats['workload'].isin(LOW_RBMPKI)]
order = ['GeoMean', 'h264_encode', '511.povray', '481.wrf', '541.leela', '538.imagick', '444.namd', '447.dealII', '464.h264ref', '456.hmmer', '403.gcc', '526.blender', '544.nab', '525.x264', '508.namd', 'grep_map0', '531.deepsjeng', '458.sjeng', '435.gromacs', '445.gobmk', '401.bzip2', '507.cactuBSSN', '502.gcc', 'ycsb_abgsave', 'tpch6', '500.perlbench', '523.xalancbmk', 'ycsb_dserver', 'ycsb_cserver', '510.parest', 'ycsb_bserver', 'ycsb_eserver', 'tpcc64', 'ycsb_aserver', '557.xz', '482.sphinx3', 'jp2_decode', '505.mcf', 'wc_8443', 'wc_map0', '436.cactusADM', '471.omnetpp', '473.astar', 'jp2_encode', 'tpch17', '483.xalancbmk', '462.libquantum', 'tpch2', '433.milc', '520.omnetpp', '437.leslie3d', '450.soplex', '459.GemsFDTD', '549.fotonik3d', '434.zeusmp', '519.lbm', '470.lbm', '429.mcf', 'h264_decode', 'bfs_ny', 'bfs_cm2003', 'bfs_dblp']
order = [x for x in order if not (x in LOW_RBMPKI)]


stats['workload'] = pd.Categorical(stats['workload'], categories=order, ordered=True)
#barplot of normalized IPC, also draw edges around bars

fig, ax = plt.subplots(figsize=(11.5, 4))
ax = sns.barplot(x='workload', y='normalized_energy', hue='nrh', data=stats[(stats['config'] == 'CoMeT')], edgecolor='black', linewidth=0.5)

ax.set_xlabel('Workload')
ax.set_ylabel('Normalized DRAM Energy')
# move ylabel down
ax.yaxis.set_label_coords(-0.045,0.3)
# draw a red line at y = 1.0, label it as baseline IPC
ax.axhline(y=0.999, color='r', linestyle='--')

# extend the y axis to 1.2
ax.set_ylim(0.95, 1.2)
# rotate x axis ticks
ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
# make axis tick font bigger
ax.tick_params(axis='both', which='major', labelsize=11)
ax.tick_params(axis='y', which='major', labelsize=12)

# make x and y axis labels bigger
ax.xaxis.label.set_size(16)
#ax.yaxis.label.set_fontweight('bold')
ax.yaxis.label.set_size(15)
#ax.xaxis.label.set_fontweight('bold')

ax.axvline(x=0.5, color='grey', linestyle='-', linewidth=0.5)


# put the legend on top of the plot
ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1), ncol=4, fancybox=False, shadow=False, framealpha=1, fontsize=12)
# prepend "nRH" to legend names
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, ['$N_{RH}$ = ' + label for label in labels], loc='upper center', bbox_to_anchor=(0.5, 1), ncol=4, fancybox=False, shadow=False, framealpha=1, fontsize=12)

# highlight the geometric mean ax label
ax.get_xticklabels()[0].set_fontweight('bold')

plt.tight_layout()
plt.show()

# save figure
fig.savefig('plots/comet-singlecore-energy.pdf', bbox_inches='tight')
print('[INFO] Plot available: comet-singlecore-energy.pdf (Figure 9)')

if args.saveSummary:
    # print to csv file
    stats.to_csv('singlecore-energy-summary.csv', index=False)


print("=======================================")
print('[INFO] Plotting single-core DRAM energy consumption comparison.')

stats = stats_full.copy()

# use seaborn-deep style
sns.set(font_scale=1.0)
sns.set_style("whitegrid")
sns.set_palette("pastel", n_colors=5)


# add comet's palette
comet_palette = [ '#648FFF', '#785EF0', '#DC267F', '#FE6100', '#FFB000']
sns.set_palette(comet_palette, n_colors=5)


# remove numbers from config names
stats['config'] = stats['config'].str.replace('-4-512-128', '')
stats['config'] = stats['config'].str.replace('Baseline0', 'Baseline')
stats['config'] = stats['config'].str.replace('1000', '')
stats['config'] = stats['config'].str.replace('500', '')
stats['config'] = stats['config'].str.replace('250', '')
stats['config'] = stats['config'].str.replace('125', '')

# new dataframe that does not have the baseline configs
stats_no_baseline = stats[~stats['config'].str.contains('Baseline')]

# order nRH from high to low
stats_no_baseline['nrh'] = pd.Categorical(stats_no_baseline['nrh'], categories=[1000, 500, 250, 125], ordered=True)

# order config in this order: SAC, Graphene, Hydra, REGA, PARA
stats_no_baseline['config'] = pd.Categorical(stats_no_baseline['config'], categories=['Graphene', 'CoMeT', 'Hydra', 'REGA', 'PARA'], ordered=True)

#boxplot of normalized IPC
fig, ax = plt.subplots(figsize=(10, 4))
# show mean values as well
ax = sns.boxplot(x="nrh", y="normalized_energy", hue="config", data=stats_no_baseline, showmeans=True, meanprops={"marker":"o","markerfacecolor":"white", "markeredgecolor":"black"},
                  showfliers = True, flierprops={"marker":"x","markerfacecolor":"black", "markeredgecolor":"black"})
ax.set_xlabel('RowHammer Threshold ($N_{RH}$)')
ax.set_ylabel('Normalized Energy Distribution')
# draw a red line at y = 1.0, label it as baseline IPC
ax.axhline(y=1.0, color='r', linestyle='--')
# extend the y axis to 1.2
ax.set_ylim(0.8, 2.0)
# make axis tick font bigger
ax.tick_params(axis='both', which='major', labelsize=14)
# draw vertical lines to separate the rowhammer threshold values
ax.axvline(x=0.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=1.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=2.5, color='grey', linestyle='-', alpha=0.5)
# make x and y axis labels bigger
ax.xaxis.label.set_size(16)
ax.yaxis.label.set_size(16)

# put the legend on top of the plot
ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2), ncol=5, fancybox=False, shadow=False, fontsize=12)

plt.tight_layout()
# save figure
fig.savefig('plots/comet-singlecore-energy-comparison.pdf', bbox_inches='tight')
if args.saveSummary:
    # export data to csv
    stats_no_baseline.to_csv('singlecore-energy-comparison-fullresults.csv', index=False)

print('[INFO] Plot available: comet-singlecore-energy-comparison.pdf (Figure 11)')
print('[INFO] Printing single-core energy comparison numbers to singlecore-energy-comparison-numbers.txt')

# redirect stdout to a file
sys.stdout = open('plots/singlecore-energy-comparison-numbers.txt', 'w')
comet_1k= stats_no_baseline[(stats_no_baseline['nrh'] == 1000) & (stats_no_baseline['config'] == 'CoMeT')]['normalized_energy'].mean()
comet_125= stats_no_baseline[(stats_no_baseline['nrh'] == 125) & (stats_no_baseline['config'] == 'CoMeT')]['normalized_energy'].mean()

graphene_1k = stats_no_baseline[(stats_no_baseline['nrh'] == 1000) & (stats_no_baseline['config'] == 'Graphene')]['normalized_energy'].mean()
graphene_125 = stats_no_baseline[(stats_no_baseline['nrh'] == 125) & (stats_no_baseline['config'] == 'Graphene')]['normalized_energy'].mean()

print('Graphene 1k: ', (graphene_1k-1)*100)
print('Graphene 125: ', (graphene_125-1)*100)

print('CoMeT 1k / Graphene 1k: ', ((comet_1k / graphene_1k)-1)*100)
print('CoMeT 125 / Graphene 125: ', ((comet_125 / graphene_125)-1)*100)

rega_1k = stats_no_baseline[(stats_no_baseline['nrh'] == 1000) & (stats_no_baseline['config'] == 'REGA')]['normalized_energy'].mean()
rega_125 = stats_no_baseline[(stats_no_baseline['nrh'] == 125) & (stats_no_baseline['config'] == 'REGA')]['normalized_energy'].mean()

para_1k = stats_no_baseline[(stats_no_baseline['nrh'] == 1000) & (stats_no_baseline['config'] == 'PARA')]['normalized_energy'].mean()
para_125 = stats_no_baseline[(stats_no_baseline['nrh'] == 125) & (stats_no_baseline['config'] == 'PARA')]['normalized_energy'].mean()

hydra_1k = stats_no_baseline[(stats_no_baseline['nrh'] == 1000) & (stats_no_baseline['config'] == 'Hydra')]['normalized_energy'].mean()
hydra_125 = stats_no_baseline[(stats_no_baseline['nrh'] == 125) & (stats_no_baseline['config'] == 'Hydra')]['normalized_energy'].mean()

print('Hydra 1k: ', (hydra_1k-1)*100)
print('Hydra 125: ', (hydra_125-1)*100)

print('Hydra_1k / CoMeT_1k: ', ((hydra_1k / comet_1k)-1)*100)
print('Hydra_125 / CoMeT_125: ', ((hydra_125 / comet_125)-1)*100)

# redirect stdout back to terminal
sys.stdout = sys.__stdout__

print('[INFO] Numbers available: singlecore-energy-comparison-numbers.txt')

print("=======================================")
print('[INFO] Plotting k-evaluation results. This may take a while.')


configs = ['Baseline.yaml', 
            'CoMeT1000-1.yaml',
            'CoMeT1000-2.yaml',
            'CoMeT1000-3.yaml',
            'CoMeT1000-4.yaml',
            'CoMeT1000-5.yaml',
            'CoMeT500-1.yaml',
            'CoMeT500-2.yaml',
            'CoMeT500-3.yaml',
            'CoMeT500-4.yaml',
            'CoMeT500-5.yaml',
            'CoMeT250-1.yaml',
            'CoMeT250-2.yaml',
            'CoMeT250-3.yaml',
            'CoMeT250-4.yaml',
            'CoMeT250-5.yaml',
            'CoMeT125-1.yaml',
            'CoMeT125-2.yaml',
            'CoMeT125-3.yaml',
            'CoMeT125-4.yaml',
            'CoMeT125-5.yaml',
              ]
# list all directories under all configs
workloads = []
for c in configs:
    workloads.append([d for d in os.listdir(os.path.join(resultsdir, c)) if os.path.isdir(os.path.join(resultsdir, c, d))])
# find only the intersection of all workloads
workloads = list(set.intersection(*map(set, workloads)))

stats_per_config_workload = []

# for every config + workload directory
for c in configs:
    for w in workloads:
        # find all files in the directory
        files = [f for f in os.listdir(os.path.join(resultsdir, c, w)) if os.path.isfile(os.path.join(resultsdir, c, w, f))]
        # find the stats file
        stat_files = [f for f in files if f.endswith('.stats')]
        # if there is a stats file
        if stat_files:
            for stat_file in stat_files:
                # if the stats_file has less than three lines skip it
                if len(open(os.path.join(resultsdir, c, w, stat_file)).readlines()) < 3:
                    continue
                
                if args.verbose:
                    # print the name of the stats_file
                    print('Found stats file: {}'.format(os.path.join(os.path.join(resultsdir, c, w, stat_file))))

                extension = ''
                # if stats_file file name itself does not start with DDR4, parse it a bit
                if not stat_file.startswith('DDR4'):
                    # get the config name from the stats_file name
                    extension = '_'.join(stat_file.split('_')[:-1])
                    # prepend underscore to extension
                    extension = '_' + extension

                # read the stats file, name columns: 'name', 'value', 'description'
                df = pd.read_csv(os.path.join(resultsdir, c, w, stat_file), header=None).T
                df.columns = df.iloc[0]
                df.drop(0,inplace=True)
                # add a new column called 'config' with the config name
                df['config'] = c + extension
                # add a new column called 'workload' with the workload name
                df['workload'] = w
                # print the stats file
                # print('Config: {}, Workload: {}, Stats: {}'.format(c, w, df))
                # append the stats to the list
                df.reset_index(inplace=True, drop=True)
                stats_per_config_workload.append(df)
        else:
            if args.verbose:
                print('Config: {}, Workload: {}, Stats: No stats file found'.format(c, w))

# concatenate all stats into one dataframe
stats = pd.concat(stats_per_config_workload)

# find elements where workload does not contain '-'
# these are multi core workloads
stats = stats[~stats['workload'].str.contains('-')]

# remove these two workloads: stream_10.trace and random_10.trace
stats = stats[~stats['workload'].isin(['stream10_200.trace', 'random10_200.trace'])]
# also from workloads
workloads = [w for w in workloads if not w in ['stream10_200', 'random10_200.trace']]

#remove configs that has RH32, AH and AAH in the name
stats = stats[~stats['config'].str.contains('RH32')]
stats = stats[~stats['config'].str.contains('AH')]
stats = stats[~stats['config'].str.contains('AAH')]

# remove "-16DR" from config names
stats['config'] = stats['config'].str.replace('-16DR', '')

# replace 1K with 1000 in config names
stats['config'] = stats['config'].str.replace('1K', '1000')

# replace 'Baseline' with 'Baseline0'
stats['config'] = stats['config'].str.replace('Baseline', 'Baseline0')

# add a new column that stores in integer the number in the config name
stats['nrh'] = stats['config'].str.extract('(\d+)').astype(int)

# remove numbers from config names
stats['config'] = stats['config'].str.replace('\d+', '')

# remove yaml from config names
stats['config'] = stats['config'].str.replace('.yaml', '')

stats_copy = stats.copy()

# instructions per cycle (IPC) is record_cycles_insts_0 / record_cycs_core_0
stats['ramulator.ipc'] = stats['ramulator.record_insts_core_0'] / stats['ramulator.record_cycs_core_0']


stats['ramulator.rbmpki'] = (stats['ramulator.row_conflicts_channel_0_core'] + stats['ramulator.row_misses_channel_0_core']) /\
                            stats['ramulator.record_insts_core_0'] * 1000


# copy the IPC of the baseline config as to all configs
baseline = stats[stats['config'] == 'Baseline0']
baseline = baseline[['workload', 'ramulator.ipc', 'ramulator.read_latency_avg_0', 'ramulator.rbmpki', 'ramulator.window_full_stall_cycles_core_0']]
# baseline
baseline.columns = ['workload', 'ramulator.baseline_ipc', 'ramulator.baseline_read_latency_avg_0', 'ramulator.baseline_rbmpki', 'ramulator.baseline_stall_cycles']

stats = pd.merge(stats, baseline, on='workload')

stats['ramulator.normalized_ipc'] = stats['ramulator.ipc'] / stats['ramulator.baseline_ipc']
stats['ramulator.normalized_read_latency'] = stats['ramulator.read_latency_avg_0'] / stats['ramulator.baseline_read_latency_avg_0']
stats['ramulator.normalized_stall_cycles'] = stats['ramulator.window_full_stall_cycles_core_0'] / stats['ramulator.baseline_stall_cycles']
stats['ramulator.normalized_rbmpki'] = stats['ramulator.rbmpki'] / stats['ramulator.baseline_rbmpki']


# add the geometric normalized ipc average as a new workload to every config
geometric_mean = stats.groupby(['config','nrh'])['ramulator.normalized_ipc'].apply(lambda x: x.prod()**(1.0/len(x))).reset_index()
geometric_mean['workload'] = 'GeoMean'


stats = pd.concat([stats, geometric_mean])

sns.set(font_scale=1.0)
sns.set_style("whitegrid")
# sns set color palette
comet_palette = ['#648FFF', '#785EF0', '#DC267F', '#FE6100', '#FFB000']
sns.set_palette(comet_palette, n_colors=5)

# remove random10_200m.trace and stream10_200m.trace
stats = stats[~stats['workload'].isin(['random10_200m.trace', 'stream10_200m.trace'])]

# drop all configs except the ones with CMS 
stats_no_baseline = stats[stats['config'].str.contains('CoMeT')]
stats_comparison = stats[~stats['config'].str.contains('CoMeT')]
# remove oracle from stats_comparison


# merge stats_comparison and stats_no_baseline
stats_new = pd.concat([stats_comparison, stats_no_baseline])

# remove config Baseline0 from stats_no_baseline
stats_new = stats_new[~stats_new['config'].str.contains('Baseline0')]


stats_new['nrh'] = pd.Categorical(stats_new['nrh'], categories=[1000,500,250,125], ordered=True)

#change COMET1000 to COMET 
stats_new['config'] = stats_new['config'].str.replace('CoMeT1000', 'CoMeT')
stats_new['config'] = stats_new['config'].str.replace('CoMeT500', 'CoMeT')
stats_new['config'] = stats_new['config'].str.replace('CoMeT250', 'CoMeT')
stats_new['config'] = stats_new['config'].str.replace('CoMeT125', 'CoMeT')


# rename config COMET COMET-n2
stats_new['config'] = stats_new['config'].str.replace('CoMeT-1', 'k=1')
stats_new['config'] = stats_new['config'].str.replace('CoMeT-2', 'k=2')
stats_new['config'] = stats_new['config'].str.replace('CoMeT-3', 'k=3')
stats_new['config'] = stats_new['config'].str.replace('CoMeT-4', 'k=4')
stats_new['config'] = stats_new['config'].str.replace('CoMeT-5', 'k=5')



# order config in this order: CMS, Graphene
stats_new['config'] = pd.Categorical(stats_new['config'], categories=['k=1','k=2','k=3','k=4', 'k=5'], ordered=True)

#boxplot of normalized IPC

# create two subplots
fig, ax = plt.subplots(figsize=(8, 2.5))

# show mean values as well
ax = sns.boxplot(x="nrh", y="ramulator.normalized_ipc", hue="config", data=stats_new, showmeans=True,
                  meanprops={"marker":"o","markerfacecolor":"white", "markeredgecolor":"black"}, showfliers=True, 
                  flierprops={'marker': 'x', 'markerfacecolor': 'black', 'markeredgecolor': 'black'})
ax.set_xlabel('RowHammer Threshold')
ax.set_ylabel('Normalized\nIPC Distribution')
# draw a red line at y = 1.0, label it as baseline IPC
ax.axhline(y=1.0, color='r', linestyle='--')
# write above the red line 'baseline IPC'
#ax.text(0.02, 0.93, 'baseline IPC', color='#e74c3c', transform=ax.transAxes, fontsize=15)
# extend the y axis to 1.2
ax.set_ylim(0.5, 1.1)
# color the 5th y tick red
#ax.get_yticklabels()[4].set_color('#e74c3c')
# make axis tick font bigger
ax.tick_params(axis='both', which='major', labelsize=14)
# draw vertical lines to separate the rowhammer threshold values
# make x and y axis labels bigger
ax.xaxis.label.set_size(16)
ax.yaxis.label.set_size(16)

# Customize the whiskers and borders
ax.lines[0].set_color('black')  # Set the color of the whiskers\

ax.axvline(x=0.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=1.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=2.5, color='grey', linestyle='-', alpha=0.5)


# put the legend on top of the plot
#ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2), ncol=5, fancybox=True, shadow=True, fontsize=12)
# add legend title as "counters per hash"
ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2), ncol=6, fancybox=False, shadow=False, fontsize=12, framealpha=1)

plt.tight_layout()
plt.show()

# save figure
fig.savefig('plots/comet-k-evaluation.pdf', bbox_inches='tight')
if args.saveSummary:
    # export data to csv
    stats_new.to_csv('comet-k-evaluation-fullresults.csv', index=False)

print('[INFO] Plot available: comet-k-evaluation.pdf (Figure 17)')

print('[INFO] Printing k-evaluation numbers to k-evaluation-numbers.txt')

# redirect stdout to a file
sys.stdout = open('plots/k-evaluation-numbers.txt', 'w')
print("Nothing to see here yet.")

# redirect stdout back to terminal
sys.stdout = sys.__stdout__
print('[INFO] Numbers available: k-evaluation-numbers.txt')

print("=======================================")
print('[INFO] Plotting the sensitivity study results (CT-nRH=1k). This may take a while.')

configs = ['Baseline.yaml',
            "CoMeT1000-1-128-128.yaml",
            "CoMeT1000-1-256-128.yaml",
            "CoMeT1000-1-512-128.yaml",
            "CoMeT1000-1-1024-128.yaml",
            "CoMeT1000-1-2048-128.yaml",
            "CoMeT1000-2-128-128.yaml",
            "CoMeT1000-2-256-128.yaml",
            "CoMeT1000-2-512-128.yaml",
            "CoMeT1000-2-1024-128.yaml",
            "CoMeT1000-2-2048-128.yaml",
            "CoMeT1000-4-128-128.yaml",
            "CoMeT1000-4-256-128.yaml",
            "CoMeT1000-4-512-128.yaml",
            "CoMeT1000-4-1024-128.yaml",
            "CoMeT1000-4-2048-128.yaml",
            "CoMeT1000-8-128-128.yaml",
            "CoMeT1000-8-256-128.yaml",
            "CoMeT1000-8-512-128.yaml",
            "CoMeT1000-8-1024-128.yaml",
            "CoMeT1000-8-2048-128.yaml",
            "CoMeT1000-16-128-128.yaml",
            "CoMeT1000-16-256-128.yaml",
            "CoMeT1000-16-512-128.yaml",
            "CoMeT1000-16-1024-128.yaml",
            "CoMeT1000-16-2048-128.yaml",
        ]
#configs = ['Baseline.yaml', 'CMS1000-100.yaml', 'Graphene1000.yaml', 'CMS1000-100-c.yaml']
# list all directories under all configs
workloads = []
for c in configs:
    workloads.append([d for d in os.listdir(os.path.join(resultsdir, c)) if os.path.isdir(os.path.join(resultsdir, c, d))])
# find only the intersection of all workloads
workloads = list(set.intersection(*map(set, workloads)))

stats_per_config_workload = []

# for every config + workload directory
for c in configs:
    for w in workloads:
        # find all files in the directory
        files = [f for f in os.listdir(os.path.join(resultsdir, c, w)) if os.path.isfile(os.path.join(resultsdir, c, w, f))]
        # find the stats file
        stat_files = [f for f in files if f.endswith('.stats')]
        # if there is a stats file
        if stat_files:
            for stat_file in stat_files:
                # if the stats_file has less than three lines skip it
                if len(open(os.path.join(resultsdir, c, w, stat_file)).readlines()) < 3:
                    continue
                
                if args.verbose:
                    # print the name of the stats_file
                    print('Found stats file: {}'.format(os.path.join(os.path.join(resultsdir, c, w, stat_file))))

                extension = ''
                # if stats_file file name itself does not start with DDR4, parse it a bit
                if not stat_file.startswith('DDR4'):
                    # get the config name from the stats_file name
                    extension = '_'.join(stat_file.split('_')[:-1])
                    # prepend underscore to extension
                    extension = '_' + extension

                # read the stats file, name columns: 'name', 'value', 'description'
                df = pd.read_csv(os.path.join(resultsdir, c, w, stat_file), header=None).T
                df.columns = df.iloc[0]
                df.drop(0,inplace=True)
                # add a new column called 'config' with the config name
                df['config'] = c + extension
                # add a new column called 'workload' with the workload name
                df['workload'] = w
                # print the stats file
                # print('Config: {}, Workload: {}, Stats: {}'.format(c, w, df))
                # append the stats to the list
                df.reset_index(inplace=True, drop=True)
                stats_per_config_workload.append(df)
        else:
            if args.verbose:
                print('Config: {}, Workload: {}, Stats: No stats file found'.format(c, w))

# concatenate all stats into one dataframe
stats = pd.concat(stats_per_config_workload)

# find elements where workload does not contain '-'
# these are multi core workloads
stats = stats[~stats['workload'].str.contains('-')]

# remove these two workloads: stream_10.trace and random_10.trace
stats = stats[~stats['workload'].isin(['stream10_200.trace', 'random10_200.trace'])]
# also from workloads
workloads = [w for w in workloads if not w in ['stream10_200', 'random10_200.trace']]

#remove configs that has RH32, AH and AAH in the name
stats = stats[~stats['config'].str.contains('RH32')]
stats = stats[~stats['config'].str.contains('AH')]
stats = stats[~stats['config'].str.contains('AAH')]

# replace 'Baseline' with 'Baseline0'
stats['config'] = stats['config'].str.replace('ae-results/', '')
stats['config'] = stats['config'].str.replace('../results/', '')
stats['config'] = stats['config'].str.replace('Baseline', 'Baseline0')

# add a new column that stores in integer the number in the config name
stats['nrh'] = stats['config'].str.extract('(\d+)').astype(int)

# remove numbers from config names
stats['config'] = stats['config'].str.replace('\d+', '')

# remove yaml from config names
stats['config'] = stats['config'].str.replace('.yaml', '')

stats_copy = stats.copy()

stats = stats_copy.copy()

# instructions per cycle (IPC) is record_cycles_insts_0 / record_cycs_core_0
stats['ramulator.ipc'] = stats['ramulator.record_insts_core_0'] / stats['ramulator.record_cycs_core_0']


stats['ramulator.rbmpki'] = (stats['ramulator.row_conflicts_channel_0_core'] + stats['ramulator.row_misses_channel_0_core']) /\
                            stats['ramulator.record_insts_core_0'] * 1000


# copy the IPC of the baseline config as to all configs
baseline = stats[stats['config'] == 'Baseline0']
baseline = baseline[['workload', 'ramulator.ipc', 'ramulator.read_latency_avg_0', 'ramulator.rbmpki', 'ramulator.window_full_stall_cycles_core_0']]
# baseline
baseline.columns = ['workload', 'ramulator.baseline_ipc', 'ramulator.baseline_read_latency_avg_0', 'ramulator.baseline_rbmpki', 'ramulator.baseline_stall_cycles']
stats = pd.merge(stats, baseline, on='workload')


stats['ramulator.normalized_ipc'] = stats['ramulator.ipc'] / stats['ramulator.baseline_ipc']
stats['ramulator.normalized_read_latency'] = stats['ramulator.read_latency_avg_0'] / stats['ramulator.baseline_read_latency_avg_0']
stats['ramulator.normalized_stall_cycles'] = stats['ramulator.window_full_stall_cycles_core_0'] / stats['ramulator.baseline_stall_cycles']
stats['ramulator.normalized_rbmpki'] = stats['ramulator.rbmpki'] / stats['ramulator.baseline_rbmpki']


# add the geometric normalized ipc average as a new workload to every config
geometric_mean = stats.groupby(['config','nrh'])['ramulator.normalized_ipc'].apply(lambda x: x.prod()**(1.0/len(x))).reset_index()
geometric_mean['workload'] = 'GeoMean'

stats = pd.concat([stats, geometric_mean])
stats_clean = stats.copy()

stats_sweep = stats_clean.copy()
sns.set(font_scale=1.0)
sns.set_style("whitegrid")
#sns.set_palette("viridis", n_colors=5)

# sns set color palette
comet_palette = ['#648FFF', '#785EF0', '#DC267F', '#FE6100', '#FFB000']
sns.set_palette(comet_palette, n_colors=5)

#print(stats_sweep['config'].unique())
# new dataframe that does not have the baseline configs
stats_no_baseline = stats_sweep[~stats_sweep['config'].str.contains('Baseline0')]
# keep only the configs that have CMS in the name
stats_sweep = stats_sweep[stats_sweep['config'].str.contains('CoMeT')]

stats_no_baseline['counters'] = stats_no_baseline['config'].apply(lambda x: int(re.search(r'CoMeT1000-\d+-(\d+)-\d+', x).group(1)) if re.search(r'CoMeT1000-\d+-(\d+)-\d+', x) else 0)
stats_no_baseline['hashes'] = stats_no_baseline['config'].apply(lambda x: int(re.search(r'CoMeT1000-(\d+)-\d+-\d+', x).group(1)) if re.search(r'CoMeT1000-(\d+)-\d+-\d+', x) else 0)

# order nRH from high to low
stats_no_baseline['counters'] = pd.Categorical(stats_no_baseline['counters'], categories=[128,256,512,1024,2048], ordered=True)

stats_no_baseline['hashes'] = pd.Categorical(stats_no_baseline['hashes'], categories=[1,2,4,8,16], ordered=True)

# drop entries with empty config
stats_no_baseline = stats_no_baseline[stats_no_baseline['config'].notna()]

#boxplot of normalized IPC
fig, ax = plt.subplots(figsize=(10, 3.6))
# show mean values as well
ax = sns.boxplot(x="hashes", y="ramulator.normalized_ipc", hue="counters", data=stats_no_baseline, showmeans=True, 
                 meanprops={"marker":"o","markerfacecolor":"white", "markeredgecolor":"black"}, showfliers=True, 
                 flierprops={'marker': 'x', 'markerfacecolor': 'black', 'markeredgecolor': 'black'})
ax.set_xlabel('Number of Hash Functions ($N_{Hash}$)')
ax.set_ylabel('Normalized\nIPC Distribution')
# draw a red line at y = 1.0, label it as baseline IPC
ax.axhline(y=1.0, color='r', linestyle='--')
# extend the y axis to 1.2
ax.set_ylim(0, 1.2)
# color the 5th y tick red
ax.get_yticklabels()[5].set_color('#e74c3c')
# make axis tick font bigger
ax.tick_params(axis='both', which='major', labelsize=14)
# draw vertical lines to separate the rowhammer threshold values
ax.axvline(x=0.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=1.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=2.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=3.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=4.5, color='grey', linestyle='-', alpha=0.5)
# make x and y axis labels bigger
ax.xaxis.label.set_size(16)
ax.yaxis.label.set_size(16)

# Customize the whiskers and borders
ax.lines[0].set_color('black')  # Set the color of the whiskers\

# add legend title as "counters per hash"
ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2), ncol=20, fancybox=False, shadow=False, fontsize=12, title_fontsize=12, title='Counters per Hash Function ($N_{Counters}$)', framealpha=1)

plt.tight_layout()
plt.show()

# save figure
fig.savefig('plots/comet-ctsweep-1k.pdf', bbox_inches='tight')
if args.saveSummary:
    # export data to csv
    stats_no_baseline.to_csv('comet-ctsweep-1k.csv', index=False)

print('[INFO] Plot available: comet-ctsweep-1k.pdf (Figure 6a)')

print("=======================================")
print('[INFO] Plotting the sensitivity study results (CT-nRH=125). This may take a while.')

configs = ['Baseline.yaml',
            "CoMeT125-1-128-128.yaml",
            "CoMeT125-1-256-128.yaml",
            "CoMeT125-1-512-128.yaml",
            "CoMeT125-1-1024-128.yaml",
            "CoMeT125-1-2048-128.yaml",
            "CoMeT125-2-128-128.yaml",
            "CoMeT125-2-256-128.yaml",
            "CoMeT125-2-512-128.yaml",
            "CoMeT125-2-1024-128.yaml",
            "CoMeT125-2-2048-128.yaml",
            "CoMeT125-4-128-128.yaml",
            "CoMeT125-4-256-128.yaml",
            "CoMeT125-4-512-128.yaml",
            "CoMeT125-4-1024-128.yaml",
            "CoMeT125-4-2048-128.yaml",
            "CoMeT125-8-128-128.yaml",
            "CoMeT125-8-256-128.yaml",
            "CoMeT125-8-512-128.yaml",
            "CoMeT125-8-1024-128.yaml",
            "CoMeT125-8-2048-128.yaml",
            "CoMeT125-16-128-128.yaml",
            "CoMeT125-16-256-128.yaml",
            "CoMeT125-16-512-128.yaml",
            "CoMeT125-16-1024-128.yaml",
            "CoMeT125-16-2048-128.yaml",
        ]
#configs = ['Baseline.yaml', 'CMS1000-100.yaml', 'Graphene1000.yaml', 'CMS1000-100-c.yaml']
# list all directories under all configs
workloads = []
for c in configs:
    workloads.append([d for d in os.listdir(os.path.join(resultsdir, c)) if os.path.isdir(os.path.join(resultsdir, c, d))])
# find only the intersection of all workloads
workloads = list(set.intersection(*map(set, workloads)))

stats_per_config_workload = []

# for every config + workload directory
for c in configs:
    for w in workloads:
        # find all files in the directory
        files = [f for f in os.listdir(os.path.join(resultsdir, c, w)) if os.path.isfile(os.path.join(resultsdir, c, w, f))]
        # find the stats file
        stat_files = [f for f in files if f.endswith('.stats')]
        # if there is a stats file
        if stat_files:
            for stat_file in stat_files:
                # if the stats_file has less than three lines skip it
                if len(open(os.path.join(resultsdir, c, w, stat_file)).readlines()) < 3:
                    continue
                
                if args.verbose:
                    # print the name of the stats_file
                    print('Found stats file: {}'.format(os.path.join(os.path.join(resultsdir, c, w, stat_file))))

                extension = ''
                # if stats_file file name itself does not start with DDR4, parse it a bit
                if not stat_file.startswith('DDR4'):
                    # get the config name from the stats_file name
                    extension = '_'.join(stat_file.split('_')[:-1])
                    # prepend underscore to extension
                    extension = '_' + extension

                # read the stats file, name columns: 'name', 'value', 'description'
                df = pd.read_csv(os.path.join(resultsdir, c, w, stat_file), header=None).T
                df.columns = df.iloc[0]
                df.drop(0,inplace=True)
                # add a new column called 'config' with the config name
                df['config'] = c + extension
                # add a new column called 'workload' with the workload name
                df['workload'] = w
                # print the stats file
                # print('Config: {}, Workload: {}, Stats: {}'.format(c, w, df))
                # append the stats to the list
                df.reset_index(inplace=True, drop=True)
                stats_per_config_workload.append(df)
        else:
            if args.verbose:
                print('Config: {}, Workload: {}, Stats: No stats file found'.format(c, w))

# concatenate all stats into one dataframe
stats = pd.concat(stats_per_config_workload)

# find elements where workload does not contain '-'
# these are multi core workloads
stats = stats[~stats['workload'].str.contains('-')]

# remove these two workloads: stream_10.trace and random_10.trace
stats = stats[~stats['workload'].isin(['stream10_200.trace', 'random10_200.trace'])]
# also from workloads
workloads = [w for w in workloads if not w in ['stream10_200', 'random10_200.trace']]

#remove configs that has RH32, AH and AAH in the name
stats = stats[~stats['config'].str.contains('RH32')]
stats = stats[~stats['config'].str.contains('AH')]
stats = stats[~stats['config'].str.contains('AAH')]

# replace 'Baseline' with 'Baseline0'
stats['config'] = stats['config'].str.replace('ae-results/', '')
stats['config'] = stats['config'].str.replace('../results/', '')
stats['config'] = stats['config'].str.replace('Baseline', 'Baseline0')

# add a new column that stores in integer the number in the config name
stats['nrh'] = stats['config'].str.extract('(\d+)').astype(int)

# remove numbers from config names
stats['config'] = stats['config'].str.replace('\d+', '')

# remove yaml from config names
stats['config'] = stats['config'].str.replace('.yaml', '')

stats_copy = stats.copy()

# instructions per cycle (IPC) is record_cycles_insts_0 / record_cycs_core_0
stats['ramulator.ipc'] = stats['ramulator.record_insts_core_0'] / stats['ramulator.record_cycs_core_0']


stats['ramulator.rbmpki'] = (stats['ramulator.row_conflicts_channel_0_core'] + stats['ramulator.row_misses_channel_0_core']) /\
                            stats['ramulator.record_insts_core_0'] * 1000


# copy the IPC of the baseline config as to all configs
baseline = stats[stats['config'] == 'Baseline0']
baseline = baseline[['workload', 'ramulator.ipc', 'ramulator.read_latency_avg_0', 'ramulator.rbmpki', 'ramulator.window_full_stall_cycles_core_0']]
# baseline
baseline.columns = ['workload', 'ramulator.baseline_ipc', 'ramulator.baseline_read_latency_avg_0', 'ramulator.baseline_rbmpki', 'ramulator.baseline_stall_cycles']

stats = pd.merge(stats, baseline, on='workload')


stats['ramulator.normalized_ipc'] = stats['ramulator.ipc'] / stats['ramulator.baseline_ipc']
stats['ramulator.normalized_read_latency'] = stats['ramulator.read_latency_avg_0'] / stats['ramulator.baseline_read_latency_avg_0']
stats['ramulator.normalized_stall_cycles'] = stats['ramulator.window_full_stall_cycles_core_0'] / stats['ramulator.baseline_stall_cycles']
stats['ramulator.normalized_rbmpki'] = stats['ramulator.rbmpki'] / stats['ramulator.baseline_rbmpki']

# add the geometric normalized ipc average as a new workload to every config
geometric_mean = stats.groupby(['config','nrh'])['ramulator.normalized_ipc'].apply(lambda x: x.prod()**(1.0/len(x))).reset_index()
geometric_mean['workload'] = 'GeoMean'



stats = pd.concat([stats, geometric_mean])

stats_clean = stats.copy()

stats_sweep = stats_clean.copy()
sns.set(font_scale=1.0)
sns.set_style("whitegrid")
#sns.set_palette("viridis", n_colors=5)

# sns set color palette
comet_palette = ['#648FFF', '#785EF0', '#DC267F', '#FE6100', '#FFB000']
sns.set_palette(comet_palette, n_colors=5)

#print(stats_sweep['config'].unique())
# new dataframe that does not have the baseline configs
stats_no_baseline = stats_sweep[~stats_sweep['config'].str.contains('Baseline0')]
# keep only the configs that have CMS in the name
stats_sweep = stats_sweep[stats_sweep['config'].str.contains('CoMeT')]

stats_no_baseline['counters'] = stats_no_baseline['config'].apply(lambda x: int(re.search(r'CoMeT125-\d+-(\d+)-\d+', x).group(1)) if re.search(r'CoMeT125-\d+-(\d+)-\d+', x) else 0)
stats_no_baseline['hashes'] = stats_no_baseline['config'].apply(lambda x: int(re.search(r'CoMeT125-(\d+)-\d+-\d+', x).group(1)) if re.search(r'CoMeT125-(\d+)-\d+-\d+', x) else 0)

# order nRH from high to low
stats_no_baseline['counters'] = pd.Categorical(stats_no_baseline['counters'], categories=[128,256,512,1024,2048], ordered=True)

stats_no_baseline['hashes'] = pd.Categorical(stats_no_baseline['hashes'], categories=[1,2,4,8,16], ordered=True)

# drop entries with empty config
stats_no_baseline = stats_no_baseline[stats_no_baseline['config'].notna()]

#boxplot of normalized IPC
fig, ax = plt.subplots(figsize=(10, 3.6))
# show mean values as well
ax = sns.boxplot(x="hashes", y="ramulator.normalized_ipc", hue="counters", data=stats_no_baseline, showmeans=True, 
                 meanprops={"marker":"o","markerfacecolor":"white", "markeredgecolor":"black"}, showfliers=True, 
                 flierprops={'marker': 'x', 'markerfacecolor': 'black', 'markeredgecolor': 'black'})
ax.set_xlabel('Number of Hash Functions ($N_{Hash}$)')
ax.set_ylabel('Normalized\nIPC Distribution')
# draw a red line at y = 1.0, label it as baseline IPC
ax.axhline(y=1.0, color='r', linestyle='--')
# extend the y axis to 1.2
ax.set_ylim(0, 1.2)
# color the 5th y tick red
ax.get_yticklabels()[5].set_color('#e74c3c')
# make axis tick font bigger
ax.tick_params(axis='both', which='major', labelsize=14)
# draw vertical lines to separate the rowhammer threshold values
ax.axvline(x=0.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=1.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=2.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=3.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=4.5, color='grey', linestyle='-', alpha=0.5)
# make x and y axis labels bigger
ax.xaxis.label.set_size(16)
ax.yaxis.label.set_size(16)

# Customize the whiskers and borders
ax.lines[0].set_color('black')  # Set the color of the whiskers\

# add legend title as "counters per hash"
ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2), ncol=20, fancybox=False, shadow=False, fontsize=12, title_fontsize=12, title='Counters per Hash Function ($N_{Counters}$)', framealpha=1)

plt.tight_layout()
plt.show()

# save figure
fig.savefig('plots/comet-ctsweep-125.pdf', bbox_inches='tight')
if args.saveSummary:
    # export data to csv
    stats_no_baseline.to_csv('cometsweep125.csv', index=False)

print('[INFO] Plot available: comet-ctsweep-125.pdf (Figure 6b)')

print("=======================================")
print('[INFO] Plotting the sensitivity study results (RAT). This may take a while.')

configs = ['Baseline.yaml',
            "CoMeT1000-4-512-512.yaml",
            "CoMeT500-4-512-512.yaml",
            "CoMeT250-4-512-512.yaml",
            "CoMeT125-4-512-512.yaml",
            "CoMeT1000-4-512-256.yaml",
            "CoMeT500-4-512-256.yaml",
            "CoMeT250-4-512-256.yaml",
            "CoMeT125-4-512-256.yaml",
            "CoMeT1000-4-512-128.yaml",
            "CoMeT500-4-512-128.yaml",
            "CoMeT250-4-512-128.yaml",
            "CoMeT125-4-512-128.yaml",
            "CoMeT1000-4-512-64.yaml",
            "CoMeT500-4-512-64.yaml",
            "CoMeT250-4-512-64.yaml",
            "CoMeT125-4-512-64.yaml",
            "CoMeT1000-4-512-32.yaml",
            "CoMeT500-4-512-32.yaml",
            "CoMeT250-4-512-32.yaml",
            "CoMeT125-4-512-32.yaml",
        ]
# list all directories under all configs
workloads = []
for c in configs:
    workloads.append([d for d in os.listdir(os.path.join(resultsdir, c)) if os.path.isdir(os.path.join(resultsdir, c, d))])
# find only the intersection of all workloads
workloads = list(set.intersection(*map(set, workloads)))

stats_per_config_workload = []

# for every config + workload directory
for c in configs:
    for w in workloads:
        # find all files in the directory
        files = [f for f in os.listdir(os.path.join(resultsdir, c, w)) if os.path.isfile(os.path.join(resultsdir, c, w, f))]
        # find the stats file
        stat_files = [f for f in files if f.endswith('.stats')]
        # if there is a stats file
        if stat_files:
            for stat_file in stat_files:
                # if the stats_file has less than three lines skip it
                if len(open(os.path.join(resultsdir, c, w, stat_file)).readlines()) < 3:
                    continue
                
                if args.verbose:
                    # print the name of the stats_file
                    print('Found stats file: {}'.format(os.path.join(os.path.join(resultsdir, c, w, stat_file))))

                extension = ''
                # if stats_file file name itself does not start with DDR4, parse it a bit
                if not stat_file.startswith('DDR4'):
                    # get the config name from the stats_file name
                    extension = '_'.join(stat_file.split('_')[:-1])
                    # prepend underscore to extension
                    extension = '_' + extension

                # read the stats file, name columns: 'name', 'value', 'description'
                df = pd.read_csv(os.path.join(resultsdir, c, w, stat_file), header=None).T
                df.columns = df.iloc[0]
                df.drop(0,inplace=True)
                # add a new column called 'config' with the config name
                df['config'] = c + extension
                # add a new column called 'workload' with the workload name
                df['workload'] = w
                # print the stats file
                # print('Config: {}, Workload: {}, Stats: {}'.format(c, w, df))
                # append the stats to the list
                df.reset_index(inplace=True, drop=True)
                stats_per_config_workload.append(df)
        else:
            if args.verbose:
                print('Config: {}, Workload: {}, Stats: No stats file found'.format(c, w))

# concatenate all stats into one dataframe
stats = pd.concat(stats_per_config_workload)

# find elements where workload does not contain '-'
# these are multi core workloads
stats = stats[~stats['workload'].str.contains('-')]

# remove these two workloads: stream_10.trace and random_10.trace
stats = stats[~stats['workload'].isin(['stream10_200.trace', 'random10_200.trace'])]
# also from workloads
workloads = [w for w in workloads if not w in ['stream10_200', 'random10_200.trace']]

#remove configs that has RH32, AH and AAH in the name
stats = stats[~stats['config'].str.contains('RH32')]
stats = stats[~stats['config'].str.contains('AH')]
stats = stats[~stats['config'].str.contains('AAH')]

# replace 'Baseline' with 'Baseline0'
stats['config'] = stats['config'].str.replace('ae-results/', '')
stats['config'] = stats['config'].str.replace('../results/', '')
stats['config'] = stats['config'].str.replace('Baseline', 'Baseline0')

# add a new column that stores in integer the number in the config name
stats['nrh'] = stats['config'].str.extract('(\d+)').astype(int)

# remove numbers from config names
stats['config'] = stats['config'].str.replace('\d+', '')

# remove yaml from config names
stats['config'] = stats['config'].str.replace('.yaml', '')

stats_copy = stats.copy()

stats = stats_copy.copy()

# instructions per cycle (IPC) is record_cycles_insts_0 / record_cycs_core_0
stats['ramulator.ipc'] = stats['ramulator.record_insts_core_0'] / stats['ramulator.record_cycs_core_0']


stats['ramulator.rbmpki'] = (stats['ramulator.row_conflicts_channel_0_core'] + stats['ramulator.row_misses_channel_0_core']) /\
                            stats['ramulator.record_insts_core_0'] * 1000


# copy the IPC of the baseline config as to all configs
baseline = stats[stats['config'] == 'Baseline0']
baseline = baseline[['workload', 'ramulator.ipc', 'ramulator.read_latency_avg_0', 'ramulator.rbmpki', 'ramulator.window_full_stall_cycles_core_0']]
# baseline
baseline.columns = ['workload', 'ramulator.baseline_ipc', 'ramulator.baseline_read_latency_avg_0', 'ramulator.baseline_rbmpki', 'ramulator.baseline_stall_cycles']
stats = pd.merge(stats, baseline, on='workload')

stats['ramulator.normalized_ipc'] = stats['ramulator.ipc'] / stats['ramulator.baseline_ipc']
stats['ramulator.normalized_read_latency'] = stats['ramulator.read_latency_avg_0'] / stats['ramulator.baseline_read_latency_avg_0']
stats['ramulator.normalized_stall_cycles'] = stats['ramulator.window_full_stall_cycles_core_0'] / stats['ramulator.baseline_stall_cycles']
stats['ramulator.normalized_rbmpki'] = stats['ramulator.rbmpki'] / stats['ramulator.baseline_rbmpki']

# add the geometric normalized ipc average as a new workload to every config
geometric_mean = stats.groupby(['config','nrh'])['ramulator.normalized_ipc'].apply(lambda x: x.prod()**(1.0/len(x))).reset_index()
geometric_mean['workload'] = 'GeoMean'


stats = pd.concat([stats, geometric_mean])

stats_clean = stats.copy()


stats_sweep = stats_clean.copy()


sns.set(font_scale=1.0)
sns.set_style("whitegrid")
#sns.set_palette("viridis", n_colors=5)

# sns set color palette
comet_palette = ['#648FFF', '#785EF0', '#DC267F', '#FE6100', '#FFB000']
sns.set_palette(comet_palette, n_colors=5)

# drop all configs except the ones with CMS 
stats_no_baseline = stats[stats['config'].str.contains('CoMeT')]

stats_no_baseline['counters'] = stats_no_baseline['config'].apply(lambda x: int(re.search(r'CoMeT(?:1000|125|250|500)+-\d+-(\d+)-\d+', x).group(1)) if re.search(r'CoMeT(?:1000|125|250|500)+-\d+-(\d+)-\d+', x) else 0)
stats_no_baseline['hashes'] =   stats_no_baseline['config'].apply(lambda x: int(re.search(r'CoMeT(?:1000|125|250|500)+-(\d+)-\d+-\d+', x).group(1)) if re.search(r'CoMeT(?:1000|125|250|500)+-(\d+)-\d+-\d+', x) else 0)
stats_no_baseline['entries'] =  stats_no_baseline['config'].apply(lambda x: int(re.search(r'CoMeT(?:1000|125|250|500)+-\d+-\d+-(\d+)', x).group(1)) if re.search(r'CoMeT(?:1000|125|250|500)+-\d+-\d+-(\d+)', x) else 0)

# change all configs with name starting with CMS to CMS
stats_no_baseline['config'] = stats_no_baseline['config'].apply(lambda x: 'CoMeT' if re.search(r'CoMeT\d+-\d+-\d+-\d+', x) else x)

# drop entries with empty config
stats_no_baseline = stats_no_baseline[stats_no_baseline['config'].notna()]


# order nRH from high to low
stats_no_baseline['counters'] = pd.Categorical(stats_no_baseline['counters'], categories=[512], ordered=True)

stats_no_baseline['hashes'] = pd.Categorical(stats_no_baseline['hashes'], categories=[4], ordered=True)

stats_no_baseline['entries'] = pd.Categorical(stats_no_baseline['entries'], categories=[32,64,128,256,512], ordered=True)
stats_no_baseline['nrh'] = pd.Categorical(stats_no_baseline['nrh'], categories=[1000,500,250,125], ordered=True)

# order config in this order: CMS, Graphene
stats_no_baseline['config'] = pd.Categorical(stats_no_baseline['config'], categories=['CoMeT'], ordered=True)


#boxplot of normalized IPC
fig, ax = plt.subplots(figsize=(10, 3.6))
# show mean values as well
ax = sns.boxplot(x="nrh", y="ramulator.normalized_ipc", hue="entries", data=stats_no_baseline, 
                 showmeans=True, meanprops={"marker":"o","markerfacecolor":"white", "markeredgecolor":"black"}, 
                 showfliers=True, flierprops={'marker': 'x', 'markerfacecolor': 'black', 'markeredgecolor': 'black'})
ax.set_xlabel('RowHammer Threshold ($N_{RH}$)')
ax.set_ylabel('Normalized\nIPC Distribution')
# draw a red line at y = 1.0, label it as baseline IPC
ax.axhline(y=1.0, color='r', linestyle='--')
# extend the y axis to 1.2
ax.set_ylim(0, 1.2)
# color the 5th y tick red
#ax.get_yticklabels()[4].set_color('#e74c3c')
# make axis tick font bigger
ax.tick_params(axis='both', which='major', labelsize=14)
# draw vertical lines to separate the rowhammer threshold values
ax.axvline(x=0.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=1.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=2.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=3.5, color='grey', linestyle='-', alpha=0.5)
# make x and y axis labels bigger
ax.xaxis.label.set_size(16)
ax.yaxis.label.set_size(16)

# Customize the whiskers and borders
ax.lines[0].set_color('black')  # Set the color of the whiskers\

# add legend title as "counters per hash"
ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2), ncol=5, fancybox=False, shadow=False, fontsize=12, title='Number of RAT Entries ($N_{RAT\_Entries}$)', title_fontsize=12, framealpha=1)

plt.tight_layout()
plt.show()

# save figure
fig.savefig('plots/comet-ratsweep.pdf', bbox_inches='tight')
if args.saveSummary:
    # export data to csv
    stats_no_baseline.to_csv('comet-ratsweep.csv', index=False)

print('[INFO] Plot available: comet-ratsweep.pdf (Figure 7)')

print("=======================================")
print('[INFO] Plotting the motivational data.')

configs = ['Hydra1000.yaml'
           ,'Hydra500.yaml'
           ,'Hydra250.yaml'
           ,'Hydra125.yaml'
           ,'Baseline.yaml']
# list all directories under all configs
workloads = []
for c in configs:
    workloads.append([d for d in os.listdir(os.path.join(resultsdir, c)) if os.path.isdir(os.path.join(resultsdir, c, d))])
# find only the intersection of all workloads
workloads = list(set.intersection(*map(set, workloads)))

stats_per_config_workload = []

# for every config + workload directory
for c in configs:
    for w in workloads:
        # find all files in the directory
        files = [f for f in os.listdir(os.path.join(resultsdir, c, w)) if os.path.isfile(os.path.join(resultsdir, c, w, f))]
        # find the stats file
        stat_files = [f for f in files if f.endswith('.stats')]
        # if there is a stats file
        if stat_files:
            for stat_file in stat_files:
                # if the stats_file has less than three lines skip it
                if len(open(os.path.join(resultsdir, c, w, stat_file)).readlines()) < 3:
                    continue
                
                if args.verbose:
                    # print the name of the stats_file
                    print('Found stats file: {}'.format(os.path.join(os.path.join(resultsdir, c, w, stat_file))))

                extension = ''
                # if stats_file file name itself does not start with DDR4, parse it a bit
                if not stat_file.startswith('DDR4'):
                    # get the config name from the stats_file name
                    extension = '_'.join(stat_file.split('_')[:-1])
                    # prepend underscore to extension
                    extension = '_' + extension

                # read the stats file, name columns: 'name', 'value', 'description'
                df = pd.read_csv(os.path.join(resultsdir, c, w, stat_file), header=None).T
                df.columns = df.iloc[0]
                df.drop(0,inplace=True)
                # add a new column called 'config' with the config name
                df['config'] = c + extension
                # add a new column called 'workload' with the workload name
                df['workload'] = w
                # print the stats file
                # print('Config: {}, Workload: {}, Stats: {}'.format(c, w, df))
                # append the stats to the list
                df.reset_index(inplace=True, drop=True)
                stats_per_config_workload.append(df)
        else:
            if args.verbose:
                print('Config: {}, Workload: {}, Stats: No stats file found'.format(c, w))

# concatenate all stats into one dataframe
stats = pd.concat(stats_per_config_workload)

# find elements where workload does not contain '-'
# these are multi core workloads
stats = stats[~stats['workload'].str.contains('-')]

# remove "-16DR" from config names
stats['config'] = stats['config'].str.replace('-16DR', '')

# replace 1K with 1000 in config names
stats['config'] = stats['config'].str.replace('1K', '1000')

# replace 'Baseline' with 'Baseline0'
stats['config'] = stats['config'].str.replace('Baseline', 'Baseline0')

# add a new column that stores in integer the number in the config name
stats['nrh'] = stats['config'].str.extract('(\d+)').astype(int)

# remove numbers from config names
stats['config'] = stats['config'].str.replace('\d+', '')

# remove yaml from config names
stats['config'] = stats['config'].str.replace('.yaml', '')

stats_copy = stats.copy()

# drop workloads that has - character in them
stats = stats[~stats['workload'].str.contains('-')]

# instructions per cycle (IPC) is record_cycles_insts_0 / record_cycs_core_0
stats['ramulator.ipc'] = stats['ramulator.record_insts_core_0'] / stats['ramulator.record_cycs_core_0']


stats['ramulator.rbmpki'] = (stats['ramulator.row_conflicts_channel_0_core'] + stats['ramulator.row_misses_channel_0_core']) /\
                            stats['ramulator.record_insts_core_0'] * 1000


# copy the IPC of the baseline config as to all configs
baseline = stats[stats['config'] == 'Baseline0']
baseline = baseline[['workload', 'ramulator.ipc', 'ramulator.read_latency_avg_0', 'ramulator.rbmpki', 'ramulator.window_full_stall_cycles_core_0']]
# baseline
baseline.columns = ['workload', 'ramulator.baseline_ipc', 'ramulator.baseline_read_latency_avg_0', 'ramulator.baseline_rbmpki', 'ramulator.baseline_stall_cycles']

stats = pd.merge(stats, baseline, on='workload')

stats['ramulator.normalized_ipc'] = stats['ramulator.ipc'] / stats['ramulator.baseline_ipc']
stats['ramulator.normalized_read_latency'] = stats['ramulator.read_latency_avg_0'] / stats['ramulator.baseline_read_latency_avg_0']
stats['ramulator.normalized_stall_cycles'] = stats['ramulator.window_full_stall_cycles_core_0'] / stats['ramulator.baseline_stall_cycles']
stats['ramulator.normalized_rbmpki'] = stats['ramulator.rbmpki'] / stats['ramulator.baseline_rbmpki']


sns.set(font_scale=1.0)
sns.set_style("whitegrid")

# remove all config integers from stats_comparison
stats['config'] = stats['config'].apply(lambda x: re.sub(r'\d+', '', x))

# remove config Baseline0 from stats_no_baseline
stats_new = stats[~stats['config'].str.contains('Baseline')]

sns.set_palette('icefire', n_colors=4)

stats_new['nrh'] = pd.Categorical(stats_new['nrh'], categories=[1000,500,250,125], ordered=True)

#boxplot of normalized IPC
fig, ax = plt.subplots(figsize=(6, 3))
# show mean values as well
ax = sns.boxplot(x="nrh", y="ramulator.normalized_ipc", data=stats_new, showmeans=True, meanprops={"marker":"o","markerfacecolor":"white", "markeredgecolor":"black"}, showfliers=True, flierprops={'marker': 'x', 'markerfacecolor': 'black', 'markeredgecolor': 'black'})
ax.set_xlabel('RowHammer Threshold')
ax.set_ylabel('Normalized\nIPC Distribution')
# draw a red line at y = 1.0, label it as baseline IPC
ax.axhline(y=1.0, color='r', linestyle='--')
# extend the y axis to 1.2
ax.set_ylim(0.4, 1.15)
# color the 5th y tick red
# make axis tick font bigger
ax.tick_params(axis='both', which='major', labelsize=14)
# draw vertical lines to separate the rowhammer threshold values
ax.axvline(x=0.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=1.5, color='grey', linestyle='-', alpha=0.5)
ax.axvline(x=2.5, color='grey', linestyle='-', alpha=0.5)
# make x and y axis labels bigger
ax.xaxis.label.set_size(16)
ax.yaxis.label.set_size(16)

# Customize the whiskers and borders
ax.lines[0].set_color('black')  # Set the color of the whiskers\

plt.tight_layout()
# save figure
fig.savefig('plots/comet-motiv.pdf', bbox_inches='tight')

print('[INFO] Plot available: comet-motiv.pdf (Figure 3)')
print('[INFO] Printing the numbers for the paper to motiv-results.txt')

# direct stdout to file
sys.stdout = open('plots/motiv-results.txt', 'w')

geometric_mean = stats.groupby(['config','nrh'])['ramulator.normalized_ipc'].apply(lambda x: x.prod()**(1.0/len(x))).reset_index()
geometric_mean['workload'] = 'GeoMean'

#print(stats['config'])


stats = pd.concat([stats, geometric_mean])

# print geomean for each config
#print(geometric_mean)

performance_overhead_1k = 1.0 - geometric_mean[geometric_mean['nrh'] == 1000]['ramulator.normalized_ipc'].values[0]
performance_overhead_125 = 1.0 - geometric_mean[geometric_mean['nrh'] == 125]['ramulator.normalized_ipc'].values[0]


min_performance = stats.groupby(['config','nrh'])['ramulator.normalized_ipc'].min().reset_index()
#print(min_performance)

max_performance_overhead_1k = 1.0 - min_performance[min_performance['nrh'] == 1000]['ramulator.normalized_ipc'].values[0]
max_performance_overhead_125 = 1.0 - min_performance[min_performance['nrh'] == 125]['ramulator.normalized_ipc'].values[0]


print("Performance overhead 1k:\t\t", performance_overhead_1k*100)
print("Maximum Performance overhead 1k:\t", max_performance_overhead_1k*100)
print("Performance overhead 125:\t\t", performance_overhead_125*100)
print("Maximum Performance overhead 125:\t", max_performance_overhead_125*100)

# redirect stdout back to console
sys.stdout = sys.__stdout__

print('[INFO] Numbers available: motiv-results.txt')

print("=======================================")
print('[INFO] All done. Bye!')