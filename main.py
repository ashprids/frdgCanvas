print("""
# frdgCanvas - A simple bitmap drawing program created with Pygame and GTK 3.0
# Made by fridge (https://fridg3.org)
# Created on 10/07/2024\n""")

import gi, pygame, setproctitle, threading, sys, os
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from pathlib import Path
from screeninfo import get_monitors

setproctitle.setproctitle("frdgCanvas")
clock = pygame.time.Clock()

# Fetches the current resource path, allowing for relative file paths to work
# both when running in Python and as an executable. Call this function with a file path
# if the file is expected to be compiled with the executable.
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)



# Canvas window
class Canvas:
    def __init__(self, name, width, height, bg_r, bg_g, bg_b, fullscreen, gridMode, gridSize, grid_r, grid_g, grid_b):
        pygame.init()

        self.screen_width = width
        self.screen_height = height
        self.project_name = name
        self.pixel_size = gridSize
        self.pen_size = 4
        
        self.bgcolour = (bg_r, bg_g, bg_b)
        self.pencolour = (40, 40, 40)
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption('frdgCanvas - ' + self.project_name + '.png')
        pygame.display.set_icon(pygame.image.load(get_resource_path('assets/icon.png')))
        
        self.canvas_width = self.screen_width // self.pixel_size
        self.canvas_height = self.screen_height // self.pixel_size
        self.canvas = [[self.bgcolour for _ in range(self.canvas_width)] for _ in range(self.canvas_height)]

        self.gridVisible = False
        self.gridcolour = (grid_r, grid_g, grid_b)
        self.grid_mode = gridMode
        if self.grid_mode:
            self.pen_size = self.pixel_size
            global optionsWindow
        optionsWindow.penSize.set_value(self.pen_size)
        
        self.drawing = False
        self.last_pos = None 

    def draw_grid(self):
        for x in range(0, self.screen_width, self.pixel_size):
            pygame.draw.line(self.screen, self.gridcolour, (x, 0), (x, self.screen_height))
        for y in range(0, self.screen_height, self.pixel_size):
            pygame.draw.line(self.screen, self.gridcolour, (0, y), (self.screen_width, y))

    def draw_canvas(self):
        for y in range(self.canvas_height):
            for x in range(self.canvas_width):
                color = self.canvas[y][x]
                pygame.draw.rect(self.screen, color, (x * self.pixel_size, y * self.pixel_size, self.pixel_size, self.pixel_size))

    def handle_events(self):
        global optionsWindow
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                optionsWindow.main_window.destroy()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.drawing = True
                    self.last_pos = event.pos
                    if not self.grid_mode:
                        self.draw_pen(event.pos)
                    else:
                        self.draw_pixel(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    self.drawing = False
                    self.last_pos = None
            elif event.type == pygame.MOUSEMOTION:
                if self.drawing:
                    if not self.grid_mode:
                        self.draw_pen(event.pos)
                    else:
                        self.draw_pixel(event.pos)

    
    def draw_pixel(self, position):
        mouse_x, mouse_y = position
        grid_x = mouse_x // self.pixel_size
        grid_y = mouse_y // self.pixel_size
        if 0 <= grid_x < self.canvas_width and 0 <= grid_y < self.canvas_height:
            self.canvas[grid_y][grid_x] = self.pencolour

    def draw_pen(self, position):
        # TODO: Custom brushes
        pygame.draw.circle(self.screen, self.pencolour, position, self.pen_size // 2)
        if self.last_pos:
            pygame.draw.line(self.screen, self.pencolour, self.last_pos, position, self.pen_size * 2)
        self.last_pos = position

    def clear_canvas(self):
        self.canvas = [[self.bgcolour for _ in range(self.canvas_width)] for _ in range(self.canvas_height)]
        self.screen.fill(self.bgcolour)

    def run(self):
        self.screen.fill(self.bgcolour)
        global canvasRunning
        while canvasRunning:
            if self.grid_mode:
                self.draw_canvas()
                if self.gridVisible:
                    self.draw_grid()
            self.handle_events()
            pygame.display.flip()
            pygame.display.update()
            clock.tick(60)
        pygame.quit()
        global optionsWindow
        optionsWindow.main_window.destroy()
        sys.exit()


class Options:
    def __init__(self, fullscreen):
        # Load the Glade file
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource_path("gtk/options.xml"))

        # Get the main window and connect the destroy signal
        self.main_window = self.builder.get_object("optionsWindow")
        if not self.main_window:
            print("Could not find optionsWindow in the Glade file.")
            return
        self.main_window.connect("destroy", Gtk.main_quit)

        if fullscreen:
            self.main_window.set_keep_above(True)

        # Get widgets
        self.penColour = self.builder.get_object("penColour")
        self.penSize = self.builder.get_object("penSize")
        self.brushSelect = self.builder.get_object("brushSelect")
        self.togglegrid = self.builder.get_object("hideGrid")
        self.clear = self.builder.get_object("clear")
        self.apply = self.builder.get_object("apply")
        self.close = self.builder.get_object("close")
        self.export = self.builder.get_object("export")

        # Check if widgets are found
        if not all([self.penColour, self.penSize, self.brushSelect, self.togglegrid, self.clear, self.close, self.export]):
            print("One or more widgets not found in options.xml. Options window will not work.")
            return
        
        brushes = Gtk.ListStore(str)
        # TODO: Automatically load brushes from a directory
        brushes.append(["Option 1"])
        brushes.append(["Option 2"])
        brushes.append(["Option 3"])

        self.brushSelect.set_model(brushes)
        renderer_text = Gtk.CellRendererText()
        self.brushSelect.pack_start(renderer_text, True)
        self.brushSelect.add_attribute(renderer_text, "text", 0)


        # Connect signals
        self.main_window.connect("delete-event", self.on_delete_event)
        self.penColour.connect("notify::rgba", self.on_pen_colour_changed)
        self.penSize.connect("value-changed", self.on_pen_size_changed)
        self.brushSelect.connect("changed", self.on_brush_changed)
        self.togglegrid.connect("clicked", self.on_togglegrid_clicked)
        self.clear.connect("clicked", self.on_clear_clicked)
        self.close.connect("clicked", self.on_close_clicked)
        self.export.connect("clicked", self.on_export_clicked)
        

    def show_confirm_dialog(self):
        dialog = Gtk.MessageDialog(
            parent=self.main_window,
            modal=True,
            type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            message_format="Closing the options menu will also close the canvas. Do you really want to exit?"
        )
        dialog.set_title("Exit Confirmation")
        response = dialog.run()
        dialog.destroy()
        return response
    
    def on_delete_event(self, widget, event):
        response = self.show_confirm_dialog()
        if response == Gtk.ResponseType.YES:
            self.main_window.destroy()
            print("Close button pressed - exiting")
            global canvasRunning
            canvasRunning = False
            sys.exit()
        else:
            print("Close canceled")
            return True

    def on_close_clicked(self, widget):
        self.show_confirm_dialog()
        print("Close button pressed - exiting")

    def on_pen_colour_changed(self, widget, param):
        rgba = widget.get_rgba()
        pencolour = (int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255))
        
        global canvasWindow
        canvasWindow.pencolour = pencolour

    def on_pen_size_changed(self, widget):
        newSize = widget.get_value_as_int()
        global canvasWindow
        canvasWindow.pen_size = newSize

    def on_brush_changed(self, widget):
        model = widget.get_model()
        index = widget.get_active()
        if index >= 0:
            text = model[index][0]
            print(f"Selected: {text}")

    def on_togglegrid_clicked(self, widget):
        global canvasWindow
        canvasWindow.gridVisible = not canvasWindow.gridVisible
        print(f"Grid visibility toggled: {canvasWindow.gridVisible}")

    def on_clear_clicked(self, widget):
        global canvasWindow
        canvasWindow.clear_canvas()
        print("Canvas cleared")

    def on_close_clicked(self, widget):
        self.main_window.destroy()
        print("Close button pressed - exiting")
        global canvasRunning
        canvasRunning = False
        sys.exit()
    
    def on_export_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Save File",
            parent=self.main_window,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE,
            Gtk.ResponseType.OK
        )

        # Add filters for file types here if necessary
        filter_png = Gtk.FileFilter()
        filter_png.set_name("PNG files")
        filter_png.add_mime_type("image/png")
        dialog.add_filter(filter_png)

        global canvasWindow
        dialog.set_current_name(canvasWindow.project_name + ".png")
        pictures_path = str(Path.home() / "Pictures")
        dialog.set_current_folder(pictures_path)

        # Show the dialog and wait for a response
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print(f"File exported as: {dialog.get_filename()}")
            pygame.image.save(canvasWindow.screen,dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            print("File export aborted")
        dialog.destroy()

# Window that renders whenever the executable is run and prompts the user to create a new project
class Setup:
    def __init__(self):
        # Load the Glade file
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource_path("gtk/setup.xml"))

        # Get the main window and connect the destroy signal
        self.main_window = self.builder.get_object("setupWindow")
        if not self.main_window:
            print("Could not find setupWindow in the XML file.")
            return
        self.main_window.connect("destroy", Gtk.main_quit)

        # Get widgets
        self.name_entry = self.builder.get_object("projectName")
        self.width_entry = self.builder.get_object("windowWidth")
        self.height_entry = self.builder.get_object("windowHeight")
        self.bgColour = self.builder.get_object("backgroundColour")
        self.fullscreen = self.builder.get_object("fullscreen")
        self.submit_button = self.builder.get_object("createCanvas")
        self.close_button = self.builder.get_object("close")

        self.grid_button = self.builder.get_object("gridMode")
        self.gridColour = self.builder.get_object("gridColour")
        self.pixel_size = self.builder.get_object("pixelSize")

        # Check if widgets are found
        if not all([self.name_entry, self.width_entry, self.height_entry, self.bgColour, self.grid_button, self.submit_button, self.close_button, self.gridColour, self.pixel_size, self.fullscreen]):
            print("One or more widgets not found in the XML file. Closing.")
            return

        # Connect signals
        self.submit_button.connect("clicked", self.on_submit_clicked)
        self.close_button.connect("clicked", self.on_close_clicked)

    def on_close_clicked(self, widget):
        self.main_window.destroy()
        sys.exit()

    def invalid_input(self):
        dialog = Gtk.MessageDialog(
            parent=self.main_window,
            modal=True,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            message_format="Invalid input provided.\nMake sure the project name only contains alphanumeric characters, and the width and height are numbers."
        )
        dialog.set_title("Error")
        response = dialog.run()
        dialog.destroy()
        return response

    def on_submit_clicked(self, widget):
        name = self.name_entry.get_text()
        width = self.width_entry.get_text()
        height = self.height_entry.get_text()
        bgColour = self.bgColour.get_rgba()
        fullscreen = self.fullscreen.get_active()

        if fullscreen:
            for monitor in get_monitors():
                if monitor.is_primary:
                    width = str(monitor.width)
                    height = str(monitor.height)

        gridMode = self.grid_button.get_active()
        pixelSize = self.pixel_size.get_text()
        gridColour = self.gridColour.get_rgba()

        if name.isalnum() and width.isdigit() and height.isdigit():
            self.main_window.destroy()
            while Gtk.events_pending():
                Gtk.main_iteration()
            print(f"Creating project '{name}'")
            def startCanvas():
                global canvasWindow
                # *breathe in*
                canvasWindow = Canvas(name, int(width), int(height), int(bgColour.red * 255), int(bgColour.green * 255), int(bgColour.blue * 255), bool(fullscreen), bool(gridMode), int(pixelSize), int(gridColour.red * 255), int(gridColour.green * 255), int(gridColour.blue * 255))
                # *breathe out*
                canvasWindow.run()

            global canvasRunning
            canvasRunning = True
            canvasThread = threading.Thread(target=startCanvas)
            canvasThread.start()
            print("Canvas thread started")

            global optionsWindow
            optionsWindow = Options(fullscreen)
            print("Options window started")
            if optionsWindow.main_window:
                optionsWindow.main_window.show_all()
                Gtk.main()

        else:
            print("Error: Invalid input provided for project creation")
            self.invalid_input()



# --// Runtime //-- #
if __name__ == "__main__":
    setupWindow = Setup()
    print("Setup window started")
    if setupWindow.main_window:
        setupWindow.main_window.show_all()
        Gtk.main()
