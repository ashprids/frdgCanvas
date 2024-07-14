print("""
# frdgCanvas - A simple bitmap drawing program created with Pygame and GTK 3.0
# Made by fridge (https://fridg3.org)
# Created on 10/07/2024\n""")

import gi, pygame, setproctitle, threading, sys, os, platform, json, random, zipfile, shutil, subprocess, time
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from pathlib import Path
from screeninfo import get_monitors

setproctitle.setproctitle("frdgCanvas")

# Fetches the current resource path, allowing for relative file paths to work
# both when running in Python and as an executable. Call this function with a file path
# if the file is expected to be compiled with the executable.
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def setupProject():
    global setupWindow
    setupWindow = Setup()
    print("Setup window started")
    if setupWindow.main_window:
        setupWindow.main_window.show_all()
        Gtk.main()



# Canvas window
class Canvas:
    def __init__(self, name, width, height, bg_r, bg_g, bg_b, gridMode, gridSize, grid_r, grid_g, grid_b):
        pygame.init()

        self.screen_width = width
        self.screen_height = height
        self.project_name = name
        self.pixel_size = gridSize
        self.pen_size = 4
        
        self.bgcolour = (bg_r, bg_g, bg_b)
        self.pencolour = (40, 40, 40)

        self.pentexture = "Default"
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.screen.fill(self.bgcolour)
        pygame.display.set_caption('frdgCanvas - ' + self.project_name + '.png')
        pygame.display.set_icon(pygame.image.load(get_resource_path('assets/icon.png')))
        
        self.canvas_width = self.screen_width // self.pixel_size
        self.canvas_height = self.screen_height // self.pixel_size
        self.canvas = [[self.bgcolour for _ in range(self.canvas_width)] for _ in range(self.canvas_height)]

        self.gridVisible = False
        self.gridcolour = (grid_r, grid_g, grid_b)
        self.grid_mode = gridMode

        global optionsWindow
        if self.grid_mode:
            optionsWindow.penSize.set_value(1)
            optionsWindow.togglegrid.set_sensitive(True)
            optionsWindow.penSize.set_sensitive(False)
            optionsWindow.brushSelect.set_sensitive(False)
        else:
            optionsWindow.togglegrid.set_sensitive(False)
            optionsWindow.penSize.set_value(self.pen_size)
        
        self.drawing = False
        self.erasing = False
        self.last_pos = None 

        self.history = []
        self.snapshot()

    def snapshot(self):
        if not self.grid_mode:
            display_surface = self.screen.copy()
            self.history.append(display_surface)

    def undo(self):
        if not self.grid_mode:
            if len(self.history) > 1:
                self.history.pop()
                last_state = self.history[-1]
                self.screen.blit(last_state, (0, 0))
                pygame.display.flip()
                print("Undo operation successful")

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
                if event.button == 1:  # Pen
                    self.drawing = True
                    self.last_pos = event.pos
                    if not self.grid_mode:
                        self.draw_pen(event.pos, False)
                    else:
                        self.draw_pixel(event.pos, False)
                elif event.button == 3:  # Eraser
                    self.drawing = True
                    self.erasing = True
                    self.last_pos = event.pos
                    if not self.grid_mode:
                        self.draw_pen(event.pos, True)
                    else:
                        self.draw_pixel(event.pos, True)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Pen
                    self.drawing = False
                    self.last_pos = None
                if event.button == 3:  # Eraser
                    self.drawing = False
                    self.erasing = False
                    self.last_pos = None
                self.snapshot()
            elif event.type == pygame.MOUSEMOTION:
                if self.drawing:
                    if not self.grid_mode:
                        if self.erasing:
                            self.draw_pen(event.pos, True)
                        else:
                            self.draw_pen(event.pos, False)
                    else:
                        if self.erasing:
                            self.draw_pixel(event.pos, True)
                        else:
                            self.draw_pixel(event.pos, False)
            elif event.type == pygame.KEYDOWN:
                if event.mod & pygame.KMOD_CTRL and event.key == pygame.K_z:
                    self.undo()

    
    def draw_pixel(self, position, eraser):
        mouse_x, mouse_y = position
        grid_x = mouse_x // self.pixel_size
        grid_y = mouse_y // self.pixel_size
        if 0 <= grid_x < self.canvas_width and 0 <= grid_y < self.canvas_height:
            if eraser:
                self.canvas[grid_y][grid_x] = self.bgcolour
            else:
                self.canvas[grid_y][grid_x] = self.pencolour

    def draw_pen(self, position, eraser):
        if self.pentexture == "Default":
            if eraser:
                pygame.draw.rect(self.screen, self.bgcolour, (position[0], position[1], self.pen_size, self.pen_size))
                if self.last_pos:
                    pygame.draw.line(self.screen, self.bgcolour, self.last_pos, position, self.pen_size * 2)
                self.last_pos = position
            else:
                pygame.draw.rect(self.screen, self.pencolour, (position[0], position[1], self.pen_size, self.pen_size))
                if self.last_pos:
                    pygame.draw.line(self.screen, self.pencolour, self.last_pos, position, self.pen_size * 2)
                self.last_pos = position
                
        else: # Custom brush
            brushDirectory = os.path.join(setupWindow.brushDirectory, self.pentexture)
            brushProperties = json.load(open(os.path.join(brushDirectory, "properties.json")))
            brushDrawLine = brushProperties["drawLine"]
            brushLineSize = brushProperties["lineSize"]
            brushUseColour = brushProperties["useColour"]
            brushRotate = brushProperties["rotate"]
            brushTextureAmount = brushProperties["textureAmount"]

            if brushTextureAmount <= 1:
                brushTexture = pygame.transform.scale(pygame.image.load(
                os.path.join(brushDirectory, "texture.png")).convert_alpha(), 
                (self.pen_size+4, self.pen_size+4))
            else:
                currentTexture = "texture" + str(random.randint(1,brushTextureAmount)) + ".png"
                brushTexture = pygame.transform.scale(pygame.image.load(
                    os.path.join(brushDirectory, currentTexture)).convert_alpha(), 
                    (self.pen_size+4, self.pen_size+4))
                
            if brushUseColour and not eraser:
                tintSurface = pygame.Surface(brushTexture.get_size(), pygame.SRCALPHA)
                tintSurface.fill(self.pencolour)
                brushTexture.blit(tintSurface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            if brushRotate:
                brushTexture = pygame.transform.rotate(brushTexture, random.randint(0, 360))
            
            if brushDrawLine:
                if self.last_pos:
                    adjustedLineSize = self.pen_size * 2 + brushLineSize
                    adjustedLineSize = max(1, adjustedLineSize)  # Ensure line size is at least 1
                    pygame.draw.line(self.screen, self.pencolour, self.last_pos, position, adjustedLineSize)
            self.last_pos = position

            if eraser:
                brushTexture.fill(self.bgcolour)
            
            texture_width, texture_height = brushTexture.get_size()
            top_left_position = (position[0] - texture_width // 2, position[1] - texture_height // 2)
            self.screen.blit(brushTexture, top_left_position)

    def clear_canvas(self):
        self.canvas = [[self.bgcolour for _ in range(self.canvas_width)] for _ in range(self.canvas_height)]
        self.screen.fill(self.bgcolour)
        self.history = []
        self.snapshot()

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
        self.new = self.builder.get_object("new")

        # Check if widgets are found
        if not all([self.penColour, self.penSize, self.brushSelect, self.togglegrid, self.clear, self.close, self.export, self.new]):
            print("One or more widgets not found in options.xml. Options window will not work.")
            return

        brushes = Gtk.ListStore(str, str)
        brushes.append(["Default","The default brush."]) #FIXME - Description does not load unless this brush is re-selected
        
        # Populate the brush list
        brushDirectory = setupWindow.brushDirectory
        for item in os.listdir(brushDirectory):
            itemPath = os.path.join(brushDirectory, item)
            if os.path.isdir(itemPath):
                properties_path = os.path.join(itemPath, "properties.json")
                if os.path.isfile(properties_path):
                    try:
                        with open(properties_path, 'r') as file:
                            properties = json.load(file)
                            brush_name = properties.get('name', 'Custom')
                            brush_author = properties.get('author', 'Unknown')
                            brush_description = properties.get('description', 'A custom brush.')
                            brush_name = f"[{brush_author}] {brush_name}"
                            brushes.append([brush_name, brush_description])
                    except Exception as e:
                        print(f"Error reading {properties_path}: {e}")

        self.brushSelect.set_model(brushes)
        renderer_text = Gtk.CellRendererText()
        self.brushSelect.pack_start(renderer_text, True)
        self.brushSelect.add_attribute(renderer_text, "text", 0)
        self.brushSelect.set_active_iter(brushes.get_iter_first())


        # Connect signals
        self.main_window.connect("delete-event", self.on_delete_event)
        self.penColour.connect("notify::rgba", self.on_pen_colour_changed)
        self.penSize.connect("value-changed", self.on_pen_size_changed)
        self.brushSelect.connect("changed", self.on_brush_changed)
        self.togglegrid.connect("clicked", self.on_togglegrid_clicked)
        self.clear.connect("clicked", self.on_clear_clicked)
        self.close.connect("clicked", self.on_close_clicked)
        self.export.connect("clicked", self.on_export_clicked)
        self.new.connect("clicked", self.on_new_clicked)
        

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

    def on_new_clicked(self, widget):
        self.main_window.destroy()
        print("Starting new project...")
        global canvasRunning
        canvasRunning = False
        global setupProject
        setupProject()

    def on_pen_colour_changed(self, widget, param):
        rgba = widget.get_rgba()
        pencolour = (int(rgba.red * 255), int(rgba.green * 255), int(rgba.blue * 255))
        
        global canvasWindow
        canvasWindow.pencolour = pencolour

    def on_pen_size_changed(self, widget):
        newSize = widget.get_value_as_int()
        global canvasWindow
        try: # Error suppression for Grid Mode
            canvasWindow.pen_size = newSize
        except:
            pass

    def on_brush_changed(self, widget):
        model = widget.get_model()
        index = widget.get_active()
        if index >= 0:
            selected = model[index][0]
            selected_description = model[index][1]
            global canvasWindow
            canvasWindow.pentexture = selected
            print(f"Brush selected: {selected} - {selected_description}")

        # Change tooltip text to brush description
        active_iter = widget.get_active_iter()
        if active_iter is not None:
            name, description = model[active_iter][:2]
            widget.set_tooltip_text(description)

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

        # Check if the operating system is supported
        if platform.system() not in ["Windows", "Darwin", "Linux"]:
            print(f"Error: Your operating system ({platform.system()}) is not supported! Please use Windows, macOS or Linux.")
            dialog = Gtk.MessageDialog(
            parent=self.main_window,
            modal=True,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            message_format=f"Your operating system ({platform.system()}) is not supported! Please use Windows, macOS or Linux.")
            dialog.set_title("Error")
            dialog.run()
            dialog.destroy()
            self.main_window.destroy()
            sys.exit()

        # Find + define config directory
        system = platform.system()
        if system == "Linux":
            self.config_dir = os.path.expanduser("~/.config/frdgCanvas")
        elif system == "Windows":
            appdata = os.environ.get("APPDATA")
            self.config_dir = os.path.join(os.path.dirname(appdata), "Local", "frdgCanvas") if appdata else None
        elif system == "Darwin":
            self.config_dir = os.path.expanduser("~/Library/Application Support/frdgCanvas")
        else:
            self.config_dir = None
            print("Unknown operating system. Configuration directory will not be created.")

        if self.config_dir:
            os.makedirs(self.config_dir, exist_ok=True)
            print(f"Using configuration directory: {self.config_dir}")

        # Create necessary config directories
        def checkDirectory(path):
            if not os.path.exists(path) and not self.config_dir is None:
                os.makedirs(path)
                print(f"Directory '{path}' not found - created.")

        self.brushDirectory = self.config_dir + "/brushes"
        checkDirectory(self.brushDirectory)

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

        self.brushInstaller = self.builder.get_object("brushInstaller")
        self.openConfig = self.builder.get_object("openConfig")
        self.add_file_filter()

        # Check if widgets are found
        if not all([self.name_entry, self.width_entry, self.height_entry, self.bgColour, self.grid_button, self.submit_button, self.close_button, self.gridColour, self.pixel_size, self.fullscreen, self.brushInstaller, self.openConfig]):
            print("One or more widgets not found in setup.xml. Closing.")
            return

        # Connect signals
        self.submit_button.connect("clicked", self.on_submit_clicked)
        self.close_button.connect("clicked", self.on_close_clicked)
        self.openConfig.connect("clicked", self.on_open_config_clicked)
        self.brushInstaller.connect("file-set", self.on_brush_set)
        
    def on_open_config_clicked(self, widget):
        if platform.system() == "Windows":
            explorer_path = os.path.normpath(self.config_dir)
            subprocess.run(["explorer", "/select,", explorer_path])
        elif platform.system() == "Darwin":
            subprocess.run(["open", "-R", self.config_dir])
        else:
            subprocess.run(["xdg-open", self.config_dir])

    def add_file_filter(self):
        file_filter = Gtk.FileFilter()
        file_filter.set_name("frdgCanvas brush files")
        file_filter.add_pattern("*.frdgbrush")
        self.brushInstaller.add_filter(file_filter)

    def installdialog(self, message):
        dialog = Gtk.MessageDialog(
            parent=self.main_window,
            modal=True,
            type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.CLOSE,
            message_format=message
        )
        dialog.set_title("Installing brush...")
        response = dialog.run()
        dialog.destroy()
        return response
    
    def on_brush_set(self, widget):
        if os.path.isdir(os.path.join(self.brushDirectory, ".temp")):
            shutil.rmtree(os.path.join(self.brushDirectory, ".temp"))
        file_path = widget.get_filename()
        print(f"Installing brush: {file_path}")
        if file_path.endswith('.frdgbrush'):
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    os.makedirs(os.path.join(self.brushDirectory, ".temp"))
                    zip_ref.extractall(os.path.join(self.brushDirectory, ".temp"))
            except zipfile.BadZipFile:
                print("Error: The file is not a valid archive.")
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print("The selected file is not a .frdgbrush file.")

        with open(os.path.join(self.brushDirectory, ".temp", "properties.json"), 'r') as file:
            properties = json.load(file)
            brush_name = properties.get('name', 'Custom')
            brush_author = properties.get('author', 'Unknown')
            brush_description = properties.get('description', 'A custom brush.')

            if os.path.isdir(os.path.join(self.brushDirectory, ("["+brush_author+"] "+brush_name))):
                print(f"The brush '{brush_name}' by '{brush_author}' is already installed.")
                self.installdialog(f"The brush '{brush_name}' by '{brush_author}' is already installed.")
            else:
                shutil.copytree(os.path.join(self.brushDirectory, ".temp"), os.path.join(self.brushDirectory, ("["+brush_author+"] "+brush_name)))
                print(f"Installed brush: {brush_name} by {brush_author} - {brush_description}")
                self.installdialog(f"Success! Installed brush: \n\n{brush_name} by {brush_author} - {brush_description}")


        if os.path.isdir(os.path.join(self.brushDirectory, ".temp")):
            shutil.rmtree(os.path.join(self.brushDirectory, ".temp"))

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
                canvasWindow = Canvas(name, int(width), int(height), int(bgColour.red * 255), int(bgColour.green * 255), int(bgColour.blue * 255), bool(gridMode), int(pixelSize), int(gridColour.red * 255), int(gridColour.green * 255), int(gridColour.blue * 255))
                # *breathe out*
                canvasWindow.run()

            global canvasRunning
            canvasRunning = True
            canvasThread = threading.Thread(target=startCanvas)

            global optionsWindow
            optionsWindow = Options(fullscreen)
            print("Options window started")
            canvasThread.start()
            print("Canvas thread started")
            if optionsWindow.main_window:
                optionsWindow.main_window.show_all()
                Gtk.main()

        else:
            print("Error: Invalid input provided for project creation")
            self.invalid_input()



# --// Runtime //-- #
if __name__ == "__main__":
    setupProject()
