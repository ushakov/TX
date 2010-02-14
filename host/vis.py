import gtk
import gobject

import model

class ComplexArrayWidget(gtk.Frame):
    def __init__(self, var, data, label):
        gtk.Frame.__init__(self)
        flab = gtk.HBox()
        text = gtk.Label(label)
        flab.add(text)
        self.combo = gtk.combo_box_new_text()
        flab.add(self.combo)
        self.var = var
        self.data = data
        for i in range(var.typ.GetLength()):
            if var.typ.HaveNames():
                self.combo.append_text(var.typ.GetName(i))
            else:
                self.combo.append_text("%s" % (i+1))
        self.set_label_widget(flab)
        self.combo.set_active(0)
        self.combo.connect("changed", self.FillIn, data)
        self.FillIn(None, data)

    def FillIn(self, dummy, data):
        idx = self.combo.get_active()
        v = self.var.Get(idx)
        children = self.get_children()
        for child in children:
            if child != self.get_label_widget():
                self.remove(child)
        assert isinstance(v.typ, model.Struct)
        self.add(MakeStructWidgetInternals(v, data))
        self.show_all()

def MakeSingleEntry(var, data, name):
    hb = gtk.HBox()
    lab = gtk.Label(name)
    lab.set_alignment(0, 0.5)
    hb.pack_start(lab)
    adj = gtk.Adjustment(data.Get(var.loc),
                         -120, 120,
                         1, 10, 0)
    entry = gtk.SpinButton(adj, 1.0, 0)
    entry.connect("changed", OnEntryChanged, None, var, data)
    hb.pack_end(entry, expand=False)
    return hb

def MakeSimpleArrayWidget(var, data, name):
    if var.typ.HaveNames():
        cnt = gtk.VBox()
        cnt.set_border_width(10)
    else:
        cnt = gtk.HBox()
        lab = gtk.Label(name + " ")
        cnt.add(lab)
        lab.set_alignment(0, 0.5)
    for i in range(var.typ.GetLength()):
        if var.typ.HaveNames():
            wgt = MakeSingleEntry(var.Get(i), data, var.typ.GetName(i))
        else:
            wgt = MakeSingleEntry(var.Get(i), data, str(i))
        cnt.add(wgt)
    if var.typ.HaveNames():
        frame = gtk.Frame(name)
        frame.set_label_align(0.5, 0.5)
        frame.add(cnt)
        return frame
    else:
        return cnt

def MakeStructWidget(var, data, name):
    frame = gtk.Frame(name)
    frame.add(MakeStructWidgetInternals(var, data))
    return frame

def MakeStructWidgetInternals(var, data):
    vbox = gtk.VBox()
    if var.typ.WantsHorizontalLayout():
        vbox = gtk.HBox()
    vbox.set_border_width(10)
    for name in var.typ.GetNames():
        v = var.Get(name)
        vbox.add(MakeWidget(v, data, name))
    return vbox

def MakeWidget(var, data, name):
    if isinstance(var.typ, model.Value):
        return MakeSingleEntry(var, data, name)
    elif isinstance(var.typ, model.Struct):
        return MakeStructWidget(var, data, name)
    elif isinstance(var.typ, model.Array):
        if isinstance(var.typ.GetType(), model.Value):
            return MakeSimpleArrayWidget(var, data, name)
        else:
            return ComplexArrayWidget(var, data, name)
    else:
        raise RuntimeError("Unknown type in MakeWidget")

def OnEntryChanged(entry, event, var, data):
    try:
        val = int(entry.get_text())
        data.Set(var.loc, val)
    except ValueError:
        pass

class ChannelGauge(gtk.VBox):
    def __init__(self, text):
        gtk.VBox.__init__(self)
        self.label = gtk.Label(text)
        self.label.set_alignment(0, 0.5)
        self.bar = gtk.ProgressBar()
        self.bar.set_pulse_step(0)
        self.pack_start(self.label, expand=False)
        self.pack_start(self.bar, expand=False)

    def Set(self, val):
        self.bar.set_fraction((val - 3000) / 2400.0 + 0.5)

class Channels(gtk.Frame):
    def __init__(self, n):
        gtk.Frame.__init__(self, "Output")
        vbox = gtk.VBox()
        self.chans = []
        for i in range(n):
            ch = ChannelGauge("CH " + str(i+1))
            vbox.pack_start(ch, expand=False)
            self.chans.append(ch)
        self.add(vbox)
        self.n = n

    def Set(self, arr):
        for i in range(self.n):
            if i < len(arr):
                self.chans[i].Set(arr[i])
            else:
                self.chans[i].Set(2000)
