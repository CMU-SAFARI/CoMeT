#include "OracleCounterBased.h"

namespace Ramulator
{
    template <class T>
    OracleCounterBased<T>::OracleCounterBased(const YAML::Node &config, Controller<T> *ctrl) : RefreshBasedDefense<T>(config, ctrl)
    {
        activation_threshold = config["activation_threshold"].as<int>();
        reset_period = config["reset_period"].as<int>();
        debug = config["debug"].as<bool>();
        debug_verbose = config["debug_verbose"].as<bool>();
        reset_period_clk = (int)(reset_period / (((float)ctrl->channel->spec->speed_entry[int(T::TimingCons::tCK_ps)]) / 1000));
        conservative = config["conservative"].as<bool>(false);

        // Get organization configuration
        this->no_rows_per_bank = ctrl->channel->spec->org_entry.count[int(T::Level::Row)];
        this->no_bank_groups = ctrl->channel->spec->org_entry.count[int(T::Level::BankGroup)];
        this->no_banks = ctrl->channel->spec->org_entry.count[int(T::Level::Bank)];
        this->no_ranks = ctrl->channel->spec->org_entry.count[int(T::Level::Rank)];

        if (debug)
        {
            std::cout << "OracleCounterBased: activation_threshold: " << activation_threshold << std::endl;
            std::cout << "OracleCounterBased: reset_period: " << reset_period << std::endl;
            std::cout << "OracleCounterBased: reset_period_clk: " << reset_period_clk << std::endl;
            std::cout << "  └  tCK: " << ((float)ctrl->channel->spec->speed_entry[int(T::TimingCons::tCK_ps)]) << std::endl;
            std::cout << "OracleCounterBased: no_rows_per_bank: " << this->no_rows_per_bank << std::endl;
            std::cout << "OracleCounterBased: no_bank_groups: " << this->no_bank_groups << std::endl;
            std::cout << "OracleCounterBased: no_banks: " << this->no_banks << std::endl;
            std::cout << "OracleCounterBased: no_ranks: " << this->no_ranks << std::endl;
        }

        max_activation_count_table_size
            .name("max_activation_table_size")
            .desc("The maximum size of the activation count table")
            .precision(0);

        preventive_refresh_count
            .name("preventive_refresh_count")
            .desc("The number of preventive refreshes")
            .precision(0);
    }

    template <class T>
    void OracleCounterBased<T>::tick()
    {
        this->schedule_preventive_refreshes();


        // reset activation count table every reset_period
        // by setting every element to 0
        if (clk % reset_period_clk == 0)
        {
            if (debug_verbose)
              std::cout << "OracleCounterBased: Resetting activation count table" << std::endl;
            activation_count_table.clear();
        }

        clk++;
    }

    template <class T>
    void OracleCounterBased<T>::update(typename T::Command cmd, const std::vector<int> &addr_vec, uint64_t open_for_nclocks, int core_id)
    {

        if (cmd != T::Command::PRE)
            return;

        int bank_group_id = addr_vec[int(T::Level::BankGroup)];
        int bank_id = addr_vec[int(T::Level::Bank)];
        int rank_id = addr_vec[int(T::Level::Rank)];
        int row_id = addr_vec[int(T::Level::Row)];

        int index = rank_id * this->no_banks * this->no_bank_groups + bank_group_id * this->no_banks + bank_id;

        long long int counter = 0;


        if (activation_count_table.find(index) == activation_count_table.end())
        {
            activation_count_table.insert(std::make_pair(index, 1));
            if(max_activation_count_table_size.value() < activation_count_table.size())
                max_activation_count_table_size = activation_count_table.size();
        }
        else
        {
            activation_count_table[index]++;
            counter = activation_count_table[index];
        }

        if (counter > activation_threshold)
        {
            if (debug_verbose)
              std::cout << "OracleCounterBased: Preventing refresh on row " << row_id << std::endl;
            this->enqueue_preventive_refresh(addr_vec);
            activation_count_table.erase(index);
        }

        if (debug_verbose)
        {
            std::cout << "OracleCounterBased: ACT on row " << row_id << std::endl;
            std::cout << "  └  "
                      << "rank: " << rank_id << std::endl;
            std::cout << "  └  "
                      << "bank_group: " << bank_group_id << std::endl;
            std::cout << "  └  "
                      << "bank: " << bank_id << std::endl;
        }
    }

}