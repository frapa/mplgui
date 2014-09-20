from gi.repository import Gtk

import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt

# Plot types
SERIES = 1
ALL_VS_FIRST = 2

class MPL:
    def __init__(self, builder, variables):
        self.variables = variables
        self.builder = builder

        # Create and fill model with data
        self.data = Gtk.ListStore(*[type(v[0]) for k, v in self.variables.items()])
        
        for vs in zip(*self.variables.values()):
            self.data.append(vs)

        # Setup data view
        self.list = self.builder.get_object("list")
        self.list.set_model(self.data)

        for n, (k, v) in enumerate(self.variables.items()):
            column = Gtk.TreeViewColumn(k, Gtk.CellRendererText(), text=n)
            column.set_min_width(120)
            column.set_resizable(True)
            column.set_reorderable(True)

            column.connect("clicked", self.on_column_clicked)

            self.list.append_column(column)

        # Notebook
        self.notebook = builder.get_object("notebook")

        self.plot_num = 0
        self.plots = {}

        # Toolbar
        self.toolbar = builder.get_object("toolbar")

        new_plot = Gtk.ToolButton.new_from_stock(Gtk.STOCK_NEW)
        new_plot.connect("clicked", self.create_new_plot)
        self.toolbar.insert(new_plot, 0)

    def create_new_plot(self, *args):
        # NON-GUI
        self.plot_num += 1
        self.plots[self.plot_num] = {
            "type": 1
        }
        plot = self.plots[self.plot_num]

        # GUI
        paned = Gtk.Paned()
        label = Gtk.Label("Plot {}".format(self.plot_num))

        # Left panel
        box = Gtk.VBox()
        box.set_homogeneous(False)
        box.set_margin_left(4)
        box.set_margin_right(4)
        box.set_margin_top(4)
        box.set_margin_bottom(4)
        box.set_size_request(240, 100)

        label_type = Gtk.Label("Plot type")
        box.pack_start(label_type, False, False, 0)

        button_series = Gtk.RadioButton.new_with_label_from_widget(None, "Series")
        button_series.connect("toggled", self.on_plot_type_changed, plot, SERIES)
        button_series.set_visible(True)
        box.pack_start(button_series, False, False, 0)
        
        button_all_vs_first = Gtk.RadioButton.new_with_label_from_widget(button_series, "All vs first")
        button_all_vs_first.connect("toggled", self.on_plot_type_changed, plot, ALL_VS_FIRST)
        button_all_vs_first.set_visible(True)
        box.pack_start(button_all_vs_first, False, False, 0)

        # panel for option
        builder = Gtk.Builder()
        builder.add_from_file("series.glade") 
        builder.connect_signals(self)

        plot["data_box"] = builder.get_object("data_box")

        panel = builder.get_object("panel")
        box.pack_start(panel, True, True, 4)

        plot_button = Gtk.Button("Plot")
        plot_button.connect("clicked", self.plot, plot)
        plot_button.set_visible(True)
        box.pack_start(plot_button, False, False, 0)

        # Add data fields
        for k, v in self.variables.items():
            builder = Gtk.Builder()
            builder.add_from_file("data.glade") 
            builder.connect_signals(self)

            field = builder.get_object("data_field")
            plot["data_box"].pack_start(field, False, False, 8)

            var_label = builder.get_object("label")
            var_label.set_text(k)

        paned.add1(box)

        # Right Panel
        image = Gtk.Image()
        image.set_visible(True)

        plot["image"] = image

        paned.add2(image)

        box.set_visible(True)
        paned.set_visible(True)

        self.notebook.append_page(paned, label)

    def menu_file_open(self, *args):
        dialog = Gtk.FileChooserDialog("Open file", None,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print(dialog.get_filename())
        
        dialog.destroy()

    def on_column_clicked(self, column, *args):
        print("ciao")

    def on_plot_type_changed(self, button, plot, t):
        plot["type"] = t     

    def plot(self, button, plot=None):
        f = plt.figure()
        ax = f.add_subplot(111)

        t = plot["type"]   
        if t == SERIES: 
            for v in self.variables.values():
                ax.errorbar(x=np.arange(len(v)), y=v)
        elif t == ALL_VS_FIRST:
            first = list(self.variables.keys())[0]
            for k, v in self.variables.items():
                if k != first:
                    ax.errorbar(x=self.variables[first], y=v)

        f.savefig("i.png")
        plot["image"].set_from_file("i.png")

    def on_window_delete(self, *args):
        Gtk.main_quit(*args)

def mplgui(variables=[]):
    builder = Gtk.Builder()
    builder.add_from_file("gui.glade") 
    builder.connect_signals(MPL(builder, variables))

    win = builder.get_object("window")
    win.show_all()

    Gtk.main()

if __name__ == "__main__":
    x = (0, 1, 2, 3, 4)
    y = (0, 1, 4, 9, 16)
    mplgui({"x":x, "y":y})
