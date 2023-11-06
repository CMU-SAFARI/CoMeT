#pragma once

#include "RefreshBasedDefense.h"
#include "Config.h"
#include "Controller.h"

#include <vector>
#include <random>

namespace Ramulator
{
  template <class T>
  class REGA : public RefreshBasedDefense<T>
  {
  public:
    REGA(const YAML::Node &config, Controller<T>* ctrl);
    ~REGA() = default;

  private:
    // REGA refreshes V different rows in a subarray every time
    // the subarray receives T activations
    int param_v;
    int param_t;
    // a victim row can be hammered at most 512/V * (T+1) + B times
    // Example V,T configuration for an nRH of 1K
    // T = 1, V = 1
    // B is the blast diameter
    // tRAS = 32 + (V − 1) × (17.5)
    
  };
};

#include "REGA.tpp"