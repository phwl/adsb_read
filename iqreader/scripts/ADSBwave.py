import time
import numpy as np
import pyModeS as pms
import sys
from datetime import datetime
import scipy.signal as sig
import matplotlib.pyplot as plt
import statistics as stats

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
    def __init__(self, osr=1, verbose=0):
        super(ADSBwave, self).__init__()
        self.osr = osr                 # oversampling ratio
        self.verbose = verbose         # verbose mode 1=print decoded squitter, 2=stats, 3=plot
        self.debug = 0         
        self.preamble = replicate(preamble, self.osr)
        self.preamble_len = len(self.preamble)

    def verify(self, cdata, xmsg):
        return self.decode(cdata) == xmsg

    def decode(self, cdata):
        """process raw IQ data in the buffer"""

        # how many packets did we see
        pkts = 0

        # oversampling rate is the rate above the minimum 2 MHz one
        osr = self.osr

        msghex = ""
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
                    print('Verify: failed check_msg')
            else:
                print('Verify: len(msgbin) <= 0')
        else:
            print('Verify: No preamble')

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

    def _good_msg(self, msg, iq_window):
        # iq_window are our raw samples find the best alignment
        frame_window = amp = np.absolute(iq_window)

        # generate the expected time domain waveform from the message
        gold_msg = msg2bin(msg, self.osr) * 0.5

        # correlate gold message to find best alignment
        besti = 0

        # generate DNN training vector
        n = len(gold_msg)

        if self.verbose >= 4:
            # make plot
            plt.plot(range(n), gold_msg, range(n), frame_window[besti:besti+n])
            plt.set(xlabel='Sample', ylabel='Magnitude')
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

