import time
import math
import numpy as np
import pyModeS as pms
import sys
from datetime import datetime
import scipy.signal as sig
import statistics as stats

def eng_string( x, format='%s', si=False):
    '''
    Returns float/int value <x> formatted in a simplified engineering format -
    using an exponent that is a multiple of 3.
    format: printf-style string used to format the value before the exponent.
    si: if true, use SI suffix for exponent, e.g. k instead of e3, n instead of
    e-9 etc.
    E.g. with format='%.2f':
        1.23e-08 => 12.30e-9
             123 => 123.00
          1230.0 => 1.23e3
      -1230000.0 => -1.23e6
    and with si=True:
          1230.0 => 1.23k
      -1230000.0 => -1.23M
    '''
    if x == 0:
        return '0'

    sign = ''
    if x < 0:
        x = -x
        sign = '-'
    exp = int( math.floor( math.log10( x)))
    exp3 = exp - ( exp % 3)
    x3 = x / ( 10 ** exp3)

    if si and exp3 >= -24 and exp3 <= 24 and exp3 != 0:
        exp3_text = 'yzafpnum kMGTPEZY'[ ( exp3 - (-24)) // 3]
    elif exp3 == 0:
        exp3_text = ''
    else:
        exp3_text = 'e%s' % exp3

    return ( '%s'+format+'%s') % ( sign, x3, exp3_text)

# Returns a np.array with each element of _r replicated times times
def replicate(a, c):
    r = []
    for x in a:
        r.extend([x] * c)
    return np.array(r)

# generates the code for a message
def msg2bin(msg, osr):
    ex_msg = "".join(['10' if x == '1' else '01' for x in pms.hex2bin(msg)])
    ex_preamble = "".join(['1' if x == 1 else '0' for x in preamble])
    ex_full = [1 if x == '1' else 0 for x in (ex_preamble + ex_msg)]
    return replicate(ex_full, osr)

pbits = 8
fbits = 112
preamble = [1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0]
th_amp_diff = 0.8   # signal amplitude threshold difference between 0 and 1 bit

class ADSBwave(object):
    def __init__(self, osr=1, verbose=0, lfp=None):
        super(ADSBwave, self).__init__()
        self.osr = osr                 # oversampling ratio
        self.verbose = verbose         # verbose mode 1=print decoded squitter, 2=stats, 3=plot
        self.debug = 0         
        self.preamble = replicate(preamble, self.osr)
        self.preamble_len = len(self.preamble)
        self.lfp = lfp

    def _print(self, msg):
        if self.lfp is None:
            print(msg)
        else:
            print(msg, file=self.lfp)
            
    def verify(self, cdata, xmsg):
        return self.decode(cdata) == xmsg

    def decode(self, cdata):
        """process raw IQ data in the buffer"""

        # how many packets did we see
        pkts = 0

        # oversampling rate is the rate above the minimum 2 MHz one
        osr = self.osr

        signal_buffer = np.absolute(cdata)
        if self._check_preamble(signal_buffer[0:pbits * 2 * osr]):
            frame_start = pbits * 2 * osr
            frame_end = (pbits + (fbits + 1)) * 2 * osr
            frame_length = (fbits + 1) * 2 * osr
            frame_pulses = signal_buffer[frame_start:frame_end]

            threshold = max(frame_pulses) * 0.2

            msgbin = []
            for j in range(0, frame_length, 2 * osr):
                p2 = frame_pulses[j : j + 2 * osr]
                if len(p2) < 2 * osr:
                    break

                if p2[0] < threshold and p2[osr] < threshold:
                    break
                elif p2[0] >= p2[osr]:
                    c = 1
                elif p2[0] < p2[osr]:
                    c = 0
                else:
                    msgbin = []
                    break

                msgbin.append(c)

            if len(msgbin) > 0:
                msghex = pms.bin2hex("".join([str(i) for i in msgbin]))
                # self._debug_msg(msghex)
                if self._check_msg(msghex):     # we have a good message
                    self._good_msg(msghex, cdata)
                else:
                    if self.verbose > 0:
                        self._print('Verify: failed check_msg')
                    return None
            else:
                self._print('Verify: len(msgbin) <= 0')
        else:
            self._print('Verify: No preamble')

        return msghex

    def _check_preamble(self, pulses):
        if len(pulses) != self.preamble_len:
            return False

        for i in range(self.preamble_len):
            if abs(pulses[i] - self.preamble[i]) > th_amp_diff:
                return False

        return True

    def _check_msg(self, msg):
        df = pms.df(msg)
        msglen = len(msg)
        if df == 17 and msglen == 28:
            if pms.crc(msg) == 0:
                return True
        elif df in [20, 21] and msglen == 28:
            return True
        elif df in [4, 5, 11] and msglen == 14:
            return True

        return False
        
    def _good_msg(self, msg, iq_window):
        # iq_window are our raw samples find the best alignment
        frame_window = amp = np.absolute(iq_window)

        # generate the expected time domain waveform from the message
        gold_msg = msg2bin(msg, self.osr) * max(frame_window)

        # correlate gold message to find best alignment
        besti = 0

        # generate DNN training vector
        n = len(gold_msg)

        if self.verbose >= 4:
            # make plot
            import matplotlib.pyplot as plt

            plt.plot(range(n), gold_msg, range(n), frame_window[besti:besti+n])
            plt.show()

    def _debug_msg(self, msg):
        df = pms.df(msg)
        if self._check_msg(msg):
            msglen = len(msg)
            if df == 17 and msglen == 28:
                print(msg, pms.icao(msg), pms.crc(msg))
            elif df in [20, 21] and msglen == 28:
                print(msg, pms.icao(msg))
            elif df in [4, 5, 11] and msglen == 14:
                print(msg, pms.icao(msg))
            if self.verbose >= 1:
                pms.tell(msg)
                print()
        elif self.debug:
            print("X", ":", msg)


