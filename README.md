# adsb_read

Reads iq samples from a file or stdin, capturing ADS-B packets. This code is derived
from [pyModeS](https://pypi.org/project/pyModeS/) and allows sampling
at higher sample rates (via the osr option), upsampling of the original
input (for testing) and saving of buffers.

Try 'python iqreader.py -h' to see all the options.
