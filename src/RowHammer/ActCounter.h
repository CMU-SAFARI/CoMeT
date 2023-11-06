#pragma once

#include "RefreshBasedDefense.h"
#include "Config.h"
#include "Controller.h"

#include <vector>
#include <unordered_map>
#include <random>

namespace Ramulator
{
  template <class T>
  class ActCounter : public RefreshBasedDefense<T>
  {
  public:
    ActCounter(const YAML::Node &config, Controller<T>* ctrl);
    ~ActCounter() = default;
    /**
     * @brief: Schedule preventive refresh to victims of the aggressor row at addr_vec
     * TODO: Think about moving this to the parent class
     */
    void schedule_preventive_refresh(const std::vector<int> addr_vec);
    void tick();
    void update(typename T::Command cmd, const std::vector<int> &addr_vec, uint64_t open_for_nclocks, int core_id = 0);
    
    void finish() {
        if (avg_unique < 1) {
            std::cout << "No refreshes: ";
            int unique_sum = 0;
            int sum125 = 0;
            int sum250 = 0;
            int sum500 = 0;
            int sum1000 = 0;  
            int sum_act_count = 0;
            for (int i = 0; i < this->no_banks * this->no_bank_groups * this->no_ranks; i++)
            {
                                //std::cout << i << ": Non-Unique: " <<  activations[i].size() << std::endl;
                sum_act_count += activations[i].size();
                unordered_map<int, int> count; 
            int sizeK =  activations[i].size();
            
            for (int K = 0; K<sizeK; K++)
            {
                                        int j = activations[i].front();
                    activations[i].pop_front();
                    if (count.find(j) == count.end())
                        count.insert({j,1});
                    else
                    {
                        int c = count.find(j)->second;
                        count.erase(j);
                        count.insert({j, c+1});
                    }
                }
            for (auto j = count.begin(); j != count.end(); j++)
            {
                if (j->second >= 125)
                    sum125++;
                else if (j->second >= 250)
                    sum250++;
                else if (j->second >= 500)
                    sum500++;
                else if (j->second >= 1000)
                    sum1000++;
            }
                unique_sum += count.size();

            }
            std::cout << "Unique:," << (((float) unique_sum)/(this->no_banks * this->no_bank_groups * this->no_ranks)) << std::endl;
            std::cout << "Unique125:," << (((float) sum125)/(this->no_banks * this->no_bank_groups * this->no_ranks)) << std::endl;
            std::cout << "Unique250:," << (((float) sum250)/(this->no_banks * this->no_bank_groups * this->no_ranks)) << std::endl;
            std::cout << "Unique500:," << (((float) sum500)/(this->no_banks * this->no_bank_groups * this->no_ranks)) << std::endl;
            std::cout << "Unique1000:," << (((float) sum1000)/(this->no_banks * this->no_bank_groups * this->no_ranks)) << std::endl;
            std::cout << "ActCount/" << (((float) sum_act_count)/(this->no_banks * this->no_bank_groups * this->no_ranks)) << std::endl;
        }
        else {
            std::cout << "Unique:," << (avg_unique) << std::endl;
            std::cout << "Unique125:," << (avg_sum125) << std::endl;
            std::cout << "Unique250:," << (avg_sum250) << std::endl;
            std::cout << "Unique500:," << (avg_sum500) << std::endl;
            std::cout << "Unique1000:," << (avg_sum1000) << std::endl;
            std::cout << "ActCount/" << (act_count) << std::endl;
        }
    }

    std::string to_string()
    {
    return fmt::format("Refresh-based RowHammer Defense\n"
                        "  └  "
                        "ActCounter\n");
    }

  private:
    int clk;
    int no_table_entries;
    int activation_threshold;
    int reset_period; // in nanoseconds
    int reset_period_clk; // in clock cycles
    bool debug = false;
    bool debug_verbose = false;
    int avg_unique = -1;
    int avg_sum125 = -1;
    int avg_sum250 = -1;
    int avg_sum500 = -1;
    int avg_sum1000 = -1;
    int act_count = -1;

    // per bank activation count table
    // indexed using rank id, bank id
    // e.g., if rank 0, bank 4, index is 4
    // if rank 1, bank 5, index is 16 (assuming 16 banks/rank) + 5
    std::vector<std::list<int>> activations;
    // spillover counter per bank
    std::vector<int> spillover_counter;

    // take rowpress into account
    bool rowpress = false;
    int rowpress_increment_nticks = 0;
    int nRAS = 0;
  };
}

#include "ActCounter.tpp"