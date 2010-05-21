#!/usr/bin/python
import gtk
from google.protobuf import text_format

import model
import ser
import vis
import proto
import config

class MainUI(object):
    def __init__(self):
        self.tx = ser.TXComm()
        self.data = self.tx.GetData()
        self.var = model.model
        if self.tx:
            self.data = self.tx.GetData()
        else:
            self.data = ser.Data(None)
            self.data.array = [0] * self.var.typ.GetSize()
        self.continue_running = True
        self.current_fname = ""
        assert len(self.data.array) == self.var.typ.GetSize()

    def StopLoop(self, dummy):
        self.continue_running = False

    def InitUI(self):
        w = gtk.Window()
        h = gtk.HBox()
        w.add(h)
        self.chans = vis.Channels(model.NUM_CHANS)
        h.add(self.chans)
        self.wgt = vis.MakeWidget(self.var, self.data, 'Model')
        h.add(self.wgt)
        bbf = gtk.Frame("Actions")
        bb = gtk.VBox()
        bbf.add(bb)
        h.add(bbf)
        l = gtk.Button("Load")
        s = gtk.Button("Save")
        #cc = gtk.Button("Connect")
        c = gtk.Button("Calibrate")
        r = gtk.Button("Reset")
        l.connect("clicked", self.DoLoad)
        s.connect("clicked", self.DoSave)
        #cc.connect("clicked", self.DoConnect)
        c.connect("clicked", self.DoCalibrate)
        r.connect("clicked", self.DoReset)
        bb.pack_start(l, expand=False)
        bb.pack_start(s, expand=False)
        #bb.pack_start(cc, expand=False)
        bb.pack_start(c, expand=False)
        bb.pack_start(r, expand=False)
        w.show_all()
        w.connect("destroy", self.StopLoop)

    def Run(self):
        while self.continue_running:
            gtk.main_iteration(False)
            if self.tx:
                r = self.tx.Check()
                if r and r[0] == '>':
                    vals = [int(t) for t in r[2:].split()]
                    self.chans.Set(vals)
            else:
                vals = [2000 + 300*t for t in range(6)]
                self.chans.Set(vals)

    def AddFilters(self, fsd):
        filt = gtk.FileFilter()
        filt.set_name("Config files (*.cfg)")
        filt.add_pattern("*.cfg")
        fsd.add_filter(filt)

        filt = gtk.FileFilter()
        filt.set_name("All files")
        filt.add_pattern("*")
        fsd.add_filter(filt)

    def DoLoad(self, button):
        fsd = gtk.FileChooserDialog("Select a file to load",
                                    None,
                                    gtk.FILE_CHOOSER_ACTION_OPEN,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                     gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        if self.current_fname:
            fsd.set_current_name(self.current_fname)

        self.AddFilters(fsd)

        response = fsd.run()
        if response == gtk.RESPONSE_OK:
            self.data = config.Load(self.var, self.data, fsd.get_filename())
            self.data.comm = self.tx
            self.wgt.SetNewData(self.data)
            current_fname = fsd.get_filename()
        fsd.destroy()

    def DoSave(self, button):
        fsd = gtk.FileChooserDialog("Select a file to save",
                                    None,
                                    gtk.FILE_CHOOSER_ACTION_SAVE,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                     gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        if not self.current_fname:
            fsd.set_current_name("model.cfg")
        else:
            fsd.set_current_name(self.current_fname)

        self.AddFilters(fsd)

        response = fsd.run()
        if response == gtk.RESPONSE_OK:
            config.Save(self.var, self.data, fsd.get_filename())
            self.current_fname = fsd.get_filename()
        fsd.destroy()

    def DoCalibrate(self, button):
        if self.tx:
            self.tx.Send("C")

    def DoReset(self, button):
        if self.tx:
            self.tx.Reset()
            self.data = self.tx.GetData()
            self.wgt.SetNewData(self.data)


def main():
    ui = MainUI()
    ui.InitUI()
    ui.Run()
        
if __name__ == "__main__":
    main()

