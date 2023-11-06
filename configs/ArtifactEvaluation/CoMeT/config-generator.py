import sys
import yaml
import math

def modify_yaml(input_file,k, num_hash, num_counter, num_table_entry, threshold, output_file):
    with open(input_file, 'r') as f:
        data = yaml.safe_load(f)

    data["post_warmup_settings"]["memory"]["controller"]["refresh_based_defense"]["no_hashes"] = num_hash
    data["post_warmup_settings"]["memory"]["controller"]["refresh_based_defense"]["no_counters_per_hash"] = num_counter
    data["post_warmup_settings"]["memory"]["controller"]["refresh_based_defense"]["aggressor_cache_size"] = num_table_entry
    data["post_warmup_settings"]["memory"]["controller"]["refresh_based_defense"]["rowhammer_threshold"] = threshold
    data["post_warmup_settings"]["memory"]["controller"]["refresh_based_defense"]["activation_threshold"] = int(math.ceil(threshold/(k+1)))
    data["post_warmup_settings"]["memory"]["controller"]["refresh_based_defense"]["reset_period"] = int(math.ceil(reset_period/(k)))

    # Write updated content to output file
    with open(output_file, 'w') as f:
        yaml.dump(data, f)

    print("\"" + output_file + "\"" +",")


num_hash = [1,2,4,8,16]
counters = [128,256,512,1024,2048]
threshold_list = [1000]
table_entries = [128]
k = 3
reset_period = 64000000

# Example usage
input_file = "CoMeT-Template.yaml"
for threshold in threshold_list:
    for hash in num_hash:
        for counter in counters:
            for num_table_entry in table_entries:
                num_counter =  counter 
                output_file = "CoMeT" + str(threshold) + "-" + str(hash) + "-" + str(num_counter) + "-" + str(num_table_entry) + ".yaml"
                modify_yaml(input_file, k, hash, num_counter, num_table_entry, threshold, output_file)
