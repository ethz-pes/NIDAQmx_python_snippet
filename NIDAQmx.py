import ctypes
import numpy


class NIDAQmx():
    """
    Class for controlling the DAQ NI-6215:
        - connect to the device
        - read and write
        - analog and digital signals

    This class:
        - use the "nicaiu.dll"
        - run on "MS Windows" but adaptation to Linux should be possible
        - should also be easy to adapt to other NI DAQ cards
        - was tested with Python 2.7 but should run with Python 3.x

    This class is meant as a lightweight code to be used as a "code snippet" and not as a full package.
    For more functionalities, you can use libraries like "NI-DAQmx Python".
    """

    def __init__(self, daq_name):
        """
        Constructor of the NIDAQmx class.
        """

        # assign the name and get the DLL (MS windows only)
        self.daq_name = daq_name
        self.NIDAQmx = ctypes.windll.nicaiu

        # number of channels for the DAQ NI-6215
        self.n = dict()
        self.n["analog_read"] = 16
        self.n["analog_write"] = 2
        self.n["digital_read"] = 4
        self.n["digital_write"] = 4

        # dict with the internal data of the DAQ NI-6215
        self.DAQmx_Val_RSE = 10083
        self.DAQmx_Val_Volts = 10348
        self.DAQmx_Val_GroupByChannel = 0
        self.DAQmx_Val_ChanPerLine = 0
        self.DAQmx_V_max = 10.0
        self.DAQmx_delay = 10.0

        # dict for the read/write tasks
        self.task = dict()

    def open(self):
        """
        Make the connection to the device.
        """

        # check the status and reset the device
        self._check_device()
        self.NIDAQmx.DAQmxResetDevice(self.daq_name)

        # counter for the task number
        self.task = dict()
        c = 0

        # analog read task
        self.task["analog_read"] = ctypes.c_ulong(c)
        self._daq_check(self.NIDAQmx.DAQmxCreateTask("", ctypes.byref(self.task["analog_read"])))
        self._daq_check(
            self.NIDAQmx.DAQmxCreateAIVoltageChan(
                self.task["analog_read"],
                self.daq_name + "/ai0:" + str(self.n["analog_read"] - 1),
                "",
                self.DAQmx_Val_RSE,
                ctypes.c_double(-self.DAQmx_V_max), ctypes.c_double(self.DAQmx_V_max),
                self.DAQmx_Val_Volts,
                None
            )
        )

        # digital read task
        self.task["digital_read"] = ctypes.c_ulong(c)
        self._daq_check(self.NIDAQmx.DAQmxCreateTask("", ctypes.byref(self.task["digital_read"])))
        self._daq_check(
            self.NIDAQmx.DAQmxCreateDIChan(
                self.task["digital_read"],
                self.daq_name + "/port0/line0:" + str(self.n["digital_read"] - 1),
                "",
                self.DAQmx_Val_ChanPerLine
            )
        )

        # analog write tasks
        for i in range(self.n["analog_write"]):
            self.task["analog_write_" + str(i)] = ctypes.c_ulong(c)
            c += 1
            self._daq_check(self.NIDAQmx.DAQmxCreateTask("", ctypes.byref(self.task["analog_write_" + str(i)])))
            self._daq_check(
                self.NIDAQmx.DAQmxCreateAOVoltageChan(
                    self.task["analog_write_" + str(i)], self.daq_name + "/ao" + str(i),
                    "",
                    ctypes.c_double(-self.DAQmx_V_max),
                    ctypes.c_double(self.DAQmx_V_max),
                    self.DAQmx_Val_Volts,
                    None
                )
            )

        # digital write tasks
        for i in range(self.n["digital_write"]):
            self.task["digital_write_" + str(i)] = ctypes.c_ulong(c)
            c += 1
            self._daq_check(self.NIDAQmx.DAQmxCreateTask("", ctypes.byref(self.task["digital_write_" + str(i)])))
            self._daq_check(
                self.NIDAQmx.DAQmxCreateDOChan(
                    self.task["digital_write_" + str(i)],
                    self.daq_name + "/port1/line" + str(i),
                    "",
                    self.DAQmx_Val_GroupByChannel
                )
            )

        # start the tasks
        for name in self.task:
            self._daq_check(self.NIDAQmx.DAQmxStartTask(self.task[name]))

    def close(self):
        """
        Close the connection to the device.
        """

        # stop the tasks
        for name in self.task:
            self.NIDAQmx.DAQmxStopTask(self.task[name])
            self.NIDAQmx.DAQmxClearTask(self.task[name])

        # reset the tasks and the device
        self.task = dict()
        self.NIDAQmx.DAQmxResetDevice(self.daq_name)

    def _daq_check(self, err):
        """
        Check the return code of the DAQ.
        """

        if err < 0:
            buf_size = 1024
            buf = ctypes.create_string_buffer('\000' * buf_size)
            self.NIDAQmx.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
            raise RuntimeError('NIDAQmx call failed with error %d: %s' % (err, repr(buf.value)))

    def _check_device(self):
        """
        Check if the DAQ is found.
        """

        buf_size = 1024
        buf = ctypes.create_string_buffer('\000' * buf_size)
        self._daq_check(self.NIDAQmx.DAQmxGetSysDevNames(ctypes.byref(buf), buf_size))

        name_tmp = ''
        namelist = []
        for ch in buf:
            if ch in '\000 \t\n':
                name_tmp = name_tmp.rstrip(',')
                if len(name_tmp) > 0:
                    namelist.append(name_tmp)
                    name_tmp = ''
                if ch == '\000':
                    break
            else:
                name_tmp += ch

        assert self.daq_name in namelist, "invalid device"

    def analog_read(self, n):
        """
        Read a analog channel.
        """

        data = numpy.zeros((self.n["analog_read"],), dtype=numpy.float64)
        self._daq_check(
            self.NIDAQmx.DAQmxReadAnalogF64(
                self.task["analog_read"],
                -1,
                ctypes.c_double(self.DAQmx_delay),
                self.DAQmx_Val_GroupByChannel, data.ctypes.data,
                self.n["analog_read"],
                ctypes.byref(ctypes.c_long()),
                None
            )
        )

        data = data.tolist()

        if isinstance(n, list):
            data = [data[i] for i in n]
        elif isinstance(n, int):
            data = data[n]
        else:
            raise RuntimeError("invalid channel")

        return data

    def digital_read(self, n):
        """
        Read one (or many) digital channel.
        """

        data = numpy.zeros((self.n["digital_read"],), dtype=numpy.uint8)
        self._daq_check(
            self.NIDAQmx.DAQmxReadDigitalLines(
                self.task["digital_read"],
                -1,
                ctypes.c_double(self.DAQmx_delay),
                self.DAQmx_Val_GroupByChannel,
                data.ctypes.data,
                self.n["digital_read"],
                ctypes.byref(ctypes.c_long()),
                ctypes.byref(ctypes.c_long()),
                None
            )
        )
        data = data.astype('bool')
        data = data.tolist()

        if isinstance(n, list):
            data = [data[i] for i in n]
        elif isinstance(n, int):
            data = data[n]
        else:
            raise RuntimeError("invalid channel")

        return data

    def analog_write(self, n, data):
        """
        Write (or many) analog channel.
        """

        assert n < self.n["analog_write"], "invalid channel"

        data = max(min(data, self.DAQmx_V_max), -self.DAQmx_V_max)

        self._daq_check(
            self.NIDAQmx.DAQmxWriteAnalogF64(
                self.task["analog_write_" + str(n)],
                1,
                0,
                ctypes.c_double(self.DAQmx_delay),
                self.DAQmx_Val_GroupByChannel,
                ctypes.byref(ctypes.c_double(data)),
                ctypes.byref(ctypes.c_long()),
                None
            )
        )

    def digital_write(self, n, data):
        """
        Write a digital channel.
        """

        assert n < self.n["digital_write"], "invalid channel"

        self._daq_check(
            self.NIDAQmx.DAQmxWriteDigitalLines(
                self.task["digital_write_" + str(n)],
                1,
                0,
                ctypes.c_double(self.DAQmx_delay),
                self.DAQmx_Val_GroupByChannel,
                ctypes.byref(ctypes.c_ushort(data)),
                ctypes.byref(ctypes.c_long()),
                None
            )
        )
