# adsb_read

Reads iq samples from a file or stdin, capturing ADS-B packets. This code is derived
from [pyModeS](https://pypi.org/project/pyModeS/) and allows sampling
at higher sample rates (via the osr option), upsampling of the original
input (for testing) and saving of buffers.

```capture/x-iqindex.txt``` is an example of a capture index. The contents look like
```
(x-1.iq,2021-06-29 17:30:34.286561,0.00793687250930816)
(x-2.iq,2021-06-29 17:30:34.391115,0.00793687250930816)
(x-3.iq,2021-06-29 17:30:34.630880,0.00793687250930816)
(x-4.iq,2021-06-29 17:30:34.720284,0.00793687250930816)
(x-5.iq,2021-06-29 17:30:50.081858,0.00793687250930816)
(x-6.iq,2021-06-29 17:30:50.174330,0.00793687250930816)
(x-7.iq,2021-06-29 17:30:50.249017,0.00793687250930816)
(x-8.iq,2021-06-29 17:30:50.338001,0.00793687250930816)
```
Each row contains (file name, time stamp, noise_floor). The files are 
.iq files but to avoid mixing up temporary files and archived files,
I've added the suffix .raw. Those files can also be seen in the
```capture``` directory.


Try 'python iqreader.py -h' to see all the options.
