import time
import traceback
import numpy as np
import pyModeS as pms
import sys

sampling_rate = 2e6
smaples_per_microsec = 2

modes_frequency = 1090e6
buffer_size = 1024 * 200
read_size = 1024 * 100
buffer_size = buffer_size * 2
read_size = read_size * 2

pbits = 8
fbits = 112
preamble = [1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0]
th_amp_diff = 0.8  # signal amplitude threshold difference between 0 and 1 bit

# convert a byte array to a complex64 numpy array
def iqtocomplex(iqdata):
    rdata = np.frombuffer(iqdata, dtype=np.uint8).astype(np.float32)
    cdata = rdata.view(np.complex64)
    return cdata

# convert a complex64 numpy array to a byte array
def complextoiq(cdata):
    rdata = cdata.view(np.float64)
    iq = rdata.astype(np.uint8)
    return iq

class SDRFileReader(object):
    def __init__(self, **kwargs):
        super(SDRFileReader, self).__init__()
        self.signal_buffer = []  # amplitude of the sample only
        self.iq_buffer = []  # iq samples
        self.fname = kwargs.get('fname', '/dev/null')

        if self.fname == '-':
            self.fd = open(0, 'rb')
        else:
            self.fd = open(self.fname, 'rb')


        self.iqfname = 'iqframe'
        self.write = self.fname = kwargs.get('wflag')
        self.frames = 0
        self.debug = kwargs.get("debug", False)
        self.raw_pipe_in = None
        self.stop_flag = False
        self.noise_floor = 1e6

        self.exception_queue = None

    def _calc_noise(self):
        """Calculate noise floor"""
        window = smaples_per_microsec * 100
        total_len = len(self.signal_buffer)
        means = (
            np.array(self.signal_buffer[: total_len // window * window])
            .reshape(-1, window)
            .mean(axis=1)
        )
        return min(means)

    def _process_buffer(self):
        """process raw IQ data in the buffer"""

        # update noise floor
        self.noise_floor = min(self._calc_noise(), self.noise_floor)

        # set minimum signal amplitude
        min_sig_amp = 3.162 * self.noise_floor  # 10 dB SNR

        # Mode S messages
        messages = []

        buffer_length = len(self.signal_buffer)

        i = 0
        while i < buffer_length:
            if self.signal_buffer[i] < min_sig_amp:
                i += 1
                continue

            if self._check_preamble(self.signal_buffer[i : i + pbits * 2]):
                frame_start = i + pbits * 2
                frame_end = i + pbits * 2 + (fbits + 1) * 2
                frame_length = (fbits + 1) * 2
                frame_pulses = self.signal_buffer[frame_start:frame_end]

                threshold = max(frame_pulses) * 0.2

                msgbin = []
                for j in range(0, frame_length, 2):
                    p2 = frame_pulses[j : j + 2]
                    if len(p2) < 2:
                        break

                    if p2[0] < threshold and p2[1] < threshold:
                        break
                    elif p2[0] >= p2[1]:
                        c = 1
                    elif p2[0] < p2[1]:
                        c = 0
                    else:
                        msgbin = []
                        break

                    msgbin.append(c)

                # advance i with a jump
                i = frame_start + j

                if len(msgbin) > 0:
                    msghex = pms.bin2hex("".join([str(i) for i in msgbin]))
                    if self._check_msg(msghex):
                        messages.append([msghex, time.time()])
                        if self.write:
                            self._saveiq(complextoiq(np.array(self.iq_buffer)))

                    if self.debug:
                        self._debug_msg(msghex)

            # elif i > buffer_length - 500:
            #     # save some for next process
            #     break
            else:
                i += 1

        # reset the buffer
        self.signal_buffer = self.signal_buffer[i:]
        self.iq_buffer = self.iq_buffer[i:]

        return messages

    def _saveiq(self, frame):
        fs = open('{}-{}.iq'.format(self.iqfname, self.frames), 'wb')
        fs.write(frame)
        fs.close()
        self.frames = self.frames + 1

    def _check_preamble(self, pulses):
        if len(pulses) != 16:
            return False

        for i in range(16):
            if abs(pulses[i] - preamble[i]) > th_amp_diff:
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

    def _debug_msg(self, msg):
        df = pms.df(msg)
        msglen = len(msg)
        if df == 17 and msglen == 28:
            print(msg, pms.icao(msg), pms.crc(msg))
        elif df in [20, 21] and msglen == 28:
            print(msg, pms.icao(msg))
        elif df in [4, 5, 11] and msglen == 14:
            print(msg, pms.icao(msg))
        else:
            print("[*]", msg, "df={}, mesglen={}".format(df, msglen))
            pass

    def _read_callback(self, iqdata, rtlsdr_obj):
        cdata = iqtocomplex(iqdata)
        # scale them to be in range [-1,1)
        amp = np.absolute((cdata - complex(127,127)) / 128)
        self.signal_buffer.extend(amp.tolist())
        self.iq_buffer.extend(cdata.tolist())

        if len(self.signal_buffer) >= buffer_size:
            messages = self._process_buffer()
            self.handle_messages(messages)

    def handle_messages(self, messages):
        """re-implement this method to handle the messages"""
        for msg, t in messages:
            # print("%15.9f %s" % (t, msg))
            pass

    def stop(self, *args, **kwargs):
        self.sdr.close()

    def run(self, raw_pipe_in=None, stop_flag=None, exception_queue=None):
        self.raw_pipe_in = raw_pipe_in
        self.exception_queue = exception_queue
        self.stop_flag = stop_flag

        while True:
            # raw data are unsigned bytes (as IQ samples)
            iqdata = self.fd.read(read_size)
            if len(iqdata) == 0:
                break
            self._read_callback(iqdata, None)



if __name__ == "__main__":
    import signal
    import argparse

    # parse command line
    parser = argparse.ArgumentParser()
    parser.add_argument('fname', metavar='fname', type=str, help='Input file name')
    parser.add_argument('-w', '--write', action='store_true', help='Write files')
    args = parser.parse_args()

    # create SDR object
    rtl = SDRFileReader(fname=args.fname, wflag=args.write)

    signal.signal(signal.SIGINT, rtl.stop)

    rtl.debug = True
    rtl.run()
