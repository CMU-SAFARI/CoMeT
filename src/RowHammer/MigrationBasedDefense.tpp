#include "MigrationBasedDefense.h"

#include "AQUA.h"

namespace Ramulator{  
  template <class T>
  MigrationBasedDefense<T>* make_migration_based_defense(const YAML::Node& config, Controller<T>* ctrl)
  {
    if (!config["migration_based_defense"])
        return nullptr;

    const YAML::Node& rbd_config = config["migration_based_defense"];
    std::string rbd_type = rbd_config["type"].as<std::string>("AQUA");

    MigrationBasedDefense<T>* rbd = nullptr;

    if (rbd_type == "AQUA")
      rbd = new PARA<T>(rbd_config, ctrl);
    else
      throw std::runtime_error(fmt::format("Unrecognized migration based defense type: {}", rbd_type));

    std::cout << fmt::format("Migration based defense: {}", rbd->to_string()) << std::endl;
    return rbd;
  }

  template <class T>
  void MigrationBasedDefense<T>::enqueue_swap_rows(const std::vector<int>& addr_vec_source, const std::vector<int>& addr_vec_destination)
  {
  }

  template <class T>
  void MigrationBasedDefense<T>::schedule_swap_rows()
  {
  }
};