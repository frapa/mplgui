import webbrowser
import os

from gi.repository import Gtk, Gdk

import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt

# Colors
COLORS = [tuple(map(lambda x: x/255.0, c)) for c in ((39,99,236), (166,16,16), (20,118,4), (255,210,0),
    (163,10,219), (5,181,138), (130,70,0), (255,108,0), (255,0,72))]
GDK_COLORS = [Gdk.RGBA(*c) for c in COLORS]

# Plot types
SERIES = 1
ALL_VS_FIRST = 2

PLOT_PANELS = {SERIES: "series", ALL_VS_FIRST: "all_vs_first"}

class MPL:
    def __init__(self, builder, variables):
        self.variables = variables
        self.builder = builder

        # Create and fill model with data
        self.update_data_model()

        # Setup data view
        self.list = self.builder.get_object("list")
        self.list.set_model(self.data)
        self.update_data_view()

        # Notebook
        self.notebook = builder.get_object("notebook")

        self.plot_num = 0
        self.plots = {}
        self.pages = {}
        self.current_plot = None

        # Toolbar
        self.toolbar = builder.get_object("toolbar")

        new_plot = Gtk.ToolButton.new_from_stock(Gtk.STOCK_NEW)
        new_plot.connect("clicked", self.create_new_plot)
        self.toolbar.insert(new_plot, 0)

        # Figure
        self.f = plt.figure()

        # Window
        self.win = builder.get_object("window")

    def update_data_model(self):
        print([type(v[0]) for k, v in self.variables.items()])
        self.data = Gtk.ListStore(*[type(v[0]) for k, v in self.variables.items()])
        
        for vs in zip(*self.variables.values()):
            self.data.append(vs)

    def update_data_view(self):
        for n, (k, v) in enumerate(self.variables.items()):
            column = Gtk.TreeViewColumn(k, Gtk.CellRendererText(), text=n)
            column.set_min_width(120)
            column.set_resizable(True)
            column.set_reorderable(True)

            column.connect("clicked", self.on_column_clicked)

            self.list.append_column(column)

    def change_panel(self, t, plot):
        new_panel = PLOT_PANELS[t]

        # panel for option
        builder = Gtk.Builder()
        builder.add_from_file("{}.glade".format(new_panel)) 
        builder.connect_signals(self)

        plot["data_box"] = builder.get_object("data_box")

        panel = builder.get_object("panel")

        # Add data fields
        for n, k in enumerate(self.variables.keys()):
            self.add_var(plot, k, n)

        # Settings specific to the type of panel choosen
        getattr(self, "change_to_" + PLOT_PANELS[t])(plot, builder, t)

        # Add some references
        plot["title_entry"] = builder.get_object("title_entry")
        plot["x_entry"] = builder.get_object("x_entry")
        plot["y_entry"] = builder.get_object("y_entry")

        return panel

    def create_new_plot(self, button, plot_type=SERIES):
        # NON-GUI
        self.plot_num += 1
        self.plots[self.plot_num] = {
            "type": 1,
            "variables": []
        }
        plot = self.plots[self.plot_num]

        # GUI
        paned = Gtk.Paned()
        label = Gtk.Label("Plot {}".format(self.plot_num))

        # Left panel
        box = Gtk.VBox()
        plot["panel_box"] = box
        box.set_homogeneous(False)
        box.set_margin_left(4)
        box.set_margin_right(4)
        box.set_margin_top(4)
        box.set_margin_bottom(4)
        box.set_size_request(240, 100)

        # Plot type
        box_plot_type = Gtk.VBox()
        box_plot_type.set_homogeneous(False)

        label_type = Gtk.Label("Plot type")
        box_plot_type.pack_start(label_type, False, False, 0)

        button_series = Gtk.RadioButton.new_with_label_from_widget(None, "Series")
        button_series.connect("toggled", self.on_plot_type_changed, plot, SERIES)
        button_series.set_visible(True)
        box_plot_type.pack_start(button_series, False, False, 0)
        
        button_all_vs_first = Gtk.RadioButton.new_with_label_from_widget(button_series, "All vs first")
        button_all_vs_first.connect("toggled", self.on_plot_type_changed, plot, ALL_VS_FIRST)
        button_all_vs_first.set_visible(True)
        box_plot_type.pack_start(button_all_vs_first, False, False, 0)

        box_plot_type.set_visible(True)
        box.pack_start(box_plot_type, False, False, 0)        

        # Panel
        panel = self.change_panel(plot_type, plot)
        plot["panel"] = panel
        box.pack_start(panel, True, True, 4)        

        plot_button = Gtk.Button("Plot")
        plot_button.connect("clicked", self.plot, plot)
        plot_button.set_visible(True)
        box.pack_start(plot_button, False, False, 0)

        paned.add1(box)

        # Right Panel
        image = Gtk.Image()
        image.set_visible(True)

        plot["image"] = image

        paned.add2(image)

        box.set_visible(True)
        paned.set_visible(True)

        i = self.notebook.append_page(paned, label)
        self.pages[paned] = self.plot_num
        self.notebook.set_current_page(i)

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
            filename = dialog.get_filename()

            if dialog.get_filter() == filter_text:
                builder = Gtk.Builder()
                builder.add_from_file("text_import.glade") 
                builder.connect_signals(self)
                
                import_dialog = builder.get_object("window")
                import_dialog.show_all()

                sep_entry = builder.get_object("sep_entry")
                head_entry = builder.get_object("head_entry")
                foot_entry = builder.get_object("foot_entry")

                ok = builder.get_object("ok")
                ok.connect("clicked", self.on_text_import_ok,
                    import_dialog, filename, sep_entry, head_entry, foot_entry)
        
        dialog.destroy()

    def menu_file_save_as(self, *args):
        if len(self.plots) == 0:
            dialog = Gtk.MessageDialog(self.win, 0, Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK, "No plot selected.")
            dialog.run()

            dialog.destroy()
        else:
            dialog = Gtk.FileChooserDialog("Save as ...", None,
                Gtk.FileChooserAction.SAVE,
                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.OK))

            filter_pdf = Gtk.FileFilter()
            filter_pdf.set_name("PDF")
            filter_pdf.add_mime_type("application/pdf")
            dialog.add_filter(filter_pdf)
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                filename = dialog.get_filename()

                if dialog.get_filter().get_name() == "PDF":
                    name, ext = os.path.splitext(filename)
                    if not ext or ext != ".pdf":
                        filename += ".pdf"

                if os.path.exists(filename):
                    ask = Gtk.MessageDialog(self.win, 0, Gtk.MessageType.QUESTION,
                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                        Gtk.STOCK_SAVE, Gtk.ResponseType.OK),
                        "A file named '{}' already exists. Do you want to replace it?".format(os.path.basename(filename)))
                    ask.format_secondary_text("Replacing will overwrite its content.")

                    response = ask.run()
                    if response == Gtk.ResponseType.CANCEL:
                        ask.destroy()
                        dialog.destroy()
                        return None

                    ask.destroy()

                self.plot(None, self.plots[self.current_plot])
                self.f.savefig(filename)
                                
            dialog.destroy()

    def menu_plot_code(self):
        pass

    def on_text_import_cancel(self, button, dialog):
        dialog.close()

    def on_text_import_ok(self, button, dialog, fname, sep_entry, head_entry, foot_entry):
        sep = sep_entry.get_text()
        headlines = int(head_entry.get_text())
        footlines = int(foot_entry.get_text())

        data = np.genfromtxt(fname, delimiter=sep, skip_header=headlines,
            skip_footer=footlines)

        for n, col in enumerate(data[1,:]):
            self.variables["dat{}".format(n)] = tuple(map(float, data[:,n])) 

        self.update_data_model()
        self.update_data_view()

        dialog.close()

    def on_var_deleted(self, button, field, plot, v):
        field.destroy()
        plot["variables"].remove(v)

    def on_var_add(self, button):
        plot = self.plots[self.current_plot]
        self.add_var(plot, list(self.variables.keys())[0])

    def add_var(self, plot, key, active=0):
        n = len(plot["variables"])

        color = COLORS[n % len(COLORS)]
        gdk_color = GDK_COLORS[n % len(COLORS)]

        var = {"key": key, "color": color, "gdk_color": gdk_color}
        
        builder = Gtk.Builder()
        builder.add_from_file("data.glade") 
        builder.connect_signals(self)

        field = builder.get_object("data_field")
        plot["data_box"].pack_start(field, False, False, 8)

        var_label = builder.get_object("label")
        var_label.set_text("Series {}".format(n+1))

        color_button = builder.get_object("color_button")
        color_button.set_rgba(gdk_color)

        color_button = builder.get_object("delete_button")
        color_button.connect("clicked", self.on_var_deleted, field, plot, var)

        combo = builder.get_object("combo")
        combo.set_entry_text_column(0)
        combo.connect("changed", self.on_var_combo_changed, var)

        for key in self.variables.keys():
            combo.append_text(key)

        combo.set_active(active)

        plot["variables"].append(var)

    def on_var_combo_changed(self, combo, var):
        string = combo.get_active_text()
        var["key"] = string

    def on_column_clicked(self, column, *args):
        print("ciao")

    def on_plot_type_changed(self, button, plot, t):
        plot["panel"].destroy()

        plot["variables"] = []

        panel = self.change_panel(t, plot)
        plot["panel"] = panel

        plot["panel_box"].pack_start(panel, True, True, 4)        
        plot["panel_box"].reorder_child(panel, 1)

        plot["type"] = t

    def change_to_series(self, plot, builder, t):
        pass
    
    def change_to_all_vs_first(self, plot, builder, t):
        variabs = list(self.variables.keys())
        plot["first"] = variabs[0]

        abscissa = builder.get_object("abscissa_combo")
        abscissa.connect("changed", self.on_change_absissa, plot)

        for key in variabs:
            abscissa.append_text(key)

        abscissa.set_active(0)

    def on_change_absissa(self, combo, plot):
        string = combo.get_active_text()
        plot["first"] = string

    def on_switch_plot(self, notebook, page, page_num):
        try:
            self.current_plot = self.pages[page]
        except:
            # Sometimes one selects the "Data" tab!!!
            pass

    def plot(self, button, plot):
        plot["code"] = "f = plt.figure()\nax = f.add_subplot(111)\n\n"

        self.f.clf()
        ax = self.f.add_subplot(111)

        t = plot["type"]   
        if t == SERIES: 
            for v in plot["variables"]:
                values = self.variables[v["key"]]
                color = v["color"]

                ax.errorbar(x=np.arange(len(values)), y=values,
                    c=color)
        elif t == ALL_VS_FIRST:
            first = plot["first"]
            for v in plot["variables"]:
                values = self.variables[v["key"]]
                color = v["color"]

                ax.errorbar(x=self.variables[first],
                    y=values, c=color)

        # Title and labels stuff
        title = plot["title_entry"].get_text()
        x_label = plot["x_entry"].get_text()
        y_label = plot["y_entry"].get_text()

        self.f.suptitle(title)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        plot["code"] += ("f.suptitle('{title}')\nax.set_xlabel('{x}')\n"
            "ax.set_ylabel('{y}')\n\n").format(title=title,
            x=x_label, y=y_label)

        self.f.savefig("i.png")
        plot["image"].set_from_file("i.png")

        return self.f

    def on_report_bug(self, *args):
        webbrowser.open_new_tab("https://github.com/frapa/mplgui/issues")

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
