

#!/bin/bash

# Updating the package list
sudo apt-get update

# Installing G++
sudo apt-get install -y g++-9
# Setting G++ 11 as the default
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-9 200
sudo update-alternatives --set g++ /usr/bin/g++-9

if g++-9 --version; then
    echo "G++ 11 installed successfully."

    # Setting G++ 11 as the default with a higher priority
    sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-9 100

    # Selecting G++ 11 as the default
    sudo update-alternatives --set g++ /usr/bin/g++-9
else
    echo "Failed to install G++ 9."
    exit 1
fi
# Installing CMake
sudo apt-get install -y cmake

# Installing Python 3 and pip
sudo apt-get install -y python3 python3-pip

# Installing pandas, seaborn, and IPython using pip
pip3 install pandas seaborn ipython

# Echoing the versions of the installed packages
echo "G++ version:"
g++ --version

echo "CMake version:"
cmake --version

echo "Python packages version:"
pip3 freeze | grep -E 'pandas|seaborn|ipython'



mkdir -p build
cd build
cmake ..
make -j
cp ramulator ..
pwd
cd ..
