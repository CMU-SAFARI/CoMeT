#include "CoMeT.h"

namespace Ramulator
{
  template <class T>
  CoMeT<T>::CoMeT(const YAML::Node &config, Controller<T>* ctrl) : RefreshBasedDefense<T>(config, ctrl)
  {
    no_counters_per_hash = config["no_counters_per_hash"].as<int>();
    no_hashes = config["no_hashes"].as<int>();
    activation_threshold = config["activation_threshold"].as<int>();
    reset_period = config["reset_period"].as<int>();
    debug = config["debug"].as<bool>();
    debug_verbose = config["debug_verbose"].as<bool>();
    debug_misuse = config["debug_misuse"].as<bool>(false);
    reset_period_clk = (int) (reset_period / (((float) ctrl->channel->spec->speed_entry[int(T::TimingCons::tCK_ps)])/1000));
    cache_size = config["aggressor_cache_size"].as<int>(10);
    conservative = config["conservative"].as<bool>(false);
    misuse_refresh = config["misuse_refresh"].as<bool>(false);
    misuse_threshold = config["misuse_threshold"].as<float>(0.5);
    misuse_history_length = config["misuse_length"].as<int>(128);

    // Get organization configuration
    this->no_rows_per_bank = ctrl->channel->spec->org_entry.count[int(T::Level::Row)];
    this->no_bank_groups = ctrl->channel->spec->org_entry.count[int(T::Level::BankGroup)];
    this->no_banks = ctrl->channel->spec->org_entry.count[int(T::Level::Bank)];
    this->no_ranks = ctrl->channel->spec->org_entry.count[int(T::Level::Rank)];

    if (debug)
    {
      std::cout << "CoMeT: activation_threshold: " << activation_threshold << std::endl;
      std::cout << "CoMeT: reset_period: " << reset_period << std::endl;
      std::cout << "CoMeT: reset_period_clk: " << reset_period_clk << std::endl;
      std::cout << "  └  tCK: " << ((float) ctrl->channel->spec->speed_entry[int(T::TimingCons::tCK_ps)]) << std::endl;
      std::cout << "CoMeT: no_rows_per_bank: " << this->no_rows_per_bank << std::endl;
      std::cout << "CoMeT: no_bank_groups: " << this->no_bank_groups << std::endl;
      std::cout << "CoMeT: no_banks: " << this->no_banks << std::endl;
      std::cout << "CoMeT: no_ranks: " << this->no_ranks << std::endl;
    }

    // Initialize activation count table
    // each table has no_table_entries entries
    for (int i = 0; i < this->no_banks * this->no_bank_groups * this->no_ranks; i++)
    {
      std::vector<std::unordered_map<int, int>> table;
      for (int j = 0; j < no_hashes; j++) 
      {
        std::unordered_map<int, int> table_per_hash;
        for (int k = 0; k < no_counters_per_hash; k++)
          table_per_hash.insert(std::make_pair(k, 0));
        table.push_back(table_per_hash);
      }
      activation_count_table.push_back(table);

      std::unordered_map<int, int> cache;
      for (int j = -1; j > -1 - cache_size; j--)
        cache.insert(std::make_pair(j, 0));
      aggressor_cache.push_back(cache);

      std::deque<bool> misuse_bit;
      for (int j = 0; j < misuse_history_length; j++)
        misuse_bit.push_back(false);
      misuse_bits.push_back(misuse_bit);
    }

    // initialize the hash functions
    hashFunctions = getHashFunctions(no_counters_per_hash, no_hashes);

    this->additional_rank_refreshes = 0;

  }
  typedef std::function<uint16_t(uint16_t)> HashFunction;

  

  template <class T>
  void CoMeT<T>::tick()
  {
    this->schedule_preventive_refreshes();

    // reset activation count table every reset_period
    // by setting every element to 0
    if (clk % reset_period_clk == 0)
    {
      std::cout << "CoMeT: Resetting activation count table" << std::endl;
      for (int i = 0; i < this->no_banks * this->no_bank_groups * this->no_ranks; i++)
      {
        for (int j = 0; j < no_hashes; j++) 
        {
          for (int k = 0; k < no_counters_per_hash; k++)
          {
            auto counter = activation_count_table[i][j].find(k);
            counter->second = 0;
          }
        }
      
        aggressor_cache[i].clear();
        for (int j = -1; j > -1 - cache_size; j--)
          aggressor_cache[i].insert(std::make_pair(j, 0));
        
        for (int j = 0; j < misuse_history_length; j++) {
          misuse_bits[i][j] = false;
        }
      }
      

      //sanity check
      for (int i = 0; i < this->no_banks * this->no_bank_groups * this->no_ranks; i++)
      {
        for (int j = 0; j < no_hashes; j++) 
        {
          std::unordered_map<int, int> table_per_hash = activation_count_table[i][j];
          for (int k = 0; k < no_counters_per_hash; k++)
          {
            auto counter = table_per_hash.find(k);
            if (counter->second != 0)
              std::cout << "CoMeT: ERROR: counter value is not 0! value: " << counter->second << std::endl;
            assert(counter->second == 0);
          }
        }
      }


    }

    clk++;
  }

  template <class T>
  void CoMeT<T>::update(typename T::Command cmd, const std::vector<int> &addr_vec, uint64_t open_for_nclocks, int core_id)
  {
    if (cmd != T::Command::PRE)
      return;
    
    int bank_group_id = addr_vec[int(T::Level::BankGroup)];
    int bank_id = addr_vec[int(T::Level::Bank)];
    int rank_id = addr_vec[int(T::Level::Rank)];
    int row_id = addr_vec[int(T::Level::Row)];


    if (debug_verbose)
    {
      std::cout << "CoMeT: ACT on row " << row_id << std::endl;
      std::cout << "  └  " << "rank: " << rank_id << std::endl;
      std::cout << "  └  " << "bank_group: " << bank_group_id << std::endl;
      std::cout << "  └  " << "bank: " << bank_id << std::endl;
    }

    // check if row is in aggressor_cache
    auto cache_entry = aggressor_cache[rank_id * this->no_banks * this->no_bank_groups + bank_group_id * this->no_banks + bank_id].find(row_id);
    if (cache_entry != aggressor_cache[rank_id * this->no_banks * this->no_bank_groups + bank_group_id * this->no_banks + bank_id].end()) 
    {
      //found in cache 
      //if (debug)
      //{
      //  std::cout << "  └  " << "row " << row_id << " found in aggressor cache" << std::endl;
      //}
      // increment the counter
      cache_entry->second += 1;

      //if cache entry is greater than threshold, schedule preventive refreshes
      if (cache_entry->second >= activation_threshold)
      {
        if (debug)
        {
          std::cout << "  └  " << "Row " << row_id << " has exceeded the threshold while in cache!" << std::endl;
        }
        // if yes, schedule preventive refreshes
        this->enqueue_preventive_refresh(addr_vec);
        // reset counter here
        cache_entry->second = 0; 
      }
      int index = rank_id * this->no_banks * this->no_bank_groups + bank_group_id * this->no_banks + bank_id;
      misuse_bits[index].pop_front();
      misuse_bits[index].push_back(false);
      return;
    }
    
    // row is not in the aggressor cache
    // check rows counters
    int min_ctr = INT_MAX;
    std::vector<int> indices;
    // check the counter values to determine whether to send preventive refreshes
    for (int i = 0; i < no_hashes; i++)
    {
      int index = rank_id * this->no_banks * this->no_bank_groups + bank_group_id * this->no_banks + bank_id;
      int hash = hashFunctions[i](row_id);
      indices.push_back(hash);
      auto counter = activation_count_table[index][i].find(hash);
      int counter_value = counter->second;
      if (debug_verbose)
      {
        std::cout << "  └  " << "hash[" << i << "]: " << hash << std::endl;
        std::cout << "  └  " << "counter[" << hash << "]: " << counter->second << std::endl;
      }
      if (min_ctr > counter_value)
        min_ctr = counter_value;
    }
    // if min counter is already equal to or greater than the threshold push true to misuse bit
    if (min_ctr >= activation_threshold) {
      // increase misuse bit
      int index = rank_id * this->no_banks * this->no_bank_groups + bank_group_id * this->no_banks + bank_id;
      misuse_bits[index].pop_front();
      misuse_bits[index].push_back(true);
      //if (debug_misuse){
      //std::cout << "misuse bits: "; 
      //for(int i =0;i<misuse_history_length;i++)
      //  std::cout <<  misuse_bits[index][i] << " ";
      //std::cout << std::endl;
      //}
    }
    //else {
    //  // increase misuse bit
    //  auto misuse = misuse_bits[rank_id * this->no_banks * this->no_bank_groups + bank_group_id * this->no_banks + bank_id];
    //  misuse.pop_front();
    //  misuse.push_back(false);
    //}
    // update counters
    for (int i = 0; i < no_hashes; i++)
    {
      int index = rank_id * this->no_banks * this->no_bank_groups + bank_group_id * this->no_banks + bank_id;
      int hash = indices[i];
      auto counter = activation_count_table[index][i].find(hash);
      // update the counter value 
      // conservative mode: only update if the counter value == the min_ctr
      if (counter->second >= activation_threshold)
        continue;
      if (conservative)
      {
        if (counter->second == min_ctr)
          counter->second +=1;
      }
      else
        counter->second += 1;
    }

    int updated_min_ctr = min_ctr + 1;
    if (debug_verbose) 
    {
      std::cout << "  └  " << "updated_min_ctr: " << updated_min_ctr << std::endl;
    }

    if (misuse_refresh) {
      int index = rank_id * this->no_banks * this->no_bank_groups + bank_group_id * this->no_banks + bank_id;
      std::deque<bool> misuse = misuse_bits[index];
      int misused = 0;
      for (int i = 0; i < misuse_history_length; i++) {
        if (misuse[i]) {
          misused++;
        }
      }
      double misused_ratio = (double) misused / (double) misuse_history_length;
      if (debug_misuse) 
      {
        //std::cout << "misused: " << misused << std::endl;
        std::cout << "misused_ratio: " << misused_ratio << std::endl;
      }
 //    std::cout << "  └  " << "misused_ratio: " << misused_ratio << std::endl;
      if (misused_ratio > misuse_threshold) {
        if (debug_misuse) 
          std::cout << " SENDING REFRESH BC OF MISUSE RATE" << std::endl;
        this->completely_refresh_dram_rank();
        // clear everything

        for (int i = 0; i < this->no_banks * this->no_bank_groups * this->no_ranks; i++)
        {
          for (int j = 0; j < no_hashes; j++) 
          {
            for (int k = 0; k < no_counters_per_hash; k++)
            {
              auto counter = activation_count_table[i][j].find(k);
              counter->second = 0;
            }
          }
        
          aggressor_cache[i].clear();
          for (int j = -1; j > -1 - cache_size; j--)
            aggressor_cache[i].insert(std::make_pair(j, 0));
          
          for (int j = 0; j < misuse_history_length; j++) {
            misuse_bits[i][j] = false;
          }
        }

        return;

      }
    }

    if (updated_min_ctr >= activation_threshold)
    {
      if (debug) 
      {
        std::cout << "Row " << row_id << " has exceeded the threshold!" << std::endl << "  └  counter indices: ";
        for (auto index : indices)  
          std::cout  << index << " ";
        std::cout << std::endl;
      }
      // if yes, schedule preventive refreshes
      this->enqueue_preventive_refresh(addr_vec);
      // cannot reset counter here 
      // insert in aggressor cache
      // find a free entry in the cache
      int index = rank_id * this->no_banks * this->no_bank_groups + bank_group_id * this->no_banks + bank_id;
      
      int remove_key = 0;
      bool found = false;
      for (auto it = aggressor_cache[index].begin(); it != aggressor_cache[index].end(); it++) 
      {
        if (it->first < 0) {
          found = true;
          remove_key = it->first;
          break;
        }
      }

      if (found) 
      {
        // remove to_remove from the table
        aggressor_cache[index].erase(remove_key);
        // add row_id to the table
        aggressor_cache[index][row_id] = 0;
        if (debug) 
        {
          std::cout << "CoMeT: " << "index: " << index << " row " << row_id << " added to aggressor cache" << std::endl;
          //for (auto entry : aggressor_cache[index])
          //  std::cout << "  └  " << "row: " << entry.first << " counter: " << entry.second << std::endl;
        }
      }
      else {
        // no free entry found
        // rand generator for cache indexing
        static std::mt19937 rng(100);  // Use a fixed seed value for deterministic results
        std::uniform_int_distribution<uint16_t> indexDistribution(0, cache_size);
        int random_index = indexDistribution(rng) % cache_size;
        //std::cout << "random_index: " << random_index << std::endl;

        // no free entry found
        int max_count = 0;
        int max_count_key = -1;
        int i = 0;
        for (auto entry : aggressor_cache[index])
        {
          if (i == random_index) {
            max_count = entry.second;
            max_count_key = entry.first;
          }
          i++;
        }
        if (debug) 
        {
          std::cout << "CoMeT: No free entry found in aggressor cache!" << std::endl;
          std::cout << "  └  " << "Removing: " << max_count_key << std::endl;
          std::cout << "  └  " << "Adding: " << row_id << std::endl;
        }
        aggressor_cache[index].erase(max_count_key);
        aggressor_cache[index][row_id] = 0;
      }
    }

  }

  template <class T>
  void CoMeT<T>::completely_refresh_dram_rank()
  {
    // reset_period * 2 is the refresh period
    // divide by tREFI to get the number of refreshes needed
    int nREFI = this->ctrl->channel->spec->speed_entry[int(T::TimingCons::nREFI)];
    int number_of_refreshes = (reset_period_clk * 2) / nREFI;

    if (debug)
      std::cout << "Completely refreshing dram ranks with number of refreshes: " << number_of_refreshes << std::endl;

    for (int i = 0 ; i < number_of_refreshes; i++)
    {
      // Refresh request to rank_id
      std::vector<int> addr_vec(int(T::Level::MAX), -1);
      addr_vec[0] = this->ctrl->channel->id;

      Request req(addr_vec, Request::Type::REFRESH, nullptr);

      req.addr_vec[int(T::Level::Rank)] = 0;
      bool what = this->ctrl->priority_enqueue(req);
      assert(what);

      this->additional_rank_refreshes++;
    }
  }
}