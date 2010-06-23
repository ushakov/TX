import serial
import gtk

import model
import vis

class Data(object):
    def __init__(self, comm):
        self.array = []
        self.comm = comm

    def Get(self, location):
        return self.array[location.offset]

    def Set(self, location, value):
        if self.array[location.offset] != value:
            print "setting", location.offset, "to", value
            self.array[location.offset] = value
            if self.comm:
                self.comm.Set(location.offset, value)
        else:
            print "hit at ", location.offset, "to", value


class TXComm(object):
    def __init__(self):
        self.port = serial.Serial("/dev/ttyUSB0", 57600)
        self.port.setTimeout(0.001)
        self.line = ""

    def Check(self):
        r = self.port.readline()
        if not r:
            return None
        if r[-1] != '\n':
            self.line += r
            return None
        if len(r) > 1 and r[-2] == '\r':
            r = r[:-2]
        if not r:
            return None
        whole_input = self.line + r
        self.line = ""
        print "<<<", whole_input
        return whole_input

    def Send(self, line):
        print ">>>", line
        self.port.write(line)
        self.port.write("\r\n")

    def Set(self, where, val):
        if val < 0:
            val += 256
        self.Send("S %03x %02x" % (where, val))
        while True:
            line = self.Check()
            if not line:
                continue
            if line == "DONE":
                return
            if line == "Err":
                raise RuntimeError("comm error")

    def GetData(self):
        self.Send("D")
        array = []
        while True:
            line = self.Check()
            if not line:
                continue
            if line == "DONE":
                break
            if line == "Err":
                raise RuntimeError("comm error")
            if line[3] != ':':
                continue
            off = int(line[:3], 16)
            if off != len(array):
                raise RuntimeError("comm out of sync: off=%s, received %s" % (
                    off, len(array)))
            f = line[4:].split()
            for hx in f:
                val = int(hx, 16)
                if val > 128:
                    val -= 256
                array.append(val)
        d = Data(self)
        d.array = array
        return d

    def Reset(self):
        self.Send("R R R")
        while True:
            line = self.Check()
            if not line:
                continue
            if line == "DONE":
                return

