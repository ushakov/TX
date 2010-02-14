import gtk
from google.protobuf import text_format

import model
import ser
import vis
import proto
import config

tx = ser.TXComm()
data = tx.GetData()
assert len(data.array) == model.model.typ.GetSize()

current_fname = ""

def DoLoad(button):
    fsd = gtk.FileChooserDialog("Select a file to load",
                                None,
                                gtk.FILE_CHOOSER_ACTION_OPEN,
                                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                 gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    global current_fname
    if current_fname:
        fsd.set_current_name(current_fname)

    filt = gtk.FileFilter()
    filt.set_name("Config files (*.cfg)")
    filt.add_pattern("*.cfg")
    fsd.add_filter(filt)

    filt = gtk.FileFilter()
    filt.set_name("All files")
    filt.add_pattern("*")
    fsd.add_filter(filt)

    response = fsd.run()
    if response == gtk.RESPONSE_OK:
        global data
        data = config.Load(model.model, fsd.get_filename())
        current_fname = fsd.get_filename()
    fsd.destroy()

def DoSave(button):
    fsd = gtk.FileChooserDialog("Select a file to save",
                                None,
                                gtk.FILE_CHOOSER_ACTION_SAVE,
                                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                 gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    global current_fname
    if not current_fname:
        fsd.set_current_name("model.cfg")
    else:
        fsd.set_current_name(current_fname)

    filt = gtk.FileFilter()
    filt.set_name("Config files (*.cfg)")
    filt.add_pattern("*.cfg")
    fsd.add_filter(filt)

    filt = gtk.FileFilter()
    filt.set_name("All files")
    filt.add_pattern("*")
    fsd.add_filter(filt)

    response = fsd.run()
    if response == gtk.RESPONSE_OK:
        config.Save(model.model, data, fsd.get_filename())
        current_fname = fsd.get_filename()
    fsd.destroy()

def DoCalibrate(button):
    tx.Send("C")

def DoReset(button):
    tx.Send("R R R")



loop = True
def StopLoop(unused):
    global loop
    loop = False

def main():
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

    w.connect("destroy", StopLoop)

    global loop
    while loop:
        gtk.main_iteration(False)
        r = tx.Check()
        if r and r[0] == '>':
            vals = [int(t) for t in r[2:].split()]
            chans.Set(vals)

        
if __name__ == "__main__":
    main()

