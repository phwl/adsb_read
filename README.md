# adsb_read

Reads iq samples from an Analog Devices ADALM Pluto, a file or stdin, capturing ADS-B packets. This code is derived
from [pyModeS](https://pypi.org/project/pyModeS/) and allows sampling
at higher sample rates (via the osr option), upsampling of the original
input (for testing), saving of buffers etc.

An example of usage with the Pluto is given below. We use osr=4 so the sampling rate is 4x nominal i.e. 4*2MHz=8MHz, and specify that the output training set is written to **/srv/breamdisk/adsb-data/x1-#**. Note that the program never overwrites files in this mode so in the example, the output is written to **/srv/breamdisk/adsb-data/x1-1700-tdata.bin** because that was the first new file name. The numbered outputs show the ADS-B messages received.

```bash
$ ./adsb_read.py --osr 4 -v -t /srv/breamdisk/adsb-data/x1
sample rate: 8000000.0
0 : 20100120E3DAF4 B1348B
1 : 284844283BB1D1 BA9C8B
Writing training file to /srv/breamdisk/adsb-data/x1-1700-tdata.bin
2 : 582BA19BFDE456 2BA19B
3 : 20000122F3DAF4 7C6C80
4 : 20000522CBECF4 7C6C80
Writing training file to /srv/breamdisk/adsb-data/x1-1701-tdata.bin
5 : 284108082C3366 FB7BD7
6 : 24040722D3DAD4 E0E5E8
7 : 20000122F3DAF4 7C6C80
Writing training file to /srv/breamdisk/adsb-data/x1-1702-tdata.bin
8 : 20000122F3DAF4 7C6C80
9 : 280008082C0822 7C6C80
```

An example of how to read the data is available in ```scripts/gentset.py```.

```bash
$ scripts/gentset.py
...
file: /srv/breamdisk/adsb-data/x1-1700-tdata.bin 2 11269
2021-07-05 15:51:20.880429
             Message: 20100120E3DAF4 
        ICAO address: B1348B 
     Downlink Format: 4 

2021-07-05 15:51:27.794353
             Message: 284844283BB1D1 
        ICAO address: BA9C8B 
     Downlink Format: 5 
...
2021-07-05 16:11:02.323771
             Message: 8D7C6CA0582155E8485A5E85313D 
        ICAO address: 7C6CA0 
     Downlink Format: 17 
            Protocol: Mode-S Extended Squitter (ADS-B) 
                Type: Airborne position (with barometric altitude) 
          CPR format: Odd 
        CPR Latitude: 0.476837158203125 
       CPR Longitude: 0.1764984130859375 
            Altitude: 5525 feet

Total records= 11693 verified= 11659
Total file size 206.787667M
```

If you set the verbosity to 4 or more (```$ ./gentset.py -vvvv```), a plot of the waveforms as illustrated below is given. The plot shows the first 200 samples of a squitter with the received waveform in orange, and the ideal waveform in blue.
![match_plot](match_plot.png)

Try ```python adsb_read.py -h``` to see all the options.
To understand how to use the program take a look at the Makefile. 


## Detailed Installation Instructions
### Linux
In Terminal run:
```bash
sudo apt update
sudo apt upgrade
ping 192.168.2.1
```

Download Libiio file from https://github.com/analogdevicesinc/libiio/releases/tag/v0.23 (or latest) and install using:
```bash
sudo apt-get update
sudo apt-get install libaio1 libserialport0
gunzip Linux-Ubuntu-20.04-x86_64.tar.gz
tar xvf Linux-Ubuntu-20.04-x86_64.tar
cd Linux-Ubuntu-20.04-x86_64/
sudo dpkg -i libiio-0.23.g92d6a35-Linux.deb
```

After attaching Pluto via USB try the following:
```bash
iio_info -s
```
You should get something like:
```bashLibrary version: 0.23 (git tag: 92d6a35)
Compiled with backends: local xml ip usb serial
Unable to create Local IIO context : No such file or directory (2)
Available contexts:
        0: 192.168.2.1 (Analog Devices PlutoSDR Rev.C (Z7010-AD9363A)), serial=1044734c96050013070021004a464f3280 [ip:pluto.local]
```
Now you should be able to secure shell to the Pluto using password 'analog'. Exit once you've finished poking around.
```bash
ssh root@192.168.2.1
```

Install Anlog devices IIO module:
```bash
mkdir -p ~/CruxSEI/Project
cd ~/CruxSEI/Projects
git clone https://github.com/analogdevicesinc/libad9361-iio.git
cd libad9361-iio/
cmake ./
make -j3
sudo make install
cd ..
git clone https://github.com/analogdevicesinc/pyadi-iio.git
cd pyadi-iio/
sudo python3 setup.py install
```

Then clone this Repo:
 ```bash
cd ..
git clone git@github.com:phwl/adsb_read.git
    OR
git clone https://github.com/phwl/adsb_read.git
```

Install Ananconda if you haven't yet or skip this ...
```bash
cd /tmp
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install libgl1-mesa-glx libegl1-mesa libxrandr2 libxrandr2 libxss1 libxcursor1 libxcomposite1 libasound2 libxi6 libxtst6
wget https://repo.anaconda.com/archive/Anaconda3-2021.05-Linux-x86_64.sh
sha256sum Anaconda3-2021.05-Linux-x86_64.sh
bash Anaconda3-2021.05-Linux-x86_64.sh
sudo bash Anaconda3-2021.05-Linux-x86_64.sh
source ~/.bashrc
sudo apt install python3-pip
```

Add the required Python modules:
```bash
cd ~/CruxSEI/Projects/adsb_read
pip3 install --user numpy pyModeS scipy matplotlib
python3 adsb_read.py -h
```

Test adsb_read.py:
```bash
make test
```

### Windows10 Ubuntu 

Download and install the Windows driver : PlutoSDR-M2k-USB-Drivers.exe - v0.7 (https://github.com/analogdevicesinc/plutosdr-m2k-drivers-win/releases/download/v0.7/PlutoSDR-M2k-USB-Drivers.exe)

Using Explore open Pluto Device and double-click info.htm
Upgrade the Firmware on Pluto if web page indicates a new version is available by following instructions on the web page
Once done test if Pluto is responding to 
```bash
ping 192.168.2.1
```

In Ubuntu Terminal
```bash
sudo apt update
sudo apt upgrade
ping 192.168.2.1
```

Download Libiio file and install using:
```bash
sudo dpkg -i libiio-0.21.g565bf68-ubuntu-18.04-amd64.deb
```

May have to install libavahi-client3 and also may have to fix broken install:
(optional)
```bash
sudo apt --fix-broken install
sudo apt-get install libavahi-client3
```

Testing on Ubuntu terminal I get this error ...
```bash
iio_info -s

Library version: 0.21 (git tag: 565bf68)
Compiled with backends: local xml ip usb serial
Unable to create Local IIO context : No such file or directory
ERROR: Unable to create Avahi DNS-SD client :Daemon not running
Scanning for IIO contexts failed: Text file busy
```

But when I use the IP address it seems fine so keep going ...
```bash
iio_info -u ip:192.168.2.1

Library version: 0.21 (git tag: 565bf68)
Compiled with backends: local xml ip usb serial
IIO context created with network backend.
Backend version: 0.21 (git tag: v0.21  )
Backend description string: 192.168.2.1 Linux (none) 5.4.0-212055-gb05d16429dac #403 SMP PREEMPT Tue Mar 30 12:57:31 CEST 2021 armv7l
IIO context has 9 attributes:
        hw_model: Analog Devices PlutoSDR Rev.C (Z7010-AD9363A)
        hw_model_variant: 1
        hw_serial: 1044730a19970009e8ff1200b4807b2f9a
		...
```

Test ssh to the Pluto
```bash
ssh root@192.168.2.1  (password: analog)

Welcome to:
______ _       _        _________________
| ___ \ |     | |      /  ___|  _  \ ___ \
| |_/ / |_   _| |_ ___ \ `--.| | | | |_/ /
|  __/| | | | | __/ _ \ `--. \ | | |    /
| |   | | |_| | || (_) /\__/ / |/ /| |\ \
\_|   |_|\__,_|\__\___/\____/|___/ \_| \_|

v0.33
https://wiki.analog.com/university/tools/pluto
#
exit
```

Now install Python3 dependencies
```bash
git clone https://github.com/analogdevicesinc/libad9361-iio.git
cd libad9361-iio
cmake ./
make -j3
sudo make install

git clone https://github.com/analogdevicesinc/pyadi-iio.git
cd pyadi-iio
sudo python3 setup.py install
```

Now test Python3 Module
```bash
python3
```
```python
import adi
sdr = adi.Pluto('ip:192.168.2.1') # or whatever your Pluto's IP is
sdr.sample_rate = int(2.5e6)
sdr.rx()
array([ -7.-13.j,   6.+10.j, -10. +1.j, ...,  11. +6.j,   1. -6.j,
        -1.+27.j])  # Values in array will differ.
exit(0)
```

Changing Pluto’s IP Address
If for some reason the default IP of 192.168.2.1 does not work because you already have a 192.168.2.0 subnet, or because you want multiple Pluto’s connected at the same time, you can change the IP using these steps:

1) Edit the config.txt file on the PlutoSDR mass storage device (i.e., the USB-drive looking thing that shows up after you plug in the Pluto). Enter the new IP you want.
2) Eject the mass storage device (don’t unplug the Pluto!). In Ubuntu 18 there’s an eject symbol next to the PlutoSDR device, when looking at the file explorer.
3) Wait a few seconds, and then cycle power by unplugging the Pluto and plugging it back in. Go back into the config.txt to determine if your change(s) saved.

“Hack” PlutoSDR to Increase RF Range
The PlutoSDR’s ship with a limited center frequency range and sampling rate, but the underlying chip is capable of much higher frequencies.

Enable tuning tune up to 6 GHz and down to 70 MHz, not to mention use a sample rate up to 56 MHz!
```bash
ssh root@192.168.2.1  (pw: analog)
fw_setenv compatible ad9364
reboot
```

