import time
import traceback
import numpy as np
import pyModeS as pms
import statistics as stats
import sys
import adi
from datetime import datetime
import scipy.signal as sig
import matplotlib.pyplot as plt

modes_frequency = 1090e6

# Returns a np.array with each element of _r replicated times times
def replicate(a, c):
    r = []
    for x in a:
        r.extend([x] * c)
    return np.array(r)


# normalised cross-correlation
def n_xcorr(x, y):
    "Plot normalised cross-correlation between two signals. look for best position in x (y is the reference)"
    ynorm = y - stats.mean(y)
    n = len(ynorm)
    xc = np.zeros(len(x)-n)
    
    for i in range(len(xc)):
        t = x[i:i+n]
        tnorm = t - stats.mean(t)
        xc[i] = np.dot(ynorm, tnorm) / (np.linalg.norm(ynorm, 2) * np.linalg.norm(tnorm, 2))
    return(np.argmax(xc), xc)

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

class SDRFileReader(object):
    def __init__(self, **kwargs):
        super(SDRFileReader, self).__init__()
        self.signal_buffer = []  # amplitude of the sample only
        self.ciq_buffer = []  # iq samples

        # command line args
        self.debug = kwargs.get("debug", False)
        self.args = kwargs.get('args')
        self.upsample = args.upsample       # replicates incoming data 
        self.downsample = args.downsample   # decimates incoming data
        self.osr = args.osr                 # oversampling ratio
        self.verbose = args.verbose         # verbose mode 1=print decoded squitter, 2=stats, 3=plot

        # find input source
        self.ofile = self.args.ofile
        self.ifile = self.args.ifile
        if self.ifile == None:
            self.sdr = adi.Pluto("ip:pluto.local")
        elif self.ifile == '-':
            self.fd = open(0, 'rb')
        else:
            self.fd = open(self.ifile, 'rb')

        # member variables
        self.frames = 0
        self.raw_pipe_in = None
        self.stop_flag = False
        self.noise_floor = 1.0e6
        self.preamble = replicate(preamble, self.osr)
        self.preamble_len = len(self.preamble)

        # sample related parameters
        self.sampling_rate = 2e6 * self.osr
        self.samples_per_microsec = 2 * self.osr
        self.buffer_size = 1024 * 2000 * self.osr
        self.read_size = self.buffer_size // 2

        # set up SDR (if we have one)
        if self.ifile == None:
            print("sample rate: {}".format(self.sampling_rate))
            self.sdr.sample_rate = int(self.sampling_rate)
            self.sdr.rx_rf_bandwidth = int(self.sampling_rate) 
            self.sdr.rx_lo = int(modes_frequency)
            self.sdr.rx_buffer_size = int(self.read_size)
            self.sdr.gain_control_mode_chan0 = "fast_attack"

        self.exception_queue = None

    def _calc_noise(self):
        """Calculate noise floor"""
        window = self.samples_per_microsec * 100
        total_len = len(self.signal_buffer)
        means = (
            np.array(self.signal_buffer[: total_len // window * window])
            .reshape(-1, window)
            .mean(axis=1)
        )
        return min(means)

    def _process_buffer(self):
        """process raw IQ data in the buffer"""

        # how many packets did we see
        pkts = 0

        # oversampling rate is the rate above the minimum 2 MHz one
        osr = self.osr

        # update noise floor
        self.noise_floor = min(self._calc_noise(), self.noise_floor)

        # set minimum signal amplitude
        min_sig_amp = 3.162 * self.noise_floor  # 10 dB SNR

        # Mode S messages
        messages = []

        buffer_length = len(self.signal_buffer)

        if self.verbose >= 2:
            print("# self.noise_floor:  ", self.noise_floor)
            print("# self.signal_buffer:  mean", stats.mean(self.signal_buffer), 
                  "std:", stats.stdev(self.signal_buffer))

        i = 0
        while i < buffer_length:
            if self.signal_buffer[i] < min_sig_amp:
                i += 1
                continue

            if self._check_preamble(self.signal_buffer[i:i + pbits * 2 * osr]):
                frame_start = i + pbits * 2 * osr
                frame_end = i + (pbits + (fbits + 1)) * 2 * osr
                frame_length = (fbits + 1) * 2 * osr
                frame_window = self.signal_buffer[i-osr:frame_end+osr]
                frame_pulses = self.signal_buffer[frame_start:frame_end]

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
                    self._debug_msg(msghex)
                    if self._check_msg(msghex):
                        self.frames = self.frames + 1
                        messages.append([msghex, time.time()])
                        self._good_msg(msghex, frame_start, frame_end, frame_window)
                    else:
                        i += 1
                        continue

                # advance i with a jump
                i = frame_start + j

            else:
                i += 1


        # save buffer if we saw messages
        if len(messages) > 0 and self.ofile is not None:
            self._saveiq(self._complextoiq(self.ciq_buffer))

        # reset the buffer
        self.signal_buffer = self.signal_buffer[i:]
        self.ciq_buffer = self.ciq_buffer[i:]

        return messages

    # convert a byte array to a complex64 numpy array
    @staticmethod
    def _iqtocomplex(iqdata):
        rdata = np.frombuffer(iqdata, dtype=np.uint8).astype(np.float32)
        cdata = rdata.view(np.complex64)
        cdata = (cdata - complex(127, 127)) / 128
        return cdata

    # convert a complex64 numpy array to a byte array
    @staticmethod
    def _complextoiq(cdata):
        rdata = np.array(cdata).view(np.float64) * 128 + 127
        iq = rdata.astype(np.uint8)
        return iq

    def _saveiq(self, frame):
        # append info to index file
        fname = '{}-{}.iq'.format(self.ofile, self.frames)
        ft = open('{}-iqindex.txt'.format(self.ofile), 'a')
        ft.write('({},{},{})\n'.format(
                 fname, datetime.now(), self.noise_floor))
        ft.close()
        # write binary iq samples
        fs = open(fname, 'wb')
        fs.write(frame)
        fs.close()

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

    def _good_msg(self, msg, frame_start, frame_end, frame_window):
        # find the best alignment
        if self.verbose >= 3:
            # the expected bitstream
            gold_msg = msg2bin(msg, self.osr) * 0.5

            # correlate to find best alignment
            (i, xc) = n_xcorr(np.array(frame_window), np.array(gold_msg))
            n = len(gold_msg)

            # make plot
            fig, axs = plt.subplots(2)
            fig.suptitle('Alignment')
            axs[0].plot(range(n), gold_msg, range(n), frame_window[i:i+n])
            axs[0].set(xlabel='Sample', ylabel='Magnitude')
            axs[1].plot(xc[0:2*self.osr])
            axs[1].set(xlabel='Offset', ylabel='Normalised cross correlation')
            plt.show()

    def _debug_msg(self, msg):
        df = pms.df(msg)
        if self._check_msg(msg):
            msglen = len(msg)
            if df == 17 and msglen == 28:
                print(self.frames, ":", msg, pms.icao(msg), pms.crc(msg))
            elif df in [20, 21] and msglen == 28:
                print(self.frames, ":", msg, pms.icao(msg))
            elif df in [4, 5, 11] and msglen == 14:
                print(self.frames, ":", msg, pms.icao(msg))
            if self.verbose >= 1:
                pms.tell(msg)
                print()
        elif self.debug:
            print("X", ":", msg)


    def _read_callback(self, cdata, rtlsdr_obj):
        # scale to be in range [-1,1)
        if self.upsample > 1:
            cdata = replicate(cdata, self.upsample)
        amp = np.absolute(cdata)
        self.signal_buffer.extend(amp.tolist())
        self.ciq_buffer.extend(cdata.tolist())

        if len(self.signal_buffer) >= self.buffer_size:
            messages = self._process_buffer()
            self.handle_messages(messages)

    def handle_messages(self, messages):
        """re-implement this method to handle the messages"""
        #for msg, t in messages:
            #print("%15.9f %s" % (t, msg))
            #pass

    def stop(self, *args, **kwargs):
        sys.exit()

    def run(self, raw_pipe_in=None, stop_flag=None, exception_queue=None):
        self.raw_pipe_in = raw_pipe_in
        self.exception_queue = exception_queue
        self.stop_flag = stop_flag

        while True:
            # raw data are unsigned bytes (as IQ samples)
            if self.ifile == None:
                cdata = self.sdr.rx() / 256
            else:
                iqdata = self.fd.read(self.read_size)
                cdata = self._iqtocomplex(iqdata)
            if len(cdata) == 0:
                break
            if self.downsample > 1:
                cdata = sig.decimate(cdata, self.downsample)
            self._read_callback(cdata, None)



if __name__ == "__main__":
    import signal
    import argparse

    # parse command line
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ifile', action='store', 
                        default=None, help='Input file name')
    parser.add_argument('-o', '--ofile', action='store', 
                        default=None, help='Output file prefix')
    parser.add_argument('-r', '--osr', type=int, default=1, 
                        help='Oversampling ratio')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='Verbose mode')
    parser.add_argument('-p', '--profile', action='store_true', 
                        help='Enable profiling')
    parser.add_argument('-u', '--upsample', type=int, default=1, 
                        help='Upsample factor')
    parser.add_argument('-d', '--downsample', type=int, default=1, 
                        help='Downsample factor')
    args = parser.parse_args()


    # create SDR object
    rtl = SDRFileReader(args = args)

    signal.signal(signal.SIGINT, rtl.stop)

    rtl.debug = False

    if (args.profile):
        import cProfile
        cProfile.run('rtl.run()')
    else:
        rtl.run()
