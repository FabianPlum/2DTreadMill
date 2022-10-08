# 2DTreadmill
The omni-directional treadmill we were told not to build.

*"Yeah, I don't think that is going to work."*

## Installing dependencies
### **Python** OAK-D Environment Setup and example Execution

depthai environment for all actual inference things and the initial darknet -> tf conversion
```bash
conda create --name depthai python=3.7
conda activate depthai
```

then install additional dependencies
```bash
pip install depthai
pip install numpy==1.16.6
pip install tensorflow==1.14.0
pip install blobconverter==1.2.7
pip install openvino-dev[tensorflow]==2021.3
pip install Pillow
```

### **Arduino**

We try to keep the Arduino dependencies as light-weight as possible. 
For now, all that is required is the [PIDController library](https://www.arduino.cc/reference/en/libraries/pidcontroller/)

We're running an Arduino Mega 2560 and the latest [IDE](https://www.arduino.cc/en/software).
