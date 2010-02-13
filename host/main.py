import gtk
from google.protobuf import text_format

import model
import ser
import vis
import proto

tx = ser.TXComm()
data = tx.GetData()
assert len(data.array) == model.model.typ.GetSize()

def DoLoad(button):
    pass

def DoSave(button):
    pass

def DoCalibrate(button):
    tx.Send("C")

def DoReset(button):
    tx.Send("R R R")



w = gtk.Window()
h = gtk.HBox()
w.add(h)
chans = vis.Channels(6)
h.add(chans)
h.add(vis.MakeWidget(model.model, data, 'Model'))
bbf = gtk.Frame("Actions")
bb = gtk.VBox()
bbf.add(bb)
h.add(bbf)
l = gtk.Button("Load")
s = gtk.Button("Save")
c = gtk.Button("Calibrate")
r = gtk.Button("Reset")
l.connect("clicked", DoLoad)
s.connect("clicked", DoSave)
c.connect("clicked", DoCalibrate)
r.connect("clicked", DoReset)
bb.pack_start(l, expand=False)
bb.pack_start(s, expand=False)
bb.pack_start(c, expand=False)
bb.pack_start(r, expand=False)
w.show_all()

loop = True
def StopLoop(unused):
    global loop
    loop = False

w.connect("destroy", StopLoop)

while loop:
    gtk.main_iteration(False)
    r = tx.Check()
    if r and r[0] == '>':
        vals = [int(t) for t in r[2:].split()]
        chans.Set(vals)

        
    
