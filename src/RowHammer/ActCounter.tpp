#include "ActCounter.h"

namespace Ramulator
{
  template <class T>
  ActCounter<T>::ActCounter(const YAML::Node &config, Controller<T>* ctrl) : RefreshBasedDefense<T>(config, ctrl)
  {
    reset_period = config["reset_period"].as<int>();
    reset_period_clk = (int) (reset_period / (((float) ctrl->channel->spec->speed_entry[int(T::TimingCons::tCK_ps)])/1000));

    // Get organization configuration
    this->no_rows_per_bank = ctrl->channel->spec->org_entry.count[int(T::Level::Row)];
    this->no_bank_groups = ctrl->channel->spec->org_entry.count[int(T::Level::BankGroup)];
    this->no_banks = ctrl->channel->spec->org_entry.count[int(T::Level::Bank)];
    this->no_ranks = ctrl->channel->spec->org_entry.count[int(T::Level::Rank)];


    // Initialize activation count table
    // each table has no_table_entries entries
    for (int i = 0; i < this->no_banks * this->no_bank_groups * this->no_ranks; i++)
    {
      std::list<int> act_list;
      activations.push_back(act_list);
    }
  }

  template <class T>
  void ActCounter<T>::tick()
  {
    this->schedule_preventive_refreshes();

    // reset activation count table every reset_period
    // by setting every element to 0
    // and reset spillover counter
    if (clk % reset_period_clk == 0)
    {
        int unique_sum = 0;
        int sum125 = 0;
        int sum250 = 0;
        int sum500 = 0;
        int sum1000 = 0;  
        int sum_act_count = 0;
        for (int i = 0; i < this->no_banks * this->no_bank_groups * this->no_ranks; i++)
        {
            sum_act_count += activations[i].size();
            unordered_map<int, int> count; 
            //std::cout << i << ": Unique: " <<  activations[i].size() << std::endl;
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

            // iterate unordered map and count number of rows with activations >= 125, 250, 500, 1000
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
        //std::out << str(unique_sum/(this->no_banks * this->no_bank_groups * this->no_ranks)) << std::endl;
        avg_unique = unique_sum/(this->no_banks * this->no_bank_groups * this->no_ranks);
        avg_sum125 = sum125/(this->no_banks * this->no_bank_groups * this->no_ranks);
        avg_sum250 = sum250/(this->no_banks * this->no_bank_groups * this->no_ranks);
        avg_sum500 = sum500/(this->no_banks * this->no_bank_groups * this->no_ranks);
        avg_sum1000 = sum1000/(this->no_banks * this->no_bank_groups * this->no_ranks);
        act_count = sum_act_count/(this->no_banks * this->no_bank_groups * this->no_ranks);
    }

    clk++;
  }

  template <class T>
  void ActCounter<T>::update(typename T::Command cmd, const std::vector<int> &addr_vec, uint64_t open_for_nclocks, int core_id)
  {
    if (cmd != T::Command::PRE)
      return;
    
    int bank_group_id = addr_vec[int(T::Level::BankGroup)];
    int bank_id = addr_vec[int(T::Level::Bank)];
    int rank_id = addr_vec[int(T::Level::Rank)];
    int row_id = addr_vec[int(T::Level::Row)];

    int index = rank_id * this->no_banks * this->no_bank_groups + bank_group_id * this->no_banks + bank_id;

    activations[index].push_back(row_id);
    //std::cout << "pushed: " << row_id << "List: " ;
    //for (auto elem : activations[index])
    //    std::cout << elem << " ";
    //std::cout << std::endl;
  }

}