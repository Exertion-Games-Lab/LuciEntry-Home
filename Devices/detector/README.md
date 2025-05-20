## How to use brainflow on Raspberry PI
We need to compile the brainflow code by ourselves instead of using pip install
To install BrainFlow into Python on a Raspberry Pi and use it like a site-package, you need to compile the BrainFlow core module from source and then install the Python binding locally. Here are the steps:

1. **Install dependencies**
```
sudo apt-get update
sudo apt-get install cmake g++ python3-dev python3-pip
```

2. **Clone the BrainFlow repository to the site-package for python**
```
cd usr/lib/python3.11/site-packages
git clone https://github.com/brainflow-dev/brainflow.git
cd brainflow
```

3. **Compile the core module**
```
python tools/build.py
```
This will compile the core module for your Raspberry Pi architecture.

4. **Install the Python binding**
```
cd python_package
python3 -m pip install -e .
```
The `-e` flag installs the package in editable mode, allowing you to modify the source code and have the changes take effect immediately.

After following these steps, BrainFlow should be installed as a site-package in your Python environment on the Raspberry Pi. You can verify the installation by running:

```python
import brainflow
print(brainflow.__version__)
```

This should print the installed version of BrainFlow without any errors.[1][2][3]

Note that since BrainFlow is compiled from source, you may need to set the `LD_LIBRARY_PATH` environment variable to include the path to the compiled libraries. You can do this by adding the following line to your shell configuration file (e.g., `~/.bashrc`):

```
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/path/to/brainflow/installed/lib
```

Replace `/path/to/brainflow/installed/lib` with the actual path to the `lib` directory where the compiled libraries are located.

By following these steps, you should be able to use BrainFlow as a site-package in your Python environment on the Raspberry Pi, just like any other Python package installed via pip.


###What does the detector do?
The detector.py script uses the BrainFlow module and YASA [6] to detect the user's sleep stages and eye movements. It supports various sleep trackers, such as Muse S and OpenBCI. Please specify the sleep tracker as a parameter when running the script.

Once the detector reads brain and eye signals, it analyzes the data and outputs both the current sleep stage and whether the user has performed an LR signal (four consecutive left-to-right eye movements). This output is sent to the smartphone application: https://github.com/Exertion-Games-Lab/LucidReality-UI.

Citations:
[1] https://brainflow-openbci.readthedocs.io/en/latest/BuildBrainFlow.html
[2] https://brainflow.readthedocs.io/en/stable/BuildBrainFlow.html
[3] https://openbci.com/forum/index.php?p=%2Fdiscussion%2F2627%2Fusing-cyton-daisy-with-brainflow-on-raspberry-pi-4
[4] https://brainflow.org/get_started/
[5] https://mne.discourse.group/t/pip-install-in-conda-environment-brainflow/7088
[6] https://github.com/raphaelvallat/yasa
