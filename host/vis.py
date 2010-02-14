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
        self.add(StructWidgetInternals(v, data))
        self.show_all()

    def SetNewData(self, data):
        self.data = data
        self.FillIn(None, data)

gobject.type_register(ComplexArrayWidget)

class SingleEntry(gtk.HBox):
    def __init__(self, var, data, name):
        gtk.HBox.__init__(self)
        lab = gtk.Label(name)
        lab.set_alignment(0, 0.5)
        self.pack_start(lab)
        adj = gtk.Adjustment(data.Get(var.loc),
                             -120, 120,
                             1, 10, 0)
        self.entry = gtk.SpinButton(adj, 1.0, 0)
        self.entry.connect("changed", self.OnEntryChanged)
        self.pack_end(self.entry, expand=False)
        self.var = var
        self.data = data

    def OnEntryChanged(self, entry):
        try:
            val = int(self.entry.get_text())
            self.data.Set(self.var.loc, val)
        except ValueError:
            pass

    def SetNewData(self, data):
        self.data = data
        self.entry.set_value(data.Get(self.var.loc))

gobject.type_register(SingleEntry)

class SimpleArrayWidget(gtk.VBox):
    def __init__(self, var, data, name):
        gtk.VBox.__init__(self)
        self.var = var
        self.data = data
        self.data_widgets = []
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
                wgt = SingleEntry(var.Get(i), data, var.typ.GetName(i))
            else:
                wgt = SingleEntry(var.Get(i), data, str(i))
            cnt.add(wgt)
            self.data_widgets.append(wgt)
        if var.typ.HaveNames():
            frame = gtk.Frame(name)
            frame.set_label_align(0.5, 0.5)
            frame.add(cnt)
            self.add(frame)
        else:
            self.add(cnt)

    def SetNewData(self, data):
        self.data = data
        for w in self.data_widgets:
            w.SetNewData(data)

gobject.type_register(SimpleArrayWidget)

class StructWidget(gtk.Frame):
    def __init__(self, var, data, name):
        gtk.Frame.__init__(self, name)
        self.internals = StructWidgetInternals(var, data)
        self.add(self.internals)

    def SetNewData(self, data):
        self.internals.SetNewData(data)

gobject.type_register(StructWidget)

class StructWidgetInternals(gtk.VBox):
    def __init__(self, var, data):
        gtk.VBox.__init__(self)
        if var.typ.WantsHorizontalLayout():
            box = gtk.HBox()
        else:
            box = gtk.VBox()
        box.set_border_width(10)
        self.data_widgets = {}
        for name in var.typ.GetNames():
            v = var.Get(name)
            wgt = MakeWidget(v, data, name)
            self.data_widgets[name] = wgt
            box.add(wgt)
        self.add(box)
        self.var = var
        self.data = data

    def SetNewData(self, data):
        self.data = data
        for name in self.var.typ.GetNames():
            w = self.data_widgets[name]
            w.SetNewData(data)

gobject.type_register(StructWidgetInternals)

def MakeWidget(var, data, name):
    if isinstance(var.typ, model.Value):
        return SingleEntry(var, data, name)
    elif isinstance(var.typ, model.Struct):
        return StructWidget(var, data, name)
    elif isinstance(var.typ, model.Array):
        if isinstance(var.typ.GetType(), model.Value):
            return SimpleArrayWidget(var, data, name)
        else:
            return ComplexArrayWidget(var, data, name)
    else:
        raise RuntimeError("Unknown type in MakeWidget")

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
