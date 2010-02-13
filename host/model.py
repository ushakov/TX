NUM_CTLS = 10
NUM_CHANS = 6
NUM_MODES = 3
CURVE_NODES = 7

class Location(object):
    def __init__(self):
        self.length = None
        self.offset = None
        self.array = None


class Type(object):
    def GetSize(self):
        return None


class Value(Type):
    def GetSize(self):
        return 1


class Array(Type):
    def __init__(self, el_type, el_num, names=None):
        self.el_type = el_type
        self.el_num = el_num
        self.names = names

    def GetSize(self):
        return self.el_type.GetSize() * self.el_num

    def GetElement(self, location, n):
        loc = Location()
        loc.length = self.el_type.GetSize()
        loc.offset = location.offset + n * self.el_type.GetSize()
        return loc

    def HaveNames(self):
        return bool(self.names)
    
    def GetName(self, n):
        if self.names:
            return self.names[n]
        return None

    def GetType(self):
        return self.el_type

    def GetLength(self):
        return self.el_num


class Empty(object):
    pass


class Struct(Type):
    def __init__(self, name, descr):
        """Descr is a list of tuples (name, type)"""
        self.name = name
        self.names = []
        self.data = {}
        self.size = 0
        self.horiz = False
        for t in descr:
            self.names.append(t[0])
            d = Empty()
            self.data[t[0]] = d
            d.offset = self.size
            d.type = t[1]
            self.size += d.type.GetSize()

    def GetName(self):
        return self.name

    def GetNames(self):
        return self.names

    def GetSize(self):
        return self.size

    def GetField(self, location, name):
        d = self.data[name]
        loc = Location()
        loc.length = d.type.GetSize()
        loc.offset = location.offset + d.offset
        return loc

    def GetType(self, name):
        d = self.data[name]
        return d.type

    def WantsHorizontalLayout(self):
        return self.horiz


class Var(object):
    def __init__(self, typ, loc = None):
        self.typ = typ
        if loc is None:
            self.loc = Location()
            self.loc.offset = 0
            self.loc.length = self.typ.GetSize()
        else:
            self.loc = loc

    def Get(self, what):
        if  isinstance(self.typ, Struct):
            return Var(self.typ.GetType(what),
                       self.typ.GetField(self.loc, what))
        if isinstance(self.typ, Array):
            return Var(self.typ.GetType(),
                       self.typ.GetElement(self.loc, what))
        raise RuntimeError("Unsupported type for Get")


def PrintType(typ, pref=""):
    if isinstance(typ, Struct):
        print "%sStruct:" % (pref)
        for name in typ.GetNames():
            print "%s  %s:" % (pref, name)
            PrintType(typ.GetType(name), pref + "    ")
    elif isinstance(typ, Array):
        print "%sArray[%d]:" % (pref, typ.GetLength())
        PrintType(typ.GetType(), pref + "  ")
    elif isinstance(typ, Value):
        print "%sValue" % pref
    else:
        raise RuntimeError("Unknown type " + typ)

CONTROL_NAMES = [
    "Ailerons",
    "Elevator",
    "Throttle",
    "Rudder",
    "Pot_A",
    "Pot_B",
    "SW_A",
    "SW_B",
    "Virt_A",
    "Virt_B",
    ]

MODE_NAMES = [
    "Normal",
    "Landing",
    "Pilotage"
    ]

CURVE_NAMES = [
    "-100",
    "-67",
    "-33",
    "0",
    "33",
    "67",
    "100"
    ]

Control = Struct("Control", [
    ('low_ep', Value()),
    ('high_ep', Value()),
    ('low_ep2', Value()),
    ('high_ep2', Value()),
    ('curve', Array(Value(), CURVE_NODES, CURVE_NAMES)),
    ('source', Value())
    ])

Channel = Struct("Channel", [
    ('mix', Array(Value(), NUM_CTLS, CONTROL_NAMES)),
    ('reverse', Value())
    ])

Mode = Struct("Mode", [
    ('controls', Array(Control, NUM_CTLS, CONTROL_NAMES)),
    ('channels', Array(Channel, NUM_CHANS)),
    ])
Mode.horiz = True

Model = Struct("Model", [
    ('num_ch', Value()),
    ('modes', Array(Mode, NUM_MODES, MODE_NAMES)),
    ])

model = Var(Model)
