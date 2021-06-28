# adsb_read

Reads iq samples from stdin and captures ads-b packets. This code is derived
from [pyModeS](https://pypi.org/project/pyModeS/) and allows sampling
at higher sample rates (via the osr option), upsampling of the original
input (for testing) and saving of ADS-B buffers.

Try 'python iqreader.py -h' to see all the options.
