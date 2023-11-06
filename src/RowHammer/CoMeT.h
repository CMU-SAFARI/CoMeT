#pragma once

#include "RefreshBasedDefense.h"
#include "Config.h"
#include "Controller.h"

#include <vector>
#include <unordered_map>
#include <random>
#include <functional>
#include <set>

namespace Ramulator
{
  template <class T>
  class CoMeT : public RefreshBasedDefense<T>
  {
  public:
    CoMeT(const YAML::Node &config, Controller<T>* ctrl);
    ~CoMeT() = default;
    /**
     * @brief: Schedule preventive refresh to victims of the aggressor row at addr_vec
     * TODO: Think about moving this to the parent class
     */
    void schedule_preventive_refresh(const std::vector<int> addr_vec);
    void tick();
    void update(typename T::Command cmd, const std::vector<int> &addr_vec, uint64_t open_for_nclocks, int core_id = 0);
    
    void finish() {}
    void completely_refresh_dram_rank();

    std::string to_string()
    {
    return fmt::format("Refresh-based RowHammer Defense\n"
                        "  └  "
                        "CoMeT\n");
    }

    typedef std::function<uint16_t(uint16_t)> HashFunction;


  private:
    int clk;
    int no_counters_per_hash;
    int no_hashes;
    int activation_threshold;
    int reset_period; // in nanoseconds
    int reset_period_clk; // in clock cycles
    bool debug = false;
    bool debug_verbose = false;
    bool debug_misuse = false;
    bool conservative = false;
    bool misuse_refresh = false;

    std::vector<std::deque<bool>> misuse_bits; // per bank misuse bits
    int misuse_history_length = 128; // ACTs 
    float misuse_threshold = 0.5; 

    // per bank activation count table
    // indexed using rank id, bank id
    // e.g., if rank 0, bank 4, index is 4
    // if rank 1, bank 5, index is 16 (assuming 16 banks/rank) + 5
    // each element is counter set for a hash function
    std::vector<std::vector<std::unordered_map<int, int>>> activation_count_table;
    std::vector<std::unordered_map<int, int>> aggressor_cache;
    int cache_size = 10;

    std::unordered_map<int, HashFunction> hashFunctions;

    std::unordered_map<int, HashFunction> getHashFunctions(uint16_t m, uint16_t k) {
      std::unordered_map<int, HashFunction> hashFunctions;
      std::mt19937 gen(100);  // Use a fixed seed value for deterministic results
      std::uniform_int_distribution<uint16_t> shiftDist(0, 15);
      std::set <uint16_t> shifts;
      for (uint16_t i = 0; i < k; ++i) {
          uint16_t shift = shiftDist(gen);
          while ( (k < 16) && shifts.find(shift) != shifts.end()) {
              shift = shiftDist(gen);
          }
          shifts.insert(shift);
          hashFunctions[i] = [shift, m](uint16_t address) -> uint16_t {
              return ((address << shift) | (address >> (16 - shift))) % m;
          };
      }
      if (debug) {
        //print the contents of the hashFunctions
        for (const auto& hashFunction : hashFunctions) {
            std::cout << "Hash function: " << hashFunction.first << " ";
            std::cout << "Hash: " << hashFunction.second(123) << std::endl;
        } 
      }
      return hashFunctions;
    }

    int nRAS = 0;
  };
}

#include "CoMeT.tpp"