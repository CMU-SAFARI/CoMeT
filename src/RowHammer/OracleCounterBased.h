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
  class OracleCounterBased : public RefreshBasedDefense<T>
  {
  public:
    OracleCounterBased(const YAML::Node &config, Controller<T>* ctrl);
    ~OracleCounterBased() = default;
    /**
     * @brief: Schedule preventive refresh to victims of the aggressor row at addr_vec
     * TODO: Think about moving this to the parent class
     */
    void schedule_preventive_refresh(const std::vector<int> addr_vec);
    void tick();
    void update(typename T::Command cmd, const std::vector<int> &addr_vec, uint64_t open_for_nclocks, int core_id = 0);
    
    void finish() {}

    std::string to_string()
    {
    return fmt::format("Refresh-based RowHammer Defense\n"
                        "  └  "
                        "OracleCounterBased\n");
    }

    typedef std::function<uint16_t(uint16_t)> HashFunction;


  private:
    int clk;
    int no_counters_per_hash;
    int no_hashes;
    int activation_threshold;
    int reset_period; // in nanoseconds
    int reset_period_clk; // in clock cycles
    bool debug;
    bool debug_verbose;
    bool conservative = false;

    ScalarStat max_activation_count_table_size;
    ScalarStat preventive_refresh_count;     

    // per bank activation count table
    // indexed using rank id, bank id
    // e.g., if rank 0, bank 4, index is 4
    // if rank 1, bank 5, index is 16 (assuming 16 banks/rank) + 5
    // each element is counter set for a hash function
    std::unordered_map<int, long long int> activation_count_table;
    int nRAS = 0;
    
  };
}

#include "OracleCounterBased.tpp"