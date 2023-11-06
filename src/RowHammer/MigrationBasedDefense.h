#pragma once

#include <queue>

#include "Controller.h"
#include "Config.h"
#include "Request.h"

namespace Ramulator{

  template <class T>
  class Controller;

  template <class T>
  class MigrationBasedDefense {
    
    public:
      MigrationBasedDefense(const YAML::Node& config, Controller<T>* ctrl) 
      { 
        this->ctrl = ctrl; 
        debug_base = config["debug_base"].as<bool>(false); 
        blast_radius = config["blast_radius"].as<int>(1);
      }
      virtual ~MigrationBasedDefense() = default;
      virtual std::string to_string() = 0;
      virtual void tick() = 0;
      virtual void update(typename T::Command cmd, const std::vector<int>& addr_vec, uint64_t open_for_nclocks, int coreid = 0) = 0;
      virtual void finish() = 0;
    protected:
      // a queue of requests
      std::queue<Request> pending_Migration_queue;
      void enqueue_swap_rows(const std::vector<int>& addr_vec_source, const std::vector<int>& addr_vec_destination);
      void schedule_swap_rows();
      Controller<T>* ctrl;

      bool debug_base = false;
      int blast_radius = 1;

      int no_rows_per_bank;
      int no_banks; // b per bg
      int no_bank_groups; // bg per rank
      int no_ranks;
  };
}

#include "MigrationBasedDefense.tpp"