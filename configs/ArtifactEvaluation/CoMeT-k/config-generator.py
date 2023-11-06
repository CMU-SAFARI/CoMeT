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


num_hash = [4]
counters = [512]
threshold_list = [1000,500,250,125]
table_entries = [128]
k_list = [1] 
reset_period = 64000000

# Example usage
input_file = "CoMeT-Template.yaml"
for threshold in threshold_list:
    for hash in num_hash:
        for counter in counters:
            for num_table_entry in table_entries:
                for k in k_list:
                    num_counter =  counter 
                    output_file = "CoMeT" + str(threshold) + "-" + str(k) + ".yaml"
                    modify_yaml(input_file, k, hash, num_counter, num_table_entry, threshold, output_file)
