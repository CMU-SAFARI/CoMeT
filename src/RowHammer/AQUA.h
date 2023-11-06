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
  class AQUA : public MigrationBasedDefense<T>
  {
  public:
    AQUA(const YAML::Node &config, Controller<T>* ctrl);
    ~AQUA() = default;
    /**
     * @brief: Schedule preventive refresh to victims of the aggressor row at addr_vec
     * TODO: Think about moving this to the parent class
     */
    void migrate_row(const std::vector<int> addr_vec);
    void tick();
    void update(typename T::Command cmd, const std::vector<int> &addr_vec, uint64_t open_for_nclocks);
    
    void finish() {}

    std::string to_string()
    {
    return fmt::format("Migration-based RowHammer Defense\n"
                        "  └  "
                        "AQUA\n");
    }

  private:
  };
}

#include "AQUA.tpp"