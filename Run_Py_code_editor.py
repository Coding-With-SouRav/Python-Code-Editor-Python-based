import ast
from collections import defaultdict
import difflib
import importlib.util
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import os
import subprocess
import sys
import tkinter as tk
import re
import threading
import jedi
import configparser
import tempfile
import queue
import shutil
import uuid 
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import signal
import pyperclip
import google.generativeai as genai
from tkinterdnd2 import DND_FILES, TkinterDnD





def resource_path(relative_path):
    """ Get absolute path to resources for both dev and PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    full_path = os.path.join(base_path, relative_path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Resource not found: {full_path}")
    return full_path

class VSCodeLikeEditor:

    class FileChangeHandler(FileSystemEventHandler):
        def __init__(self, editor):
            super().__init__()
            self.editor = editor

        def on_any_event(self, event):
            self.editor.should_update = True

    class CustomInputDialog(tk.Toplevel):
        def __init__(self,editor, parent, title, prompt):
            super().__init__(parent)
            self.editor = editor
            self.title(title)
            self.overrideredirect(True) 
            self.config(bg=self.editor.BLACK)
            self.entry = None
            self.result = None

            self.CustomInputDialog_label = tk.Label(self, text=prompt, bg=self.editor.BLACK, fg='cyan', font=("Consolas", 14))
            self.CustomInputDialog_label.pack(padx=20, pady=10)

            self.entry = tk.Entry(self, font=("Consolas", 14), bg=self.editor.BLACK, fg="white", insertbackground="white")
            self.entry.pack(padx=20, pady=5)
            self.entry.bind("<Return>", lambda e: self.ok_pressed())  # Enter key binding

            button_frame = tk.Frame(self, bg=self.editor.BLACK)
            button_frame.pack(pady=5)

            self.ok_button = tk.Button(button_frame, text="OK", command=self.ok_pressed, 
                                    bg="#007acc", fg="white", font=("Consolas", 14), width=8)
            self.ok_button.pack(side=tk.RIGHT, padx=5)

            self.cancel_button = tk.Button(button_frame, text="Cancel", command=self.cancel_pressed,
                                        bg="red", fg="white", font=("Consolas", 14), width=8)
            self.cancel_button.pack(side=tk.LEFT, padx=5)

            self.geometry("+%d+%d" % (parent.winfo_rootx()+50, parent.winfo_rooty()+50))
            self.grab_set()

                        
        def ok_pressed(self):
            self.result = self.entry.get()
            self.destroy()

        def cancel_pressed(self):
            self.result = None
            self.destroy()

        def show(self):
            self.wait_window()
            return self.result
                
    class ToolTip:
        def __init__(self, editor, widget, text):
            self.editor = editor
            self.widget = widget
            self.text = text
            self.tipwindow = None
            self.widget.bind("<Enter>", self.showtip)
            self.widget.bind("<Leave>", self.hidetip)

        def showtip(self, event=None):
            if self.tipwindow:
                return
            # Calculate position relative to the main window
            x = self.widget.winfo_rootx() + 25
            y = self.widget.winfo_rooty() + 25
            self.tipwindow = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)  # Remove window decorations
            tw.wm_geometry(f"+{x}+{y}")
            self.ToolTip_label = tk.Label(tw, text=self.text, bg=self.editor.BLACK, fg="#ffff00", font=("Consolas", 11, "italic"))
            self.ToolTip_label.pack()

        def hidetip(self, event=None):
            if self.tipwindow:
                self.tipwindow.destroy()
            self.tipwindow = None

    class ReverseToolTip:
        def __init__(self,editor, widget, text):
            self.editor = editor
            self.widget = widget
            self.text = text
            self.tipwindow = None
            self.widget.bind("<Enter>", self.showtip)
            self.widget.bind("<Leave>", self.hidetip)

        def showtip(self, event=None):
            if self.tipwindow:
                return
            # Calculate position relative to the main window
            x = self.widget.winfo_rootx() -100
            y = self.widget.winfo_rooty() + 25
            self.tipwindow = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)  # Remove window decorations
            tw.wm_geometry(f"+{x}+{y}")
            self.ReverseToolTip_label = tk.Label(tw, text=self.text, bg=self.editor.BLACK, fg="#ffff00", font=("Consolas", 11, "italic"))
            self.ReverseToolTip_label.pack()

        def hidetip(self, event=None):
            if self.tipwindow:
                self.tipwindow.destroy()
            self.tipwindow = None
                
    class Toggle_replace_btn_ToolTip:
        def __init__(self, editor, widget, text):
            self.editor = editor
            self.widget = widget
            self.text = text
            self.tipwindow = None
            self.widget.bind("<Enter>", self.showtip)
            self.widget.bind("<Leave>", self.hidetip)

        def showtip(self, event=None):
            if self.tipwindow:
                return
            # Calculate position relative to the main window
            x = self.widget.winfo_rootx() - 100
            y = self.widget.winfo_rooty() - 25
            self.tipwindow = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)  # Remove window decorations
            tw.wm_geometry(f"+{x}+{y}")
            self.ToolTip_label = tk.Label(tw, text=self.text, bg=self.editor.BLACK, fg="#ffff00", font=("Consolas", 11, "italic"))
            self.ToolTip_label.pack()

        def hidetip(self, event=None):
            if self.tipwindow:
                self.tipwindow.destroy()
            self.tipwindow = None

    class ReplaceDialog(tk.Toplevel):
        def __init__(self, editor):
            super().__init__(editor.root)
            self.editor = editor
            self.transient(editor.root) 
            self.overrideredirect(True)
            self.wm_attributes("-topmost", True)
            self.last_known_position = None

            self.replace_visible = False

            self.bind("<Unmap>", self.on_unmap)
            self.bind("<Map>", self.on_map)
            self.editor.root.bind("<Configure>", self.update_position)
            self.editor.root.bind("<FocusIn>", self.on_main_window_focus)
        
            self.configure(bg=editor.BLACK)
            self.transient(editor.root)  # Set as transient window
            editor.root.bind("<<ThemeChanged>>", self.update_theme)
            
            # Store initial search position
            self.search_start = "1.0"
            self.current_match = None
            
            # Find Frame
            self.find_frame = tk.Frame(self, bg=editor.BLACK)
            self.find_frame.pack(pady=5)

            self.toggle_button = tk.Button(
                self.find_frame,
                text=">>",
                command=self.toggle_replace,
                bg=editor.BLACK,
                fg='yellow',
                bd=0,
                activebackground=editor.BLACK,
                activeforeground='cyan',
                font=('Consolas', 11)
            )
            self.toggle_button.pack(side=tk.LEFT, padx=(0, 1))
            self.editor.Toggle_replace_btn_ToolTip(self.editor, self.toggle_button, "Toggle Replace")

            self.close_replace_btn = tk.Button(
                self.find_frame,
                text=" ❌ ",
                command=self.on_close,
                bg=editor.BLACK,
                fg='red',
                bd=0,
                activebackground=editor.BLACK,
                activeforeground='red',
                font=('Consolas', 11)
            )
            self.close_replace_btn.pack(side=tk.RIGHT, padx=(0, 1))
            
            
            self.find_label = tk.Label(self.find_frame, text="", bg=editor.BLACK, font= ('Consolas',12), fg='cyan')
            self.find_label.pack(side=tk.LEFT)

            self.match_count_label = tk.Label(self.find_frame, text="0 matches", 
                                        bg=editor.BLACK, fg='yellow',
                                        font=('Consolas',12))
            self.match_count_label.pack(side=tk.RIGHT, padx=5)

            self.find_entry = tk.Entry(self.find_frame, 
                                       width=10, 
                                       bg=editor.BLACK, 
                                       fg='gray', 
                                       insertbackground='white', 
                                       font= ('Consolas',12,'italic')
                                       ) 
            self.find_entry.insert(0, "Find")
            self.find_entry.pack(side=tk.LEFT, padx=5)
            self.find_entry.bind("<FocusIn>", self.on_find_focus_in)
            self.find_entry.bind("<FocusOut>", self.on_find_focus_out)


           
            # Replace Frame
            self.replace_frame = tk.Frame(self, bg=editor.BLACK)

            self.replace_label = tk.Label(self.replace_frame, text="", bg=editor.BLACK, font= ('Consolas',12), fg='cyan')
            self.replace_label.pack(side=tk.LEFT)
            
            self.replace_entry = tk.Entry(self.replace_frame,
                                            width=24,
                                            bg=editor.BLACK, 
                                            fg='gray', 
                                            insertbackground='white',
                                            font= ('Consolas',12,'italic')
                                            )
            self.replace_entry.insert(0, "Replace")
            self.replace_entry.pack(side=tk.LEFT, padx=0)
            self.replace_entry.bind("<FocusIn>", self.on_replace_focus_in)
            self.replace_entry.bind("<FocusOut>", self.on_replace_focus_out)

            self.replace_entry.bind("<Return>", self.replace_next)
            self.find_entry.bind("<Up>", lambda e: self.toggle_replace())
            self.find_entry.bind("<Down>", lambda e: self.toggle_replace())
            
           
            self.protocol("WM_DELETE_WINDOW", self.on_close)
            self.find_entry.bind("<KeyRelease>", self.highlight_matches)
            self.find_entry.bind("<KeyPress>", self.highlight_matches)

            self.update_position()
       
        def toggle_replace(self):
            self.replace_visible = not self.replace_visible
            
            if self.replace_visible:
                # Pack replace frame AFTER find frame
                self.replace_frame.pack(pady=5, after=self.find_frame)
                self.toggle_button.config(text="˅", font=('Consolas', 13))
            else:
                self.replace_frame.pack_forget()
                self.toggle_button.config(text=">>", font=('Consolas', 11))
            
            # Force geometry update
            self.update_idletasks()
            self.update_position()
            self.geometry("")

        def on_main_window_focus(self, event=None):
            """Bring replace dialog to front when main window gets focus"""
            if self.winfo_exists():
                self.lift()

        def update_position(self, e = None):
            if not self.winfo_exists():
                return

            # Get main window dimensions
            main_win = self.editor.root
            main_x = main_win.winfo_x()
            main_y = main_win.winfo_y()
            main_width = main_win.winfo_width()
            main_height = main_win.winfo_height()

            # Get code editor position
            code_editor = self.editor.code_editor
            ed_x = code_editor.winfo_rootx() + code_editor.winfo_width()
            ed_y = code_editor.winfo_rooty()

            # Get dialog dimensions
            self.update_idletasks()
            dlg_width = self.winfo_width()
            dlg_height = self.winfo_height()

            # Calculate max allowed position
            max_x = main_x + main_width - dlg_width
            max_y = main_y + main_height - dlg_height

            # Constrain coordinates within main window
            x = max(main_x, min(ed_x, max_x))
            y = max(main_y, min(ed_y, max_y))

            # Ensure dialog doesn't go offscreen vertically
            screen_height = self.winfo_screenheight()
            if y + dlg_height > screen_height:
                y = max(main_y, ed_y - dlg_height - 20)

            self.geometry(f"+{int(x)}+{int(y)}")
            self.deiconify()

        def update_theme(self, event=None):
            if not self.winfo_exists():  # Check if the replace dialog exists
                return
            self.configure(bg=self.editor.BLACK)
            self.find_frame.configure(bg=self.editor.BLACK)
            self.find_label.configure(bg=self.editor.BLACK)
            self.replace_frame.configure(bg=self.editor.BLACK)
            self.replace_label.configure(bg=self.editor.BLACK)
            self.find_entry.configure(bg=self.editor.BLACK)
            self.replace_entry.configure(bg=self.editor.BLACK)
            self.match_count_label.configure(bg=self.editor.BLACK)
            self.toggle_button.configure(bg=self.editor.BLACK, activebackground= self.editor.BLACK)
            self.close_replace_btn.configure(bg=self.editor.BLACK, activebackground= self.editor.BLACK)

        def on_unmap(self, event):
            if self.editor.root.state() == 'iconic':
                # self.withdraw()
                return

        def on_map(self, event = None):
            self.update_position()

        def highlight_matches(self, event=None):
            self.editor.code_editor.tag_remove("search_highlight", "1.0", tk.END)
            find_text = self.find_entry.get().strip()

            if find_text == "Find" and self.find_entry.cget('fg') == 'gray':
                find_text = ""  

            match_count = 0  # Initialize counter

            if not find_text:
                self.match_count_label.config(text="0 matches")  # Reset count if empty
                self.update_position()
                return  
            
            if find_text:
                start = "1.0"
                while True:
                    start = self.editor.code_editor.search(
                        find_text, start, 
                        nocase=False, 
                        stopindex=tk.END,
                        regexp=False
                    )
                    if not start:
                        break
                    end = f"{start}+{len(find_text)}c"
                    self.editor.code_editor.tag_add("search_highlight", start, end)
                    match_count += 1  # Increment counter
                    start = end

                # Update match count label
                self.match_count_label.config(
                    text=f"{match_count} {'match' if match_count == 1 else 'matches'}"
                )
            
            self.update_position()
            self.editor.code_editor.tag_config(
                "search_highlight", 
                background="yellow", 
                foreground="black"
            )
        
        def on_close(self):
            self.editor.code_editor.tag_remove("search_highlight", "1.0", tk.END)
            self.editor.code_editor.tag_remove("current_match", "1.0", tk.END)
            self.editor.code_editor.focus_set()
            self.destroy()
            if hasattr(self.editor, 'replace_dialog'):
                del self.editor.replace_dialog

        def find_next_match(self, start_pos):
            find_text = self.find_entry.get()
            if not find_text:
                return None
                
            # Search from current position
            match_pos = self.editor.code_editor.search(
                find_text, start_pos, 
                nocase=False, 
                stopindex=tk.END,
                regexp=False
            )

            if match_pos:
                # Highlight current match
                end_pos = f"{match_pos}+{len(self.find_entry.get())}c"
                self.editor.code_editor.tag_add("current_match", match_pos, end_pos)
                self.editor.code_editor.tag_config(
                    "current_match", 
                    background="orange", 
                    foreground="black"
                )
            
            # If not found, wrap around from start
            if not match_pos and start_pos != "1.0":
                match_pos = self.editor.code_editor.search(
                    find_text, "1.0", 
                    nocase=False, 
                    stopindex=start_pos,
                    regexp=False
                )
                
            return match_pos

        def replace_next(self, event=None):
            find_text = self.find_entry.get().strip()

            if find_text == "Find" and self.find_entry.cget('fg') == 'gray':
                find_text = ""

            replace_text = self.replace_entry.get().strip()

            if replace_text == "Replace" and self.replace_entry.cget('fg') == 'gray':
                replace_text = ""  # Treat placeholder as empty

            
            if not find_text:
                return
                
            editor = self.editor
            editor.code_editor.tag_remove("match", "1.0", tk.END)
            
            # Get current cursor position or use last match end
            start_pos = editor.code_editor.index(tk.INSERT)
            if self.current_match:
                start_pos = self.current_match
                
            match_pos = self.find_next_match(start_pos)
            
            if match_pos:
                self.editor.code_editor.tag_remove("current_match", "1.0", tk.END)
                end_pos = f"{match_pos}+{len(find_text)}c"
                
                # Highlight the match
                editor.code_editor.tag_add("match", match_pos, end_pos)
                editor.code_editor.tag_config("match", background="#4A4A4A")
                
                # Replace when Enter is pressed
                editor.code_editor.delete(match_pos, end_pos)
                editor.code_editor.insert(match_pos, replace_text)
                self.editor.highlight_syntax()
                
                # Move cursor to end of replacement
                new_pos = f"{match_pos}+{len(replace_text)}c"
                editor.code_editor.mark_set(tk.INSERT, new_pos)
                editor.code_editor.see(new_pos)
                
                # Store current match position
                self.current_match = new_pos
                self.highlight_matches()
            else:
                if not self.current_match:
                    messagebox.showinfo("Replace", "Text not found", parent=self)
                else:
                    # After wrapping around
                    messagebox.showinfo("Replace", "No more occurrences", parent=self)
                    self.current_match = None
                editor.code_editor.tag_remove("match", "1.0", tk.END)

        def on_find_focus_in(self, event):
            if self.find_entry.get() == "Find":
                self.find_entry.delete(0, tk.END)  # Remove placeholder text
                self.find_entry.config(fg='white', font=('Consolas', 12))

        def on_find_focus_out(self, event):
            if not self.find_entry.get():
                self.find_entry.insert(0, "Find")
                self.find_entry.config(fg='gray', font=('Consolas', 12, 'italic'))
            else:
                # Ensure non-placeholder text has correct formatting
                self.find_entry.config(fg='white', font=('Consolas', 12))

        def on_replace_focus_in(self, event):
            if self.replace_entry.get() == "Replace":
                self.replace_entry.delete(0, tk.END)  # Remove placeholder text
                self.replace_entry.config(fg='white', font=('Consolas', 12))

        def on_replace_focus_out(self, event):
            if not self.replace_entry.get():
                self.replace_entry.insert(0, "Replace")
                self.replace_entry.config(fg='gray', font=('Consolas', 12, 'italic'))

    def __init__(self, root):
        self.BLACK = 'black'
        self.CYAN = 'cyan'


        self.output_queue = queue.Queue()
        self.root = root
        self.root.title("Python Editor")
        
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.config(bg=self.BLACK)  # Add this line


        # Colors
        self.ACCENT_COLOR = "#007acc"
        self.TERMINAL_BG = "#252526"
        self.TERMINAL_FG = "#ffffff"
        self.FOLDER_COLOR = "#ffcc00"
        self.FILE_COLOR = "#00ffcc"
        self.SELECTION_BORDER = "black"  # Add brown color constant
        

        # Global Variables
        self.font_size = 14
        self.font_style = ("Consolas", 14)
        self.menu_bar_font_style = ("Consolas", 12)
        self.current_file = None
        self.folder_path = None
        self.process = None
        self.file_selected = False
        self.last_col_position = {}
        self.deletion_history = [] 
        self.undo_stack = [] 
        self.redo_stack = []
        self.active_processes = [] 
        self.opened_files = []
        self.current_tab = None
        self.tab_buttons = {}
        self.tab_frame = None
        self.canvas_scrollbar = None
        self.clipboard = {"operation": None, "paths": []} 
        self.backup_dir = tempfile.mkdtemp(prefix='editor_undo_') 
        self.typed_word = ""
        self.config_file = "config.ini"
        self.last_line_count = 0  
        self.suggestion_timer = None 
        self.update_timer = None 
        self.highlight_timer = None
        self.rename_entry = None 
        self.ctrl_shift_pressed_during_click = False 
        self.observer = None
        self.should_update = False
        self.sidebar_visible = True
        self.selection_anchor = None
        self.missing_module_check_timer = None
        self.import_check_timer = None
        self.syntax_colors = {
            "data_type": "#03f34a",
            "keyword1": "#ff00ff",
            "keyword2": "blue",
            "non_data_type": self.CYAN,
            "bracket": "yellow",
            "number": "#970fed",
            "string": "#c25507",
            "import_text": "#05be1c",
            "comment": "green",
            "comment_bracket": "green"
        }
        self.import_pattern = re.compile(
            r"^(?:from\s+([\w.]+)\s+import|import\s+([\w., \n]+?(?=\s*as\s+\w+|\s*$)))",
            re.MULTILINE
        )
        
        genai.configure(api_key='AIzaSyCgepCd72RunvdGLuD-258qaawcWeHBubg')
        self.generation_config = {"temperature": 0.9, "max_output_tokens": 2048}
        
        self.load_images()
        self.init_ui()
        self.load_window_geometry()
        self.on_text_change()
        self.code_editor.tag_config("error", underline=True, underlinefg="red", foreground="red")
        if getattr(sys, 'frozen', False):
            sys.path.append(os.path.join(sys._MEIPASS, 'jedi'))
            sys.path.append(os.path.join(sys._MEIPASS, 'parso'))
        self.auto_save()

    def load_images(self):

        self.window_icon_path = resource_path(r"icons\app_icon.ico")
        self.root.iconbitmap(self.window_icon_path)  

        self.bg_img = Image.open(resource_path(r"icons\python_bg.png")).resize((340, 340))
        self.file_explorer_img = Image.open(resource_path(r"icons\file_explorer.png")).resize((35, 40))
        self.search_img = Image.open(resource_path(r"icons\search.png")).resize((35, 40))
        self.toggle_folder_img = Image.open(resource_path(r"icons\Toggle_folders.png")).resize((35, 40))
        self.terminal_close_img = Image.open(resource_path(r"icons\terminal_close.png")).resize((25, 25))
        self.terminal_delete_img = Image.open(resource_path(r"icons\trash_bin.png")).resize((22, 30))
        self.folder_img = Image.open(resource_path(r"icons\folder.png")).resize((17, 17))
        self.new_folder_img = Image.open(resource_path(r"icons\new_folder.png")).resize((25, 25))
        self.file_img = Image.open(resource_path(r"icons\file.png")).resize((17, 17))
        self.new_file_img = Image.open(resource_path(r"icons\new_file.png")).resize((30, 30))
        self.python_img = Image.open(resource_path(r"icons\python.png")).resize((17, 17))
        self.html_img = Image.open(resource_path(r"icons\html.png")).resize((17, 17))
        self.css_img = Image.open(resource_path(r"icons\css.png")).resize((17, 17))
        self.js_img = Image.open(resource_path(r"icons\js.png")).resize((17, 17))
        self.png_img = Image.open(resource_path(r"icons\png.png")).resize((17, 17))
        self.ico_img = Image.open(resource_path(r"icons\ico.png")).resize((17, 17))
        self.csv_img = Image.open(resource_path(r"icons\csv.png")).resize((17, 17))
        self.pyc_img = Image.open(resource_path(r"icons\pyc.png")).resize((17, 17))
        self.jpg_img = Image.open(resource_path(r"icons\jpg.png")).resize((17, 17))
        self.db_img = Image.open(resource_path(r"icons\db.png")).resize((17, 17))
        self.c_img = Image.open(resource_path(r"icons\c.png")).resize((17, 17))
        self.cpp_img = Image.open(resource_path(r"icons\cpp.png")).resize((17, 17))
        self.cserp_img = Image.open(resource_path(r"icons\cserp.png")).resize((17, 17))

        self.dark_blue_img = Image.open(resource_path(r"icons\dark_blue_theme.png")).resize((27, 25))
        self.black_img = Image.open(resource_path(r"icons\black_theme.png")).resize((30, 28))
        self.dark_green_img = Image.open(resource_path(r"icons\dark_green_theme.png")).resize((26, 30))
        self.dark_gray_img = Image.open(resource_path(r"icons\dark_gray_theme.png")).resize((23, 23))


        self.bg_photo = ImageTk.PhotoImage(self.bg_img)
        self.file_explorer_icon = ImageTk.PhotoImage(self.file_explorer_img)
        self.search_icon = ImageTk.PhotoImage(self.search_img)
        self.toggle_folder_icon = ImageTk.PhotoImage(self.toggle_folder_img)
        self.terminal_delete_icon = ImageTk.PhotoImage(self.terminal_delete_img)
        self.terminal_close_icon = ImageTk.PhotoImage(self.terminal_close_img)
        self.folder_icon = ImageTk.PhotoImage(self.folder_img)
        self.new_folder_icon = ImageTk.PhotoImage(self.new_folder_img)
        self.file_icon = ImageTk.PhotoImage(self.file_img)
        self.new_file_icon = ImageTk.PhotoImage(self.new_file_img)
        self.python_icon = ImageTk.PhotoImage(self.python_img)
        self.html_icon = ImageTk.PhotoImage(self.html_img)
        self.css_icon = ImageTk.PhotoImage(self.css_img)
        self.js_icon = ImageTk.PhotoImage(self.js_img)
        self.png_icon = ImageTk.PhotoImage(self.png_img)
        self.ico_icon = ImageTk.PhotoImage(self.ico_img)
        self.csv_icon = ImageTk.PhotoImage(self.csv_img)
        self.pyc_icon = ImageTk.PhotoImage(self.pyc_img)
        self.jpg_icon = ImageTk.PhotoImage(self.jpg_img)
        self.db_icon = ImageTk.PhotoImage(self.db_img)
        self.c_icon = ImageTk.PhotoImage(self.c_img)
        self.cpp_icon = ImageTk.PhotoImage(self.cpp_img)
        self.cserp_icon = ImageTk.PhotoImage(self.cserp_img)

        self.dark_blue_icon = ImageTk.PhotoImage(self.dark_blue_img)
        self.black_icon = ImageTk.PhotoImage(self.black_img)
        self.dark_green_icon = ImageTk.PhotoImage(self.dark_green_img)
        self.dark_gray_icon = ImageTk.PhotoImage(self.dark_gray_img)

    def init_ui(self):
                
        self.top_frame = tk.Frame(self.root, bg=self.BLACK)
        self.top_frame.pack(fill=tk.X, side="top")

        self.filename_label = tk.Label(self.top_frame, text="", bg=self.BLACK, fg="yellow",font=("Consolas", 14))
        self.filename_label.bind("<Button-1>", lambda e: self.focus_file_in_tree())
        self.filename_label.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.filename_label.pack_forget()

        # Run Button
        self.run_button = tk.Button(self.top_frame, 
                                    text=" ▶ ", 
                                    font=self.font_style,
                                    activebackground=self.BLACK, 
                                    command=self.run_code, 
                                    bg=self.ACCENT_COLOR, 
                                    fg="white")
        self.run_button.pack(side=tk.RIGHT, padx=5, pady=5)
        self.ReverseToolTip(self,self.run_button, "Run Code (Alt+S)")

        # Stop Button
        self.stop_button = tk.Button(self.top_frame,
                                            text=" ■ ",
                                            font=self.font_style,
                                            command=self.stop_code,
                                            bg="red",
                                            activebackground=self.BLACK, 
                                            fg="white")
        self.stop_button.pack(side=tk.RIGHT, padx=5, pady=5)
        self.ReverseToolTip(self,self.stop_button, "Stop Code (Ctrl+Q)")
        self.stop_button.pack_forget()

       
        self.AI_search_entry = tk.Entry(
            self.top_frame,
            font=("Consolas", 14, 'italic'),
            bg=self.BLACK,
            fg="white",
            insertbackground="white",
            border=0,
            borderwidth=3,
            width=40,
            relief="flat",
            highlightthickness=1,
            highlightcolor=self.ACCENT_COLOR,
            highlightbackground=self.CYAN
        )

        self.AI_search_entry.place(relx=0.565, rely=0.5, anchor='center')  # Center in top frame
        self.AI_search_entry.insert(0, "                Ask to AI...")
        self.AI_search_entry.config(fg='gray')
        self.AI_search_entry.bind("<FocusIn>", lambda e: self.AI_search_entry.delete(0, tk.END))
        self.AI_search_entry.bind("<FocusOut>", lambda e: self.AI_search_entry.insert(0, "              Ask to AI...") if not self.AI_search_entry.get() else None)
        self.AI_search_entry.bind("<Return>", self.handle_ai_query)
 


        self.file_explorer_toggle_btn = tk.Button(
            self.top_frame,
            image=self.file_explorer_icon,
            command=self.toggle_sidebar,
            bg=self.BLACK,
            activebackground=self.BLACK,
            border=0,
            borderwidth=0
        )        
        self.file_explorer_toggle_btn.place(x=7, y=5, width=40, height=40)
        self.ToolTip(self,self.file_explorer_toggle_btn, "File Explorer\n (Ctrl+Shift+E)")

        self.word_search_btn = tk.Button(
            self.top_frame,
            image=self.search_icon,
            command=self.open_replace_dialog,
            bg=self.BLACK,
            activebackground=self.BLACK,
            border=0,
            borderwidth=0
        )        
        self.word_search_btn.place(x=60, y=5, width=40, height=40)
        self.ToolTip(self,self.word_search_btn, "Search for text\n in files (F3)")

        self.toggle_folder_btn= tk.Button(
            self.top_frame,
            image=self.toggle_folder_icon,
            command=self.toggle_all_folders,
            bg=self.BLACK,
            activebackground=self.BLACK,
            border=0,
            borderwidth=0
        )        
        self.toggle_folder_btn.place(x=120, y=5, width=40, height=40)
        self.ToolTip(self,self.toggle_folder_btn, "Expand/Collapse\n All Folders (F6)")

        # Main Pane
        self.main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=8, bg=self.CYAN)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        # Style Configuration
        self.style = ttk.Style()
        self.style.layout("Custom.Treeview.Item", [
                    ('Treeitem.padding', {'sticky': 'nswe', 'children': [
                        ('Treeitem.indicator', {'side': 'left', 'sticky': ''}),
                        ('Treeitem.image', {'side': 'left', 'sticky': ''}),
                        ('Treeitem.text', {'side': 'left', 'sticky': ''}),
                    ]})
                ])
        self.style.theme_use('clam')
        self.style.configure("Treeview", 
                            font=("Consolas", 12),
                            background=self.BLACK, 
                            fieldbackground=self.BLACK, 
                            foreground=self.CYAN, 
                            bordercolor="#654321",
                            borderwidth=2,
                            rowheight = 28,
                            padding=5
                            )
        self.style.configure("Treeview.Heading",
                            font=("Consolas", 12),
                            background=self.BLACK, 
                            foreground=self.CYAN
                            )
        self.style.map("Treeview",
                        background=[("selected", self.BLACK)],
                        foreground=[('selected', self.CYAN)],
                        bordercolor=[('selected', '#654321')],  # Brown border for selection
                        relief=[('selected', 'solid')],
                        borderwidth=[('selected', 2)]  
                       )
        self.style.map("Custom.Treeview",
                            background=[('selected', '#1a1a1a')],
                            relief=[('selected', 'solid')],
                            bordercolor=[('selected', '#007acc')],
                            borderwidth=[('selected', 2)],
                            foreground=[('selected', 'white')]
                        )
        self.style.configure("Treeview.clipboard", 
                   background="#2d2d30", 
                   foreground=self.CYAN)
        
        self.style.configure("Clipboard.Treeview", background="#2d2d30")
        self.style.map("Clipboard.Treeview",
            background=[('selected', '#2d2d30')],
            foreground=[('selected', self.CYAN)]
        )

        self.style.configure("Vertical.TScrollbar", gripcount=0, background=self.BLACK, troughcolor=self.BLACK, borderwidth=0, width=8)
        self.style.configure("Treeview.Folder", font=("Consolas", 12), foreground="orange")
        self.style.configure("Treeview.File", font=("Consolas", 12), foreground=self.CYAN)
        self.style.configure("Custom.Treeview", background=self.BLACK, foreground=self.CYAN)

        # Folder Tree Frame
        self.folder_tree_frame = tk.Frame(self.main_pane,
                                           bg=self.BLACK, width=550,
                                           highlightbackground=self.SELECTION_BORDER,
                                           highlightthickness=0
                                           )
        self.main_pane.add(self.folder_tree_frame)
        self.folder_tree_frame.pack_propagate(False)
        self.folder_tree_frame.config(width=280)  # initial width
        self.folder_tree_frame.bind("<Configure>", self.enforce_max_width)
        self.folder_tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        self.main_pane.paneconfig(self.folder_tree_frame, minsize=0)
        
        self.button_frame = tk.Frame(self.folder_tree_frame, bg=self.BLACK)
        self.button_frame.pack(fill=tk.X, side=tk.TOP, pady=5)

        self.button_frame1 = tk.Frame(self.folder_tree_frame, bg=self.BLACK)
        self.button_frame1.pack(fill=tk.X, side=tk.TOP, pady=5)

        self.folder_name_label = tk.Label(self.button_frame, text="[❌] No Folder Opened", bg=self.BLACK, fg='#ff0000', font=("Consolas", 15))
        self.folder_name_label.pack(expand=True,fill=tk.BOTH, pady=5)
        self.search_frame = tk.Frame(self.button_frame1, bg=self.BLACK)
        
        self.tree_search_entry = tk.Entry(
            self.search_frame,
            font=("Consolas", 14,'bold'),
            bg=self.BLACK,
            fg="white",
            insertbackground="white",
            border=0,
            borderwidth=3,
            highlightbackground=self.BLACK,
            justify='center'
        )
        self.tree_search_entry.insert(0, "Search")
        self.tree_search_entry.config(fg="gray")

        self.tree_search_entry.pack(side=tk.BOTTOM, fill=tk.X, expand=True)

        self.tree_search_entry.bind("<FocusIn>", self.clear_placeholder)
        self.tree_search_entry.bind("<FocusOut>", self.add_placeholder)
        self.tree_search_entry.bind("<KeyRelease>", self.filter_tree)

        self.make_file_button = tk.Button(
            self.button_frame1,
            image=self.new_file_icon,  # Use the file icon
            command=self.make_file,
            bg=self.BLACK,
            activebackground=self.BLACK,
            border=0,
            borderwidth=0
        )
        
        self.ToolTip(self,self.make_file_button, "Make File")

        self.make_folder_button = tk.Button(
            self.button_frame1,
            image=self.new_folder_icon,  # Use the folder icon
            command=self.make_folder,
            bg=self.BLACK,
            activebackground=self.BLACK,
            border=0,
            borderwidth=0
        )
        
        self.ToolTip(self,self.make_folder_button, "Make Folder")

        self.make_file_button.pack(side=tk.LEFT, padx=5, pady=0)
        self.make_folder_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.folder_tree_scroll_bar = ttk.Scrollbar(self.folder_tree_frame, orient="vertical")
        self.folder_tree_scroll_bar.pack(side="right", fill="y")

        # File Tree View
        self.file_tree = ttk.Treeview(self.folder_tree_frame,
                                    style="Treeview",
                                    selectmode="extended",
                                    padding=(3,3),
                                    yscrollcommand=self.folder_tree_scroll_bar.set,
                                    
                                    )
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.folder_tree_scroll_bar.config(command=self.file_tree.yview)
        self.file_tree.tag_configure("folder", font=("Monospace Text", 12), foreground="#fc0505")
        self.file_tree.tag_configure("file", font=("Math Italic", 12), foreground="#0ce466")
        self.file_tree.tag_configure("cut_item", background="yellow")
        self.file_tree.configure(style="Custom.Treeview")
        self.file_tree.drop_target_register(DND_FILES)
        self.file_tree.dnd_bind('<<Drop>>', self.handle_external_drop)
        self.file_tree.bind("<MouseWheel>", self.on_mousewheel)
        self.file_tree.bind("<<TreeviewSelect>>", self.open_file_from_tree)
        self.file_tree.bind("<Button-3>", self.show_context_menu)
        self.file_tree.bind("<F2>", self.start_rename_via_shortcut)
        self.file_tree.bind("<Delete>", self.delete_items)
        self.file_tree.bind("<ButtonPress-1>", self.on_drag_start)
        self.file_tree.bind("<B1-Motion>", self.on_drag_motion)
        self.file_tree.bind("<ButtonRelease-1>", self.on_drag_release)
        self.file_tree.bind("<Control-a>", self.select_all_files_folders)
        self.file_tree.bind("<Control-A>", self.select_all_files_folders)
        self.file_tree.bind("<Button-1>", self.on_tree_click)  
        self.file_tree.bind("<Control-z>", self.safe_undo)
        self.file_tree.bind("<Control-Z>", self.safe_undo)
        self.file_tree.bind("<Control-y>", self.safe_redo)
        self.file_tree.bind("<Control-Y>", self.safe_redo)
        self.file_tree.bind("<Control-x>", self.cut_items)
        self.file_tree.bind("<Control-c>", self.copy_items)
        self.file_tree.bind("<Control-v>", self.paste_items)
        


        self.folder_tree_horizontal_scroll_bar = ttk.Scrollbar(self.file_tree, orient="horizontal")
        self.folder_tree_horizontal_scroll_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.file_tree.configure(xscrollcommand=self.folder_tree_horizontal_scroll_bar.set)
        self.folder_tree_horizontal_scroll_bar.config(command=self.file_tree.xview)
        self.file_tree.column("#0", width=500, minwidth=300, stretch=True)


        # Vertical Pane
        self.vertical_pane = tk.PanedWindow(self.main_pane, orient=tk.VERTICAL, sashwidth=8, bg=self.CYAN)
        self.main_pane.add(self.vertical_pane, stretch="always")

        # Frame
        self.frame = tk.Frame(self.vertical_pane)
        self.vertical_pane.add(self.frame, stretch="always")

        # Terminal Section (Resizable)
        self.terminal_frame = tk.Frame(self.vertical_pane, bg=self.BLACK)
        self.vertical_pane.add(self.terminal_frame, height=270,stretch = "never")

        # Close Button Frame
        self.close_button_frame = tk.Frame(self.terminal_frame, bg=self.BLACK)
        self.close_button_frame.pack(side=tk.TOP, fill=tk.X)

        # Close Button
        self.close_button = tk.Button(
            self.close_button_frame,
            image=self.terminal_close_icon, 
            bg=self.BLACK, 
            activebackground='red',
            activeforeground=self.BLACK,
            border=0,
            borderwidth=0,
            command=lambda: self.vertical_pane.forget(self.terminal_frame)  # Hide the terminal
        )
        self.close_button.pack(side=tk.RIGHT, padx=10, pady=0)
        self.ReverseToolTip(self,self.close_button, "Hide Terminal")
        
        self.terminal_delete_button = tk.Button(
            self.close_button_frame,
            image=self.terminal_delete_icon, 
            bg=self.BLACK, 
            activebackground='red',
            border=0,
            borderwidth=0,
            command=lambda e=None: [self.vertical_pane.forget(self.terminal_frame), self.stop_code(),self.terminal_delete_clear()]
        )
        self.terminal_delete_button.pack(side=tk.RIGHT, padx=2, pady=0)
        self.ReverseToolTip(self,self.terminal_delete_button, "Kill Terminal")
        

        # Editor Frame
        self.editor_frame = tk.Frame(self.frame, bg=self.BLACK)
        self.editor_frame.pack(fill=tk.BOTH, expand=True)

        self.file_tab_canvas = tk.Canvas(self.editor_frame, bg=self.BLACK, height=30, highlightthickness=1,highlightcolor=self.CYAN,highlightbackground=self.CYAN)
        self.file_tab_canvas.pack(side=tk.TOP, fill=tk.X)

        self.canvas_scrollbar = ttk.Scrollbar(self.editor_frame, orient="horizontal",
                                            command=self.file_tab_canvas.xview)
        self.canvas_scrollbar.pack(side=tk.TOP, fill=tk.X)
        # self.canvas_scrollbar.pack_forget()
        self.file_tab_canvas.configure(xscrollcommand=self.canvas_scrollbar.set)

        self.tab_frame = tk.Frame(self.file_tab_canvas, bg=self.BLACK)
        self.file_tab_canvas.create_window((0,0), window=self.tab_frame, anchor="nw")
        self.canvas_scrollbar.pack_forget()

        self.editor_frame.bind("<Enter>", self.bind_mousewheel)
        self.editor_frame.bind("<Leave>", self.unbind_mousewheel)

        
        self.editor_content = tk.Frame(self.editor_frame)
        self.editor_content.pack(fill=tk.BOTH, expand=True)

        self.editor_content.bind("<Enter>", self.show_scrollbars)
        self.editor_content.bind("<Leave>", self.hide_scrollbars)

        # Line Numbers
        self.line_numbers = tk.Text(self.editor_content, width=4, padx=5, bg=self.BLACK, fg="#7bdc5e", state=tk.DISABLED, font=("Consolas", self.font_size))
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        self.line_numbers.bind("<MouseWheel>", self.on_mouse_wheel)
        self.line_numbers.config(yscrollcommand=self.sync_scroll)
        self.line_numbers.tag_configure("highlight", foreground="red")

        # Stylish Scrollbar Configuration
        self.style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background=self.CYAN, # cyan
            darkcolor=self.BLACK,
            lightcolor=self.BLACK,
            troughcolor=self.BLACK, # black
            bordercolor=self.BLACK, # black
            arrowcolor=self.BLACK, # black
            relief="flat",
            width=5  # Make it slightly thicker
        )

        self.style.map(
            "Vertical.TScrollbar",
            background=[('active', 'magenta')], # cyan
            arrowcolor=[('active', self.CYAN)]
        )
        
        self.style.configure(
            "Horizontal.TScrollbar",
            gripcount=0,
            background=self.CYAN, # cyan
            darkcolor=self.BLACK,
            lightcolor=self.BLACK,
            troughcolor=self.BLACK, # black
            bordercolor=self.BLACK, # black
            arrowcolor=self.BLACK, # black
            relief="flat",
            width=5  # Make it slightly thicker
        )

        self.style.map(
            "Horizontal.TScrollbar",
            background=[('active', 'magenta')], # cyan
            arrowcolor=[('active', self.CYAN)]
        )

        # Code Scrollbar
        self.scrollbar = ttk.Scrollbar(self.editor_content, orient="vertical",cursor="arrow")
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar.pack_forget()
        self.scrollbar.config(command=lambda *args: self.sync_scroll(*args))
        self.line_numbers.config(yscrollcommand=self.scrollbar.set)


        
        # Main Code Editor
        self.code_editor = tk.Text(
            self.editor_content, wrap=tk.NONE, undo=True, font=self.font_style, background=self.BLACK, foreground="white",
            insertbackground="white", yscrollcommand=lambda *args: (self.scrollbar.set(*args), self.sync_scroll(*args)),
        )
        self.code_editor.tag_configure("missing_module", underline=True, underlinefg="red", foreground="red")
        self.code_editor.tag_configure("definition_highlight", background="#ffff88", foreground="black")
        self.code_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.code_editor.tag_configure("current_line", 
                              borderwidth=1,
                              relief="ridge"
                              )  
        self.code_editor.tag_raise("current_line", "sel")
        for char in ['"', "'", "(", "{", "["]:
            self.code_editor.bind(char, self.wrap_selected_text, add="+")


        self.horizontal_scrollbar = ttk.Scrollbar(self.code_editor, orient="horizontal", cursor="arrow")
        self.horizontal_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.horizontal_scrollbar.pack_forget() 
        self.code_editor.config(xscrollcommand=self.horizontal_scrollbar.set)
        self.horizontal_scrollbar.config(command=lambda *args: self.code_editor.xview(*args))
        
        self.bg_label = tk.Label(self.code_editor, image=self.bg_photo, bg=self.BLACK)
        self.bg_label.place(relx=0.5, rely=0.5, anchor='center')
        self.bg_label.bind("<Button-1>", lambda e: self.code_editor.focus_set())
        self.code_editor.bind("<Control-s>", self.save_file)
        self.code_editor.bind("<MouseWheel>", lambda event: self.on_mouse_wheel(event))
        self.scrollbar.config(command=lambda *args: (self.code_editor.yview(*args), self.sync_scroll(*args)))
        self.editor_frame.pack_propagate(False) 
        self.code_editor.config(undo=True, maxundo=1000)

        
        self.suggestion_box = tk.Listbox(self.editor_content, bg=self.BLACK, fg="white", font=("Consolas", 14), height=6)
        self.suggestion_box.bind("<Return>", self.insert_suggestion)
        self.suggestion_box.bind("<<ListboxSelect>>", self.insert_suggestion)
        self.suggestion_box.bind("<Up>", self.navigate_suggestions)
        self.suggestion_box.bind("<Down>", self.navigate_suggestions)
        self.suggestion_box.bind("<Tab>", self.insert_suggestion)

        
        # Main Terminal
        self.terminal = tk.Text(self.terminal_frame, state="disabled", height=50, wrap=tk.WORD, font=("Consolas", 12), bg=self.BLACK, fg="red")
        self.terminal_label = tk.Label(self.close_button_frame, text="T E R M I N A L", fg="white", bg=self.BLACK, font=("Arial", 15, 'bold'))
        self.terminal_label.pack(fill="x", pady=0)
        self.terminal.pack(fill=tk.BOTH, expand=True)
        self.terminal.config(state="disabled")
        self.terminal.tag_config("output", foreground="yellow")
        self.terminal.tag_config("error", foreground="red")
        self.terminal.tag_config("ai", foreground="#00ff00")
        self.terminal.bind("<Control-C>", self.copy_terminal_text)
        self.terminal.bind("<Control-c>", self.copy_terminal_text)

        # Terminal Entry Box (Input)
        self.terminal_input = tk.Entry(self.terminal_frame, bg=self.TERMINAL_BG, fg=self.TERMINAL_FG, insertbackground="white", font=("Consolas", 14))
        self.terminal_input.pack(fill="x", padx=5, pady=5, ipady=5)
        self.terminal_input.bind("<Return>", self.execute_command)
        

        # Terminal Scrollbar
        self.terminal_scrollbar = ttk.Scrollbar(self.terminal, orient=tk.VERTICAL, command=self.terminal.yview, cursor='arrow')
        self.terminal.config(yscrollcommand=self.terminal_scrollbar.set)
        self.terminal_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Placeholder Item
        self.placeholder_item = self.file_tree.insert("", "end", text="", tags=("placeholder",))
        self.file_tree.tag_configure("placeholder", foreground=self.BLACK, background=self.BLACK)

        # Menu Bar
        self.menu_bar = tk.Menu(self.root, background=self.BLACK)
        self.root.config(menu=self.menu_bar)

        # File Menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0, background=self.CYAN)
        self.file_menu.add_command(label="Open File",accelerator='Ctrl+O', font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.open_file)
        self.file_menu.add_command(label="Open Folder",accelerator="Ctrl+Shift+O", font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.open_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save",accelerator="Ctrl+S", font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.save_file)
        self.file_menu.add_command(label="Save As",accelerator="Ctrl+Shift+S", font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.save_as_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", font=self.menu_bar_font_style, background=self.BLACK, foreground='red', command=self.exit_editor)

        # Edit Menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0, bg=self.CYAN)
        self.edit_menu.add_command(label="Undo",accelerator='Ctrl+Z', font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.safe_undo)
        self.edit_menu.add_command(label="Redo",accelerator='Ctrl+Y', font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.safe_redo)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut",accelerator='Ctrl+X', font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.cut_text)
        self.edit_menu.add_command(label="Copy",accelerator='Ctrl+C', font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.copy_text)
        self.edit_menu.add_command(label="Paste",accelerator='Ctrl+V', font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.paste_text)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Rename",accelerator='F2', font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.start_rename_via_shortcut)
        self.edit_menu.add_command(label="Search",accelerator='F3', font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.open_search_bar)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Zoom In",accelerator='Ctrl++', font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.increase_text_size)
        self.edit_menu.add_command(label="Zoom Out",accelerator=' Ctrl+-', font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.decrease_text_size)


        # Run Menu
        self.run_menu = tk.Menu(self.menu_bar, tearoff=0,bg=self.CYAN)
        self.run_menu.add_command(label="Run",accelerator='Alt+S', font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.run_code)
        self.run_menu.add_separator()
        self.run_menu.add_command(label="Stop Running... ",accelerator='Ctrl+Q', font=self.menu_bar_font_style, background='red', foreground='white', command=self.stop_code)

        
        # terminal menu 
        self.terminal_menu = tk.Menu(self.menu_bar,tearoff=0,bg=self.CYAN)
        self.terminal_menu.add_command(label="Show Terminal     ",accelerator='Ctrl+Shift+T', font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.reopen_terminal)
        self.terminal_menu.add_command(label="Clear Terminal    ",accelerator='Ctrl+Shift+C', font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.terminal_delete_clear)
        self.terminal_menu.add_separator()
        self.terminal_menu.add_command(label="New Terminal      ",accelerator='Ctrl+Shift+`', font=self.menu_bar_font_style, background=self.BLACK, foreground='white', command=self.open_new_terminal)


        # Theme Menu
        self.theme_menu = tk.Menu(self.menu_bar,tearoff=0,bg='black', foreground='white',font=self.menu_bar_font_style)
        self.theme_menu.add_command(label="Dark Blue    ",image=self.dark_blue_icon, compound='right',command=self.change_dark_blue_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Black        ",image=self.black_icon, compound='right',command=self.change_dark_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Dark Green   ",image=self.dark_green_icon, compound='right',command=self.change_dark_green_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Dark Gray    ",image=self.dark_gray_icon, compound='right',command=self.change_dark_gray_theme)


        # Menu Bar
        self.custom_menu_font = ("Consolas", 12)
        self.menu_bar.add_cascade(label="File", font=self.custom_menu_font, background=self.BLACK, foreground='white', menu=self.file_menu)
        self.menu_bar.add_cascade(label="Edit", font=self.custom_menu_font, background=self.BLACK, foreground='white', menu=self.edit_menu)
        self.menu_bar.add_cascade(label="Run", font=self.custom_menu_font, background=self.BLACK, foreground='white', menu=self.run_menu)
        self.menu_bar.add_cascade(label="Terminal", font=self.custom_menu_font, background=self.BLACK, foreground='white', menu=self.terminal_menu)
        self.menu_bar.add_cascade(label="Theme", font=self.custom_menu_font, background=self.BLACK, foreground='white', menu=self.theme_menu)
     



        # Bindings for code editor
        self.code_editor.bind("<KeyRelease>", lambda e: (self.update_line_numbers(), self.show_suggestions(e), self.on_text_change(e)))
        self.code_editor.bind("<KeyPress>", self.on_key_press)
        self.code_editor.bind("<Return>", self.update_line_numbers, add="+")
        self.code_editor.bind("<BackSpace>", self.update_line_numbers, add="+")
        self.code_editor.bind("<Delete>", self.update_line_numbers, add="+")
        self.code_editor.bind("<Configure>", self.update_line_numbers, add="+")
        self.code_editor.bind("<ButtonRelease-1>", lambda event: self.update_line_numbers())
        self.code_editor.bind("<Return>", self.auto_indent, add="+")
        self.code_editor.bind("<Return>", self.insert_selected_suggestion)
        self.code_editor.bind("<Return>", self.bg_label.place_forget())
        self.code_editor.bind("<Control-c>", self.copy_text)
        self.code_editor.bind("<Control-x>", self.cut_text)
        self.code_editor.bind("<Control-v>", self.on_paste)
        self.code_editor.bind("<Control-C>", self.copy_text)
        self.code_editor.bind("<Control-X>", self.cut_text)
        self.code_editor.bind("<Control-V>", self.on_paste)
        self.code_editor.bind("<<Paste>>", self.on_paste)
        self.code_editor.bind("<Control-slash>", self.toggle_comment)
        self.code_editor.bind("<MouseWheel>", self.on_mouse_wheel)
        self.code_editor.bind("<Shift-MouseWheel>", self.on_shift_mouse_wheel)
        self.code_editor.bind("<Double-Button-1>", self.select_word)
        self.code_editor.bind("<Double-Button-1>", self.select_word_inside_special_chars, add="+")
        self.code_editor.bind("<Return>", self.handle_enter, add="+")
        self.code_editor.bind("<Button-1>", lambda e: self.root.after(1, self.update_line_numbers))
        self.code_editor.bind("<Button-1>", self.deselect_all, add="+")
        self.code_editor.bind("<Escape>", lambda e: (self.suggestion_box.place_forget(), self.code_editor.focus_set()))
        self.code_editor.bind("<BackSpace>", self.on_backspace)
        self.code_editor.bind("<Control-BackSpace>", self.delete_word, add="+")
        self.code_editor.bind("<Control-Delete>", self.delete_next_word, add="+")
        self.code_editor.bind("<Control-a>", self.select_all)
        self.code_editor.bind("<Left>", self.move_cursor_after_selection)
        self.code_editor.bind("<Right>", self.move_cursor_after_selection)
        self.code_editor.bind("<Up>", lambda e: self.navigate_suggestions(e) if self.suggestion_box.winfo_ismapped() else self.move_cursor_after_selection(e))
        self.code_editor.bind("<Down>", lambda e: self.navigate_suggestions(e) if self.suggestion_box.winfo_ismapped() else self.move_cursor_after_selection(e))
        self.code_editor.bind("<Right>", self.skip_suggestion, add="+")
        self.code_editor.bind("<Up>", self.update_line_numbers, add="+")
        self.code_editor.bind("<Down>", self.update_line_numbers, add="+")
        self.code_editor.bind("<KeyRelease>", self.on_key_release)
        self.code_editor.bind("<Tab>", self.indent_selected_text)
        self.code_editor.bind("<Shift-Tab>", self.unindent_selected_text)
        self.code_editor.bind("<Control-Right>", self.move_to_next_word_boundary)
        self.code_editor.bind("<Control-Left>", self.move_to_previous_word_boundary)
        self.code_editor.bind("<Alt-Up>", lambda event: self.move_line("up"))
        self.code_editor.bind("<Alt-Down>", lambda event: self.move_line("down"))
        self.code_editor.bind("<Control-Shift-C>", self.terminal_delete_clear)
        self.code_editor.bind("<Control-Shift-c>", self.terminal_delete_clear)
        self.code_editor.bind("<Control-Shift-asciitilde>", self.open_new_terminal)
        self.code_editor.bind("<Control-Return>", self.insert_new_line_below)
        self.code_editor.bind("<Alt-Shift-Down>", self.duplicate_line)
        self.code_editor.bind("<Shift-Left>", lambda e: self.modify_selection("left", False))
        self.code_editor.bind("<Shift-Right>", lambda e: self.modify_selection("right", False))
        self.code_editor.bind("<Control-Shift-Left>", lambda e: self.modify_selection("left", True))
        self.code_editor.bind("<Control-Shift-Right>", lambda e: self.modify_selection("right", True))
        self.code_editor.bind("<Button-1>", self.handle_mouse_click)
        self.code_editor.after(1, self._highlight_syntax)
        self.code_editor.bind("<Control-Button-1>", self.jump_to_definition)
                

        # Keyboard Shortcuts
        self.root.bind("<Control-o>", self.open_file)
        self.root.bind("<Control-O>", self.open_file)
        self.root.bind("<Control-s>", self.save_file)
        self.root.bind("<Control-S>", self.save_file)
        self.root.bind("<Control-Shift-o>", self.open_folder)
        self.root.bind("<Control-Shift-O>", self.open_folder)
        self.root.bind("<KeyRelease>", self.on_text_change)
        self.root.bind("<Control-plus>", self.increase_text_size)
        self.root.bind("<Control-minus>", self.decrease_text_size)
        self.root.bind("<Control-equal>", self.increase_text_size)
        self.root.bind("<Shift-Tab>", self.shift_tab)
        self.root.bind("<Button-1>", self.check_click_outside_suggestion_box, add="+")
        self.root.bind("(", self.auto_complete)
        self.root.bind("[", self.auto_complete)
        self.root.bind("{", self.auto_complete)
        self.root.bind("'", self.auto_complete)
        self.root.bind('"', self.auto_complete)
        self.root.bind("<Double-Button-1>", self.select_word_inside_special_chars)
        self.root.bind("<Alt-s>", lambda event: self.run_code())
        self.root.bind("<Alt-S>", lambda event: self.run_code())
        self.root.bind("<F3>", self.open_replace_dialog)
        self.root.bind("<Control-q>", lambda event: self.stop_code())
        self.root.bind("<Alt-S>", lambda event: self.run_code())
        self.root.bind("<Control-Q>", lambda event: self.stop_code())
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.bind("<Control-x>", self.cut_items)
        self.root.bind("<Control-c>", self.copy_items)
        self.root.bind("<Control-v>", self.paste_items)
        self.root.bind("<Control-X>", self.cut_items)
        self.root.bind("<Control-C>", self.copy_items)
        self.root.bind("<Control-V>", self.paste_items)
        self.root.bind("<F6>", self.toggle_all_folders)
        self.root.bind("<Control-Shift-t>", self.reopen_terminal)
        self.root.bind("<Control-Shift-T>", self.reopen_terminal)
        self.root.bind("<Control-Shift-E>", self.toggle_sidebar)
        self.root.bind("<Control-Shift-e>", self.toggle_sidebar)
        self.root.bind("<Control-Shift-c>", self.terminal_delete_clear)
        self.root.bind("<Control-Shift-C>", self.terminal_delete_clear)
        self.root.bind("<Control-Shift-asciitilde>", self.open_new_terminal)
        self.root.bind("<F9>", self.open_search_bar)
    
    def show_scrollbars(self,event):
        self.horizontal_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def hide_scrollbars(self,event):
        self.horizontal_scrollbar.pack_forget()
        self.scrollbar.pack_forget()

    def on_close(self):
        self.save_window_geometry()
        self.stop_code()

        for process in self.active_processes:
            try:
                if sys.platform == "win32":
                    os.kill(process.pid, signal.CTRL_BREAK_EVENT)

                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.kill()
            except:
                pass

        if hasattr(self, 'backup_dir'):
            try:
                shutil.rmtree(self.backup_dir)
            except Exception as e:
                pass 
        
        self.stop_file_monitor() 
        if self.process:
            try:
                if sys.platform == "win32":
                    os.kill(self.process.pid, signal.CTRL_BREAK_EVENT)
                else:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.kill()
            except:
                pass
        self.root.destroy()
    
    def load_window_geometry(self):
        if os.path.exists(self.config_file):
            config = configparser.ConfigParser()
            config.read(self.config_file)
            if "Geometry" in config:
                geometry = config["Geometry"].get("size", "")
                state = config["Geometry"].get("state", "normal")
                if geometry:
                    self.root.geometry(geometry)
                    self.root.update_idletasks()
                    self.root.update()
                if state == "zoomed":
                    self.root.state("zoomed")  # Restore maximized state
                elif state == "iconic":
                    self.root.iconify()  # Restore minimized state

    def save_window_geometry(self):
        config = configparser.ConfigParser()
        config["Geometry"] = {
            "size": self.root.geometry(),
            "state": self.root.state()  # Save window state (normal, maximized, etc.)
        }
        with open(self.config_file, "w") as f:
            config.write(f)

    def open_file(self, event=None):
        file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            self.code_editor.delete("1.0", tk.END)
            self.code_editor.insert("1.0", content)
            self.root.title(f"VS Code Like Python Editor - {os.path.basename(file_path)}")
            self.filename_label.config(text=os.path.basename(file_path))
            self.current_file = file_path

            self.load_file(file_path)
            self.add_file_tab(file_path) 
            self.on_text_change()
            self.update_line_numbers()
            self.highlight_syntax()
            self.auto_save()

    def open_file_from_tree(self, event):

        if self.ctrl_shift_pressed_during_click:
            self.ctrl_shift_pressed_during_click = False  # Reset flag
            return 


        selected_items = self.file_tree.selection()
        if not selected_items:
            return

        for selected_item in selected_items:
            try:
                # Validate item existence
                if not self.file_tree.exists(selected_item):
                    continue
                    
                values = self.file_tree.item(selected_item, "values")
                if not values:
                    continue

                file_path = values[0]
                if os.path.isfile(file_path):
                    self.load_file(file_path)
                    self.add_file_tab(file_path) 
                    self.on_text_change()
                    self.update_line_numbers()
                    self.highlight_syntax()
                    self.file_selected = True
                    
                    self.root.after(1, self.auto_save)

            except tk.TclError as e:
                print(f"Ignoring invalid item: {str(e)}")
                continue
            
    def load_file(self, filepath):
        if not os.path.exists(filepath):
            self.terminal_output(f"[✖] File not found: {os.path.basename(filepath)}\n", error=True)
            self.close_tab(filepath)  # Close the invalid tab
            return
        self.current_file = filepath
        self.filename_label.config(text=os.path.basename(filepath))
        self.add_file_tab(filepath)  
    
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
            self.code_editor.delete("1.0", tk.END)
            self.code_editor.insert("1.0", content.rstrip())  # Remove trailing newlines
            self.code_editor.edit_reset()  # Reset undo/redo stack
            self.code_editor.edit_modified(False)  # Mark as unmodified
        except UnicodeDecodeError:
            self.terminal_output(f"[✖] Cannot open '{os.path.basename(filepath)}'...\n", error=True)

    def save_file(self, event=None):
        if self.current_file:
            with open(self.current_file, "w", encoding="utf-8") as file:
                file.write(self.code_editor.get("1.0", tk.END))
            self.code_editor.edit_modified(False)  

        else:
            self.save_as_file()
        
        return 'break'

    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        self.filename_label.config(text=os.path.basename(file_path))
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(self.code_editor.get("1.0", tk.END))
            self.current_file = file_path
            self.root.title(f"Python Editor - {os.path.basename(file_path)}")

    def auto_save(self, event=None):
        if not self.code_editor.edit_modified():  # Check if the text has changed
            return

        if self.current_file:
            try:
                with open(self.current_file, "w", encoding="utf-8") as file:
                    file.write(self.code_editor.get("1.0", tk.END))

            except Exception as e:
                pass

        self.root.after(500, self.auto_save)  # Auto-save every 500ms

    def update_layout(self):
        """Ensure scrollbar remains visible after resizing the font."""
        self.root.update_idletasks()

    def increase_text_size(self, event=None):
        """Increase font size and ensure scrollbar stays visible."""
        size = min(40, self.font_style[1] + 1)
        self.font_style = (self.font_style[0], size)
        self.code_editor.config(font=self.font_style)
        self.line_numbers.config(font=self.font_style)

        self.update_layout()

    def decrease_text_size(self, event=None):
        """Decrease font size and ensure scrollbar stays visible."""
        size = max(10, self.font_style[1] - 1)  # Prevent font size from going below 8
        self.font_style = (self.font_style[0], size)
        self.code_editor.config(font=self.font_style)
        self.line_numbers.config(font=self.font_style)

        self.update_layout()  # Keep scrollbar visible

    def select_all(self, event=None):
        self.code_editor.tag_add("sel", "1.0", tk.END)
        return "break"

    def deselect_all(self, event):
        """Deselect text when clicking outside."""
        self.code_editor.tag_remove("sel", "1.0", "end")

    def copy_text(self, event=None):
        try:
            # Check if any text is selected
            if self.code_editor.tag_ranges(tk.SEL):
                selected_text = self.code_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
            else:
                selected_text = ""  # If no text is selected, copy an empty string

            self.root.clipboard_clear()  # Clear clipboard
            self.root.clipboard_append(selected_text)  # Copy selected text (or empty string)
            self.root.update()  # Ensure clipboard updates
        except tk.TclError:
            pass  # Ignore errors (prevents crash)

        return "break"
    
    def copy_terminal_text(self, event=None):
        try:
            # Check if any text is selected
            if self.terminal.tag_ranges(tk.SEL):
                selected_text = self.terminal.get(tk.SEL_FIRST, tk.SEL_LAST)
            else:
                selected_text = ""  # If no text is selected, copy an empty string

            self.root.clipboard_clear()  # Clear clipboard
            self.root.clipboard_append(selected_text)  # Copy selected text (or empty string)
            self.root.update()  # Ensure clipboard updates
        except tk.TclError:
            pass  # Ignore errors (prevents crash)

        return "break"

    def cut_text(self, event=None):
        try:
            # Check if any text is selected
            if self.code_editor.tag_ranges(tk.SEL):
                selected_text = self.code_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                self.code_editor.delete(tk.SEL_FIRST, tk.SEL_LAST)  # Remove selected text
                self.root.update()
            else:
                self.cut_whole_line(event) 

            # self.root.update()  # Ensure clipboard updates
        except tk.TclError:
            pass  # Ignore errors (prevents crash)

        return "break"

    def paste_text(self, event=None):
        try:
            clipboard_text = self.root.clipboard_get()  # Get clipboard content
            if clipboard_text:
                self.code_editor.insert(tk.INSERT, clipboard_text)  # Insert at cursor
        except tk.TclError:
            pass  # Ignore error if clipboard is empty
        return "break"

    def exit_editor(self):
        self.root.quit()

    def highlight_syntax(self):
        if self.highlight_timer:
            self.root.after_cancel(self.highlight_timer)
        
        self.highlight_timer = self.root.after(200, self._highlight_syntax)

    def _highlight_syntax(self):

        if not hasattr(self, "_scroll_binding_added"):
            # self.code_editor.bind("<MouseWheel>", lambda e: self._highlight_syntax())
            self._scroll_binding_added = True

        # Get the visible region's start and end indices
        start_vis = self.code_editor.index("@0,0")
        end_vis = self.code_editor.index("@0,10000")
        first_visible_line = int(start_vis.split('.')[0])
        last_visible_line = int(end_vis.split('.')[0])

        # Define syntax elements and colors
        datatypes = {"str", "int", "float", "bool", "list", "tuple", "dict", "set", "complex", "bytes", "range", "enumerate"}
        keywords1 = {"for", "while", "if", "else", "elif", "try", "except", "finally", "break", "continue", "return", "import", "from", "as", "with", 'input', "lambda", "yield", "global", "nonlocal", "pass", "raise", 'do'}
        keywords2 = {"and", "or", "not", "is", "in", "def", 'print', "class", 'True', 'False', 'None', 'NOTE'}
        COLORS = self.syntax_colors

        # Remove previous tags only in the visible region
        tags_to_remove = [
            *COLORS.keys(), "number", "string", "comment",
            "comment_bracket", "import_text", "brown_bracket",
            "bracket_content"  # New tag for our brown content
        ]
        for tag in tags_to_remove:
            self.code_editor.tag_remove(tag, start_vis, end_vis)

        # Get visible text content
        visible_text = self.code_editor.get(start_vis, end_vis)

        # Highlight brackets
        for match in re.finditer(r'[\[\]{}()]', visible_text):
            start_pos = match.start()
            end_pos = match.end()
            start_idx = f"{start_vis}+{start_pos}c"
            end_idx = f"{start_vis}+{end_pos}c"
            self.code_editor.tag_add("bracket", start_idx, end_idx)

        # Highlight keywords and data types
        words = re.finditer(r'\b\w+\b', visible_text)
        bracket_stack = []
        for match in words:
            word = match.group()
            start_pos = match.start()
            end_pos = match.end()
            start_idx = f"{start_vis}+{start_pos}c"
            end_idx = f"{start_vis}+{end_pos}c"

            # Check if inside brackets (only considers visible region brackets)
            inside_bracket = any(start <= start_pos <= end for start, end in bracket_stack)
            if inside_bracket:
                continue  # Skip highlighting if inside brackets

            if word in datatypes:
                tag = "data_type"
            elif word in keywords1:
                tag = "keyword1"
            elif word in keywords2:
                tag = "keyword2"
            else:
                tag = "non_data_type"

            # Apply tag if not overlapping with brackets
            existing_tags = self.code_editor.tag_names(start_idx)
            if "bracket" not in existing_tags:
                self.code_editor.tag_add(tag, start_idx, end_idx)

        # Configure tag colors
        for tag, color in COLORS.items():
            self.code_editor.tag_configure(tag, foreground=color)

        # Highlight numbers
        numbers = r"\b\d+\b"
        for match in re.finditer(numbers, visible_text):
            start_pos = match.start()
            end_pos = match.end()
            start_idx = f"{start_vis}+{start_pos}c"
            end_idx = f"{start_vis}+{end_pos}c"
            self.code_editor.tag_add("number", start_idx, end_idx)
        self.code_editor.tag_config("number", foreground="#970fed")

        # Highlight strings
        # Triple-quoted strings
        triple_pattern = r"('''|\"\"\")(.*?)\1"
        for match in re.finditer(triple_pattern, visible_text, flags=re.DOTALL):
            start_pos, end_pos = match.span()
            start_idx = f"{start_vis}+{start_pos}c"
            end_idx = f"{start_vis}+{end_pos}c"
            self.code_editor.tag_add("string", start_idx, end_idx)
        # Single/double quoted strings
        string_pattern = r"(['\"])(.*?)\1"
        for match in re.finditer(string_pattern, visible_text, flags=re.DOTALL):
            start_pos, end_pos = match.span()
            start_idx = f"{start_vis}+{start_pos}c"
            end_idx = f"{start_vis}+{end_pos}c"
            if "string" not in self.code_editor.tag_names(start_idx):
                self.code_editor.tag_add("string", start_idx, end_idx)
        self.code_editor.tag_config("string", foreground="#c25507")

        # Highlight imports
        import_pattern = r"\b(?:from|import)\s+([\w\.]+)(?:\s*,\s*([\w\.]+))*"
        for match in re.finditer(import_pattern, visible_text):
            modules = match.groups()
            start_pos = match.start()
            for mod in modules:
                if mod:
                    mod_start = visible_text.find(mod, start_pos)
                    if mod_start != -1:
                        mod_end = mod_start + len(mod)
                        start_idx = f"{start_vis}+{mod_start}c"
                        end_idx = f"{start_vis}+{mod_end}c"
                        self.code_editor.tag_add("import_text", start_idx, end_idx)
        self.code_editor.tag_config("import_text", foreground="#05be1c")

        # Highlight comments
        for line_num in range(first_visible_line, last_visible_line + 1):
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.end"
            line_text = self.code_editor.get(line_start, line_end)
            comment_start = line_text.find('#')
            if comment_start != -1:
                start_idx = f"{line_num}.{comment_start}"
                end_idx = f"{line_num}.end"
                self.code_editor.tag_add("comment", start_idx, end_idx)
                # Check for brackets in comments
                for idx, char in enumerate(line_text[comment_start:], start=comment_start):
                    if char in "(){}[]":
                        bracket_idx = f"{line_num}.{idx}"
                        self.code_editor.tag_add("comment_bracket", bracket_idx, f"{bracket_idx}+1c")
        self.code_editor.tag_config("comment", foreground=self.syntax_colors["comment"])
        self.code_editor.tag_config("comment_bracket", foreground=self.syntax_colors["comment_bracket"])


        # brackets
        bracket_colors = ["yellow", "violet", self.CYAN, "#1d00e4", "orange", "magenta"]
        # Configure each bracket color tag
        for color in bracket_colors:
            self.code_editor.tag_configure(color, foreground=color)
        self.code_editor.tag_config("brown_bracket", foreground="#8B4513")

        # Process entire text up to visible end for accurate nesting
        initial_text  = self.code_editor.get("1.0", start_vis)
        bracket_pairs = {"(": ")", "{": "}", "[": "]"}
        stack = []
        for char in initial_text:
            if char in bracket_pairs:
                stack.append(char)
            elif char in bracket_pairs.values():
                if stack and bracket_pairs.get(stack[-1]) == char:
                    stack.pop()

        # Process visible area for nested brackets
        visible_text = self.code_editor.get(start_vis, end_vis)
        visible_stack = []  # Tracks positions of opening brackets in visible area

        for i, char in enumerate(visible_text):
            pos = f"{start_vis}+{i}c"
            current_tags = self.code_editor.tag_names(pos)
            
            # Skip if inside comment/string
            if 'comment' in current_tags or 'string' in current_tags or 'comment_bracket' in current_tags:
                if char in bracket_pairs or char in bracket_pairs.values():
                    self.code_editor.tag_add("brown_bracket", pos, f"{pos}+1c")
                continue

            if char in bracket_pairs:
                # Opening bracket in visible area
                stack.append(char)
                visible_stack.append((char, pos))
                level = len(stack) - 1  # Current depth before pushing
                color = bracket_colors[level % len(bracket_colors)]
                self.code_editor.tag_add(color, pos, f"{pos}+1c")
            elif char in bracket_pairs.values():
                if stack and bracket_pairs.get(stack[-1]) == char:
                    # Closing bracket matches
                    popped_char = stack.pop()
                    level_after_pop = len(stack)
                    if visible_stack and visible_stack[-1][0] == popped_char:
                        # Matching opening is in visible area
                        _, opening_pos = visible_stack.pop()
                        color = bracket_colors[level_after_pop % len(bracket_colors)]
                        self.code_editor.tag_add(color, pos, f"{pos}+1c")
                    else:
                        # Matching opening is outside visible area
                        color = bracket_colors[level_after_pop % len(bracket_colors)]
                        self.code_editor.tag_add(color, pos, f"{pos}+1c")

    def on_text_change(self, event=None):
        if hasattr(self, 'replace_dialog') and self.replace_dialog.winfo_exists():
            self.replace_dialog.highlight_matches()

        if self.update_timer:
            self.root.after_cancel(self.update_timer)
        
        self.update_timer = self.root.after(200, self._perform_updates)
        content = self.code_editor.get("1.0", "end-1c").strip()
        if content == "":
            self.bg_label.place(relx=0.5, rely=0.5, anchor='center')
        
        else:
            self.bg_label.place_forget()
        
        self.schedule_import_check()

        if hasattr(self, 'replace_dialog') and self.replace_dialog.winfo_exists():
            self.replace_dialog.highlight_matches()

    def _perform_updates(self):
        self.highlight_syntax()
        self.update_line_numbers()
        self.auto_save()
        self.check_for_errors()
        # Add this block for real-time search updates
        if hasattr(self, 'search_window') and self.search_window.winfo_exists():
            if self.text_search_entry.get().strip() != "Search":
                self.real_time_search()
    
    def get_line_column(self, index):
        line = self.code_editor.index(f"1.0+{index}c").split(".")
        return int(line[0]), int(line[1])

    def safe_undo(self, event=None):
        if not self.undo_stack:
            return
        
        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        
        if action['type'] == 'create':
            # Undo creation: delete the item
            path = action['path']
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e:
                self.terminal_output(f"Couldn't delete {path}\n", error=True)
                pass
            self.update_file_tree(self.folder_path)
            
        elif action['type'] == 'delete':
            # Undo deletion: restore from backup
            try:
                for entry in reversed(action['batch']):
                    shutil.move(entry['backup_path'], entry['original_path'])
                shutil.rmtree(action['backup_dir'])
            except Exception as e:
                self.terminal_output(f"Undo Error - {str(e)}\n",error= True)
            self.update_file_tree(self.folder_path)
    
    def safe_redo(self, event=None):
        if not self.redo_stack:
            return
        
        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        
        if action['type'] == 'create':
            # Redo creation: recreate item
            try:
                if action['is_directory']:
                    os.makedirs(action['path'], exist_ok=False)
                else:
                    with open(action['path'], 'w') as f:
                        f.write('')
            except Exception as e:
                self.terminal_output(f"Redo Error- {str(e)}\n",error=True)
            self.update_file_tree(self.folder_path)
            
        elif action['type'] == 'delete':
            # Redo deletion: delete again
            try:
                backup_root = tempfile.mkdtemp(prefix='editor_redo_')
                new_batch = []
                for entry in action['batch']:
                    new_backup = os.path.join(backup_root, os.path.basename(entry['original_path']))
                    shutil.move(entry['original_path'], new_backup)
                    new_batch.append({
                        'original_path': entry['original_path'],
                        'backup_path': new_backup
                    })
                self.undo_stack.append({
                    'type': 'delete',
                    'batch': new_batch,
                    'backup_dir': backup_root
                })
            except Exception as e:
                self.terminal_output(f"Redo Erro - {str(e)}\n",error= True)
                pass
            self.update_file_tree(self.folder_path)

    def on_key_press(self, event):
        """Force Tkinter to treat each keypress as a separate undo action."""
        self.code_editor.edit_separator()  # Ensure each keypress gets its own undo step

    def auto_indent(self, event=None):
        """Handles indentation when pressing Enter."""
        cursor_position = self.code_editor.index(tk.INSERT)
        line, col = map(int, cursor_position.split('.'))
        line_start = f"{line}.0"

        # Get text from line start to cursor position
        text_before_cursor = self.code_editor.get(line_start, cursor_position)

        # Extract current indentation
        current_indent = ""
        for char in text_before_cursor:
            if char in (" ", "\t"):
                current_indent += char
            else:
                break

        # If cursor is at line start, insert new line above
        if col == 0:
            self.code_editor.insert(line_start, "\n")
            return "break"

        # Check if text before cursor (ignoring whitespace) ends with ":"
        if text_before_cursor.strip().endswith(":"):
            # Add extra indentation for code blocks
            self.code_editor.insert(tk.INSERT, "\n" + current_indent + "\t")
        else:
            # Maintain existing indentation
            self.code_editor.insert(tk.INSERT, "\n" + current_indent)

        return "break"

    def sync_scroll(self, *args):
        """Syncs line numbers with text editor scrolling."""
        self.line_numbers.yview_moveto(self.code_editor.yview()[0])
        self.code_editor.yview_moveto(self.line_numbers.yview()[0])
        if args and args[0] in ("moveto", "scroll"):  # Ensure valid scroll commands
            self.code_editor.yview(*args)
            self.line_numbers.yview(*args)
        else:
            self.line_numbers.yview_moveto(self.code_editor.yview()[0])  # Move line numbers with text editor
        self.highlight_syntax()

    def on_mouse_wheel(self, event):
        """Sync mouse wheel scrolling for both text editor and line numbers."""
        self.code_editor.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.line_numbers.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def shift_tab(self, event=None):
        cursor_position = self.code_editor.index(tk.INSERT)
        line_content = self.code_editor.get(cursor_position + " linestart", cursor_position)

        if line_content.startswith("    "):  # If line starts with indentation
            self.code_editor.delete(cursor_position + " linestart", cursor_position + " linestart + 4 chars")
        return "break"

    def auto_complete(self, event):
        pairs = {"(": ")", "[": "]", "{": "}", "'": "'", '"': '"'}
        char = event.char
        if char in pairs:
            self.code_editor.insert(tk.INSERT, pairs[char])
            self.code_editor.mark_set("insert", "insert-1c")
        return "break"

    def toggle_comment(self, event=None):
        # Check if there is a selection
        if self.code_editor.tag_ranges("sel"):
            start_index = self.code_editor.index("sel.first")
            end_index = self.code_editor.index("sel.last")
        else:
            start_index = self.code_editor.index("insert linestart")
            end_index = self.code_editor.index("insert lineend")

        # Determine start and end lines
        start_line = int(start_index.split('.')[0])
        end_line = int(end_index.split('.')[0])

        # Check if all selected lines are commented
        all_commented = True
        for line_num in range(start_line, end_line + 1):
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.end"
            line_content = self.code_editor.get(line_start, line_end).lstrip()
            if line_content and not line_content.startswith(('# ', '#')):
                all_commented = False
                break

        # Toggle comments for each line
        for line_num in range(start_line, end_line + 1):
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.end"
            line_content = self.code_editor.get(line_start, line_end)
            indentation = len(line_content) - len(line_content.lstrip())
            content_part = line_content[indentation:]

            if line_content.strip():
                if all_commented:
                    # Uncomment
                    if content_part.startswith("# "):
                        new_line = line_content[:indentation] + content_part[2:]
                    elif content_part.startswith("#"):
                        new_line = line_content[:indentation] + content_part[1:]
                    else:
                        new_line = line_content
                else:
                    # Comment
                    new_line = line_content[:indentation] + "# " + line_content[indentation:]
            else:
                new_line = line_content  # Empty line

            # Replace the line
            self.code_editor.delete(line_start, line_end)
            self.code_editor.insert(line_start, new_line)

        # Re-apply the original selection if it existed
        if self.code_editor.tag_ranges("sel"):
            self.code_editor.tag_add("sel", start_index, end_index)
        
        return "break"

    def deselect_and_move_cursor(self, event):
        """Deselects text and moves cursor properly."""
        if self.code_editor.tag_ranges("sel"):
            selection_start = self.code_editor.index("sel.first")
            selection_end = self.code_editor.index("sel.last")

            # Handle full text selection (Ctrl+A)
            if selection_start == "1.0" and selection_end == self.code_editor.index("end-1c"):
                if event.keysym == "Left":
                    self.code_editor.mark_set(tk.INSERT, "1.0")  # Move to start
                elif event.keysym == "Right":
                    self.code_editor.mark_set(tk.INSERT, "end")  # Move to end
            else:
                # Move cursor based on arrow key
                if event.keysym == "Right":
                    self.code_editor.mark_set(tk.INSERT, selection_end)
                elif event.keysym == "Left":
                    self.code_editor.mark_set(tk.INSERT, selection_start)

            self.code_editor.tag_remove("sel", "1.0", "end")  # Remove selection
            self.code_editor.config(insertontime=500)  # Restore cursor visibility
            return "break"

    def select_word_inside_special_chars(self, event):
        """Selects only the word inside surrounding special characters, ignoring dots and special symbols."""
        cursor_index = self.code_editor.index(tk.CURRENT)
        cursor_line, cursor_col = map(int, cursor_index.split("."))

        # Get the full line text
        line_start = f"{cursor_line}.0"
        line_end = f"{cursor_line}.end"
        line_text = self.code_editor.get(line_start, line_end)

        # Find all words surrounded by special characters
        matches = list(re.finditer(r'[^a-zA-Z0-9_]?([a-zA-Z0-9_]+)[^a-zA-Z0-9_]?', line_text))

        # Check if cursor is inside a valid word
        for match in matches:
            text_start, text_end = match.span(1)  # Get the inside word position

            if text_start <= cursor_col < text_end:
                actual_start = f"{cursor_line}.{text_start}"
                actual_end = f"{cursor_line}.{text_end}"

                self.code_editor.tag_remove("sel", "1.0", tk.END)  # Clear previous selection
                self.code_editor.tag_add("sel", actual_start, actual_end)  # Select only the word
                return "break"

        return None  # Allow normal selection outside special characters

    def run_code(self):
        if not self.vertical_pane.panes() or self.terminal_frame not in self.vertical_pane.panes():
            self.vertical_pane.add(self.terminal_frame, height=270)  # Reopen terminal

        # Use saved file if available and valid
        if self.current_file and self.current_file.endswith(".py") and os.path.exists(self.current_file):
            script_path = self.current_file
            self.terminal_output(f"Running saved file: {os.path.basename(script_path)}...\n", error=False)
        else:
            # Create temp file only for unsaved/new files
            if self.current_file and not self.current_file.endswith(".py"):
                self.terminal_output(f"Cannot run: {os.path.basename(self.current_file)} | (Only Python files can be executed)\n", error=True)
                return
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                script_path = temp_file.name
                temp_file.write(self.code_editor.get("1.0", tk.END))
            self.terminal_output(f"Running temporary file: {os.path.basename(script_path)}...\n", error=False)

        # Rest of the existing process handling remains the same
        if self.process:
            self.terminal_output("A process is already running. Stop it first!\nPlease press Ctrl+Q to Stop the Code\n", error=True)
            return

        # Windows-specific setup to prevent new windows
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        self.stop_button.pack(side=tk.RIGHT, padx=5, pady=5)  # Show stop button
        self.run_button.pack_forget() 
        self.terminal_input.config(state='disabled')  # Disable terminal input

        # 🔥 Determine working directory:
        if self.folder_path and self.current_file and self.current_file.startswith(self.folder_path):
            working_directory = self.folder_path
        elif self.current_file:
            working_directory = os.path.dirname(self.current_file)
        else:
            working_directory = os.getcwd()  # fallback

        try:
            self.process = subprocess.Popen(
                ['python',"-u", script_path],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=0,
                cwd=working_directory,
                startupinfo=startupinfo,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            )
            self.active_processes.append(self.process) 
        except Exception as e:
            self.terminal_output(f"Failed to start process: {e}\n", error=True)
            self.process = None
            self.stop_code()
            return

        # Start threads to read stdout and stderr
        threading.Thread(target=self.read_output_stream, args=(self.process.stdout, False), daemon=True).start()
        threading.Thread(target=self.read_output_stream, args=(self.process.stderr, True), daemon=True).start()

        # Start a periodic check for process completion
        self.check_process_status()

    def terminal_output(self, text, error=False):
        """Updates the terminal with new text."""
        self.terminal.config(state="normal")
        error_pattern = re.compile(r'File "(.*?)", line (\d+)')
        start_index = self.terminal.index("end-1c")
        self.terminal.insert("end", text, "error" if error else "output")
        for match in error_pattern.finditer(text):
            file_path, line_number = match.groups()
            
            # Store line number and file path for later use
            tag_name = f"error_{line_number}"
            self.terminal.tag_add(tag_name, f"{start_index} linestart", "end")
            self.terminal.tag_config(tag_name, foreground="red", underline=True)
            
            # Bind click event to navigate to the error line
            self.terminal.tag_bind(tag_name, "<Control-Button-1>", lambda e, ln=line_number: self.goto_error_line(ln))

        self.terminal.see(tk.END)  # Auto-scroll to the end
        self.terminal.config(state="disabled")

    def goto_error_line(self, line_number):
        """Moves cursor to the specified error line in the code editor."""
        try:
            line_index = f"{line_number}.0"
            self.code_editor.mark_set("insert", line_index)
            self.code_editor.see(line_index)  # Scroll to the line
            self.code_editor.focus_set()
            
            # Highlight the error line temporarily
            self.code_editor.tag_add("error_highlight", line_index, f"{line_number}.end")
            self.code_editor.tag_config("error_highlight", background="darkred")

            # Remove highlight after a short delay
            self.root.after(1000, lambda: self.code_editor.tag_remove("error_highlight", line_index, f"{line_number}.end"))

        except Exception as e:
            print(f"Error navigating to line {line_number}: {e}")

    def stop_code(self):
        """Terminate all processes and their child processes forcefully"""
        for process in self.active_processes:
            try:
                if process.poll() is None:  # Check if process is alive
                    if sys.platform == "win32":
                        # Kill entire process tree on Windows
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    else:
                        # Unix: Kill process group
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    process.kill()
            except Exception as e:
                pass
        self.active_processes.clear()  # Clear the list
        
        # GUI cleanup
        self.stop_button.pack_forget()
        self.run_button.pack(side=tk.RIGHT, padx=5, pady=5)
        self.terminal_input.config(state='normal')
        self.root.config(cursor="")

    def update_file_tree(self, path, parent="",restore_expanded=True):
        if not path:
            return
        expanded_paths = self.get_expanded_paths() if restore_expanded else set()

        if parent == "":
            self.file_tree.delete(*self.file_tree.get_children())

        
        # was_expanded = self.file_tree.item(parent, "open") if parent else False
        self.file_tree.delete(*self.file_tree.get_children(parent))

        if not os.path.exists(path):
            return


        # Separate folders and files
        items = os.listdir(path)
        folders = []
        files = []

        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                folders.append(item)
            else:
                files.append(item)

        # Sort case-insensitively
        folders = sorted(folders, key=lambda x: x.lower())
        files = sorted(files, key=lambda x: x.lower())

        # Add folders first
        for item in folders:
            full_path = os.path.join(path, item)
            folder_node = self.file_tree.insert(
                parent, "end", 
                text=" " + item,
                image=self.folder_icon,
                values=[full_path],
                open=False,
                tags=("folder",)
            )
            self.update_file_tree(full_path, folder_node)

        # Add files with proper icons
        for item in files:
            full_path = os.path.join(path, item)
            file_ext = os.path.splitext(item)[1].lower()
            
            if file_ext == ".py":
                icon = self.python_icon
                tags = ("file", "python")
            elif file_ext == ".html":
                icon = self.html_icon
                tags = ("file", "html")
            elif file_ext == ".css":
                icon = self.css_icon
                tags = ("file", "css")
            elif file_ext == ".js":
                icon = self.js_icon
                tags = ("file", "js")
            elif file_ext == ".png":
                icon = self.png_icon
                tags = ("file", "png")
            elif file_ext == ".jpg":
                icon = self.jpg_icon
                tags = ("file", "jpg")
            elif file_ext == ".ico":
                icon = self.ico_icon
                tags = ("file", "ico")
            elif file_ext == ".csv":
                icon = self.csv_icon
                tags = ("file", "csv")
            elif file_ext == ".pyc":
                icon = self.pyc_icon
                tags = ("file", "pyc")
            elif file_ext == ".db":
                icon = self.db_icon
                tags = ("file", "db")
            elif file_ext == ".c":
                icon = self.c_icon
                tags = ("file", "c")
            elif file_ext == ".cpp":
                icon = self.cpp_icon
                tags = ("file", "cpp")
            elif file_ext == ".cs":
                icon = self.cserp_icon
                tags = ("file", "cs")
            else:
                icon = self.file_icon
                tags = ("file",)

            self.file_tree.insert(
                parent, "end",
                text=" " + item,
                image=icon,
                values=[full_path],
                tags=tags
            )

        # Add empty folder placeholder if needed
        if not folders and not files:
            self.file_tree.insert(parent, "end", text="(Empty Folder)", values=[""], tags=("placeholder",))

        
        if restore_expanded:
            self.restore_expanded_paths(expanded_paths)

    def execute_command(self, event=None):
        command = self.terminal_input.get().strip()
        self.terminal_input.delete(0, tk.END)

        if self.process:
            # If a process is running, send the input to its stdin
            try:
                self.process.stdin.write(command + "\n")
                self.process.stdin.flush()
                self.terminal_input.config(state='disabled')             
                
            except Exception as e:
                self.terminal_output(f"Error sending input to process: {e}\n", error=True)
            return 'break'
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        if command.lower() == "cls":
            self.terminal.config(state="normal")
            self.terminal.delete("1.0", tk.END)
            self.terminal.insert("end", "Terminal Cleared...\n")
            self.terminal.config(state="disabled")
            return 'break'

        self.terminal_output(f">>> {command}\n", error=False)
        self.run_button.pack_forget()
        self.stop_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # Working Directory Logic
        if self.folder_path and os.path.exists(self.folder_path):
            working_directory = self.folder_path
        else:
            working_directory = os.getcwd()

        

        try:
            # If no process is running, execute the command in a new shell
            self.process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=working_directory, 
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW 
            )
            self.active_processes.append(self.process)  
        except Exception as e:
            self.terminal_output(f"Failed to run command: {e}\n", error=True)
            return 'break'

        # Start a thread to read the output
        threading.Thread(target=self.read_terminal_output, daemon=True).start()
        

        return 'break'

    def read_terminal_output(self):
        try:
            while self.process and self.process.poll() is None:
                # Read stdout and stderr line by line
                stdout_line = self.process.stdout.readline()
                stderr_line = self.process.stderr.readline()

                if stdout_line:
                    self.terminal_output(stdout_line, error=False)
                if stderr_line:
                    self.terminal_output(stderr_line, error=True)

            # Read any remaining output after process ends
            if self.process:
                remaining_stdout = self.process.stdout.read()
                remaining_stderr = self.process.stderr.read()

                if remaining_stdout:
                    self.terminal_output(remaining_stdout, error=False)
                if remaining_stderr:
                    self.terminal_output(remaining_stderr, error=True)

        except Exception as e:
            self.terminal_output(f"Error reading output: {e}\n", error=True)

        finally:
            self.process = None

    def open_folder(self, event=None, path=None):
        # Get default directory (user's Desktop)
        default_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        
        if not path:
            # Use system file dialog with proper starting directory
            path = filedialog.askdirectory(
                title="Select Folder to Open",
                initialdir=default_dir,
                mustexist=True
            )

        if path and os.path.isdir(path):
            self.folder_path = os.path.abspath(path)
            self.file_tree.delete(*self.file_tree.get_children())
            self.update_file_tree(self.folder_path)
            folder_name = os.path.basename(path)
            self.folder_name_label.config(text=self.truncate_folder_name(folder_name), 
                                        fg='#ffff00', font=self.font_style)
            self.folder_name_label.config(font='bold')
            self.start_file_monitor()
            self.root.focus_set()

    def select_file(self, file_path):
        """Call this function when selecting a file from the file tree"""
        self.current_file = file_path
        self.file_selected = True  # Enable auto-save only after selecting a file

        # Load file contents into the editor
        with open(self.current_file, "r", encoding="utf-8") as file:
            self.code_editor.delete("1.0", tk.END)
            self.code_editor.insert("1.0", file.read())
        self.root.after(5, self.auto_save)

    def update_line_numbers(self, event=None):
        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.delete("1.0", tk.END)

        total_lines = int(self.code_editor.index("end-1c").split(".")[0])
        cursor_line = int(self.code_editor.index(tk.INSERT).split(".")[0])

        self.code_editor.tag_remove("current_line", "1.0", tk.END)
        self.code_editor.tag_add("current_line", f"{cursor_line}.0", f"{cursor_line}.end+1c")

        # Generate line numbers
        line_text = "\n".join(str(i) for i in range(1, total_lines + 1))
        self.line_numbers.insert("1.0", line_text)

        # Highlight the current line number
        self.line_numbers.tag_remove("highlight", "1.0", tk.END)
        self.line_numbers.tag_add("highlight", f"{cursor_line}.0", f"{cursor_line}.end")

        # Adjust line number width dynamically
        max_line_digits = len(str(total_lines))
        new_width = max(4, max_line_digits + 2)  # Ensure at least 4 width
        self.line_numbers.config(width=new_width)

        self.line_numbers.config(state=tk.DISABLED)

        # if not self.is_cursor_visible():
        #     self.code_editor.see(tk.INSERT)

        self.sync_scroll()  # Ensure scrolling is synced
        # self.line_numbers.config(state=tk.DISABLED)
        self.root.after(1, self.auto_save)

    def is_cursor_visible(self):
        # Get the bounding box of the cursor position
        bbox = self.code_editor.bbox(tk.INSERT)
        
        # If bbox exists, the cursor is visible in the viewport
        return bbox is not None

    def fuzzy_match(self, typed_word, suggestions):
        """Find words that match `typed_word`, even if letters are missing."""
        if not typed_word or not suggestions:
            return []

        typed_word_lower = typed_word.lower()

        # Prioritize words containing the typed letters in order
        matches = [word for word in suggestions if typed_word_lower in word.lower()]

        # If no direct substring match, fall back to closest matches
        if not matches:
            matches = difflib.get_close_matches(typed_word, suggestions, n=10, cutoff=0.4)

        return matches if matches else suggestions

    def on_shift_mouse_wheel(self, event):
        """Enables horizontal scrolling when Shift + Mouse Wheel is used."""
        self.code_editor.xview_scroll(-1 * (event.delta // 120), "units")
        return "break"

    def show_suggestions(self, event):

        # Add this at the beginning of the method
        if getattr(sys, 'frozen', False):
            from jedi.api.environment import get_default_environment
            env = get_default_environment()
            script = jedi.Script(
                code=self.code_editor.get("1.0", tk.END),
                path=self.current_file or 'temp.py',
                environment=env
            )
        else:
            script = jedi.Script(code=self.code_editor.get("1.0", tk.END))

        if event.keysym in ["Up", "Down", "Return", "Tab", "Right"]:
            return

        cursor_pos = self.code_editor.index(tk.INSERT)

        try:
            line, col = map(int, cursor_pos.split("."))
        except ValueError:
            return

        text = self.code_editor.get("1.0", tk.END).strip()
        lines = text.split("\n")

        if not text or line > len(lines):
            return

        if line <= len(lines):
            max_col = len(lines[line - 1])  # Max column = line length
            if col > max_col:
                return

        # Check if the last character before the cursor is a dot
        if col > 0 and self.code_editor.get(f"{line}.{col - 1}") == ".":
            self.typed_word = ""
            for i in range(col - 2, -1, -1):  # Start from the character before the dot
                char = self.code_editor.get(f"{line}.{i}")
                if char.isalnum() or char == "_":
                    self.typed_word = char + self.typed_word
                else:
                    break

            try:
                # script = jedi.Script(text)
                completions = script.complete(line, col)
                all_matches = [c.name for c in completions] if completions else []

                # **Apply fuzzy matching**
                matches = self.fuzzy_match(self.typed_word, all_matches)

                if matches:
                    self.suggestion_box.delete(0, tk.END)
                    for word in matches:
                        self.suggestion_box.insert(tk.END, word)

                    # Get the cursor's bounding box relative to the code editor
                    bbox = self.code_editor.bbox(tk.INSERT)
                    if bbox:
                        x, y, _, _ = bbox

                        # Get the code editor's position relative to the main window
                        editor_x = self.code_editor.winfo_x()
                        editor_y = self.code_editor.winfo_y()

                        # Calculate the absolute position of the suggestion box
                        abs_x = editor_x + x + 10  # Add padding
                        abs_y = editor_y + y + 30  # Add padding

                        # Ensure the suggestion box stays within the code editor's bounds
                        editor_width = self.code_editor.winfo_width()
                        editor_height = self.code_editor.winfo_height()

                        # Adjust if the suggestion box goes out of the editor's right edge
                        if abs_x + self.suggestion_box.winfo_reqwidth() > editor_x + editor_width:
                            abs_x = editor_x + editor_width - self.suggestion_box.winfo_reqwidth()

                        # Adjust if the suggestion box goes out of the editor's bottom edge
                        if abs_y + self.suggestion_box.winfo_reqheight() > editor_y + editor_height:
                            abs_y = editor_y + y - self.suggestion_box.winfo_reqheight() - 30  # Move above the cursor

                        # Place the suggestion box
                        self.suggestion_box.place(x=abs_x - editor_x, y=abs_y - editor_y)
                        self.suggestion_box.config(height=min(len(matches), 10))
                        self.suggestion_box.select_set(0)
                else:
                    self.suggestion_box.place_forget()

            except Exception as e:
                print("Jedi Error:", e)
                self.suggestion_box.place_forget()
        else:
            self.typed_word = ""
            for i in range(col - 1, -1, -1):
                char = self.code_editor.get(f"{line}.{i}")
                if char.isalnum() or char == "_":
                    self.typed_word = char + self.typed_word
                else:
                    break

            try:
                # script = jedi.Script(text)
                completions = script.complete(line, col)
                all_matches = [c.name for c in completions] if completions else []

                # **Apply fuzzy matching**
                matches = self.fuzzy_match(self.typed_word, all_matches)

                if matches:
                    self.suggestion_box.delete(0, tk.END)
                    for word in matches:
                        self.suggestion_box.insert(tk.END, word)

                    # Get the cursor's bounding box relative to the code editor
                    bbox = self.code_editor.bbox(tk.INSERT)
                    if bbox:
                        x, y, _, _ = bbox

                        # Get the code editor's position relative to the main window
                        editor_x = self.code_editor.winfo_x()
                        editor_y = self.code_editor.winfo_y()

                        # Calculate the absolute position of the suggestion box
                        abs_x = editor_x + x + 10  # Add padding
                        abs_y = editor_y + y + 30  # Add padding

                        # Ensure the suggestion box stays within the code editor's bounds
                        editor_width = self.code_editor.winfo_width()
                        editor_height = self.code_editor.winfo_height()

                        # Adjust if the suggestion box goes out of the editor's right edge
                        if abs_x + self.suggestion_box.winfo_reqwidth() > editor_x + editor_width:
                            abs_x = editor_x + editor_width - self.suggestion_box.winfo_reqwidth()

                        # Adjust if the suggestion box goes out of the editor's bottom edge
                        if abs_y + self.suggestion_box.winfo_reqheight() > editor_y + editor_height:
                            abs_y = editor_y + y - self.suggestion_box.winfo_reqheight() - 30  # Move above the cursor

                        # Place the suggestion box
                        self.suggestion_box.place(x=abs_x - editor_x, y=abs_y - editor_y)
                        self.suggestion_box.config(height=min(len(matches), 10))
                        self.suggestion_box.select_set(0)
                else:
                    self.suggestion_box.place_forget()

            except Exception as e:
                print("Jedi Error:", e)
                self.suggestion_box.place_forget()

    def on_backspace(self, event):
        self.root.after(1, lambda: (self.update_line_numbers(), self.code_editor.see(tk.INSERT)))

    def handle_enter(self, event):
        """Handles both auto-indent and inserting suggestions when Enter is pressed."""
        if self.suggestion_box.winfo_ismapped():  # If suggestions are visible
            self.insert_suggestion(event)  # Insert selected suggestion
        else:
            self.auto_indent(event)  # Otherwise, perform auto-indent

        self.root.after(1, self.update_line_numbers)  # Ensure line number update after insertion

        self.code_editor.see(tk.INSERT)
        self.root.after(1, self.auto_save)

        return "break"

    def insert_suggestion(self, event=None):
        """Inserts the selected suggestion into the text editor."""
        if self.suggestion_box.winfo_ismapped():
            selected_index = self.suggestion_box.curselection()
            if selected_index:
                selected_word = self.suggestion_box.get(selected_index)

                cursor_pos = self.code_editor.index(tk.INSERT)
                line, col = map(int, cursor_pos.split("."))
                start_pos = f"{line}.{col - len(self.typed_word)}"

                self.code_editor.delete(start_pos, tk.INSERT)
                self.code_editor.insert(tk.INSERT, selected_word)
                self.suggestion_box.place_forget()
                self.code_editor.focus_set()

                return "break"

        return  # Default behavior if no suggestion is selected

    def navigate_suggestions(self, event):
        """Navigates suggestions if suggestion box is visible."""
        if self.suggestion_box.winfo_ismapped():
            selected_index = self.suggestion_box.curselection()
            if event.keysym == "Down":
                if selected_index:
                    index = selected_index[0]
                    if index < self.suggestion_box.size() - 1:
                        self.suggestion_box.select_clear(index)
                        self.suggestion_box.select_set(index + 1)
                        self.suggestion_box.activate(index + 1)
                        self.suggestion_box.see(index + 1)
                else:
                    self.suggestion_box.select_set(0)
                    self.suggestion_box.activate(0)
                    self.suggestion_box.see(0)
                return "break"

            elif event.keysym == "Up":
                if selected_index:
                    index = selected_index[0]
                    if index > 0:
                        self.suggestion_box.select_clear(index)
                        self.suggestion_box.select_set(index - 1)
                        self.suggestion_box.activate(index - 1)
                        self.suggestion_box.see(index - 1)
                    else:
                        # If at the top, move selection to the last item
                        self.suggestion_box.select_clear(index)
                        self.suggestion_box.select_set(self.suggestion_box.size() - 1)
                        self.suggestion_box.activate(self.suggestion_box.size() - 1)
                        self.suggestion_box.see(self.suggestion_box.size() - 1)
                else:
                    # If no selection, move to the last item
                    self.suggestion_box.select_set(self.suggestion_box.size() - 1)
                    self.suggestion_box.activate(self.suggestion_box.size() - 1)
                    self.suggestion_box.see(self.suggestion_box.size() - 1)
                return "break"

        return  # Allow normal arrow key behavior if suggestion box is hidden
    
    def skip_suggestion(self, event):
        """Closes suggestion box and moves cursor to the right."""
        if self.suggestion_box.winfo_ismapped():
            self.suggestion_box.place_forget()

        cursor_pos = self.code_editor.index(tk.INSERT)
        line, col = map(int, cursor_pos.split("."))
        line_text = self.code_editor.get(f"{line}.0", f"{line}.end")

        if col < len(line_text):
            self.code_editor.mark_set(tk.INSERT, f"{line}.{col + 1}")

        return "break"

    def on_paste(self, event):
        """Update line numbers after pasting text."""
        self.bg_label.place_forget()
        self.code_editor.after(1, self.update_line_numbers)  # Ensure line number update after pasting
        self.code_editor.after(1, self.highlight_syntax)  # Ensure line number update after pasting
        self.root.after(1, self.auto_save)

        return None  # Allow normal paste behavior

    def delete_word(self, event):
        """Deletes the previous word or special character when Ctrl+Backspace is pressed and updates line numbers."""
        cursor_pos = self.code_editor.index(tk.INSERT)
        line, col = map(int, cursor_pos.split("."))

        if line == 1 and col == 0:
            return "break"  # Prevent deleting beyond the first line

        text_before_cursor = self.code_editor.get(f"{line}.0", f"{line}.{col}")

        if col == 0:
            # If at the start of a line, merge with the previous line
            prev_line_length = len(self.code_editor.get(f"{line-1}.0", f"{line-1}.end"))
            self.code_editor.delete(f"{line-1}.{prev_line_length}", f"{line}.0")
            self.code_editor.mark_set(tk.INSERT, f"{line-1}.{prev_line_length}")
        else:
            word_end = col  # Start at the cursor position

            # Step 1: Skip over spaces
            while word_end > 0 and text_before_cursor[word_end - 1] == " ":
                word_end -= 1

            # Get character before the new position
            prev_char = text_before_cursor[word_end - 1] if word_end > 0 else ""

            # Step 2: Delete based on the character type
            if prev_char.isalnum() or prev_char == "_":
                # If it's part of a word, delete the whole word
                while word_end > 0 and (text_before_cursor[word_end - 1].isalnum() or text_before_cursor[word_end - 1] == "_"):
                    word_end -= 1
            else:
                # If it's a special character, delete just that one character
                word_end -= 1

            self.code_editor.delete(f"{line}.{word_end}", f"{line}.{col}")

        # **Update line numbers after deletion**
        self.root.after(1, self.update_line_numbers)

        return "break"

    def delete_next_word(self, event):
        """Deletes the next word or special character when Ctrl+Delete is pressed and updates line numbers."""
        cursor_pos = self.code_editor.index(tk.INSERT)  # Get cursor position
        line, col = map(int, cursor_pos.split("."))

        text_after_cursor = self.code_editor.get(cursor_pos, f"{line}.end")  # Text after cursor

        if not text_after_cursor.strip():  # If nothing after cursor, merge next line
            next_line_text = self.code_editor.get(f"{line+1}.0", f"{line+1}.end")
            self.code_editor.delete(f"{line}.end", f"{line+1}.0")  # Merge next line up
            return "break"

        # Define special characters
        special_chars = r",./<>?;':\"[\]{}\\|/*\-+=)(*&^%$#@!~`"
        escaped_special_chars = re.escape(special_chars)

        # Match next word or individual special character
        match = re.match(rf"(\s*[\w_]+|\s*[{escaped_special_chars}])", text_after_cursor)

        if match:
            end_pos = f"{cursor_pos}+{match.end()}c"  # End position of match
            self.code_editor.delete(cursor_pos, end_pos)  # Delete the found part

        # **Update line numbers after deletion**
        self.root.after(1, self.update_line_numbers)

        return "break"

    def move_cursor_after_selection(self, event):
        """Moves cursor based on arrow key direction after selection."""
        if self.code_editor.tag_ranges("sel"):
            selection_start = self.code_editor.index("sel.first")
            selection_end = self.code_editor.index("sel.last")

            if event.keysym in ["Right", "Down"]:
                self.code_editor.mark_set(tk.INSERT, selection_end)  # Move to end
                self.root.after(1, self.update_line_numbers)
            elif event.keysym in ["Left", "Up"]:
                self.code_editor.mark_set(tk.INSERT, selection_start)  # Move to start
                self.root.after(1, self.update_line_numbers)

            self.code_editor.tag_remove("sel", "1.0", tk.END)  # Deselect text
            return "break"

    def insert_selected_suggestion(self, event):
        """Inserts the selected suggestion when Enter is pressed, preventing a new line if suggestions are open."""
        if self.suggestion_box.winfo_ismapped():  # If suggestion box is visible
            selected = self.suggestion_box.curselection()
            if selected:
                suggestion_text = self.suggestion_box.get(selected[0])

                # Get current cursor position
                cursor_pos = self.code_editor.index(tk.INSERT)

                # Find the start of the actual word (ignoring spaces or dots)
                line, col = map(int, cursor_pos.split("."))
                line_text = self.code_editor.get(f"{line}.0", f"{line}.end")

                start_col = col
                while start_col > 0 and line_text[start_col - 1].isalnum():  # Only consider word characters
                    start_col -= 1

                word_start = f"{line}.{start_col}"  # Start of actual word
                word_end = cursor_pos  # Replace only up to cursor position

                # Replace only the word, keeping punctuation like "." or " " intact
                self.code_editor.delete(word_start, word_end)
                self.code_editor.insert(word_start, suggestion_text)

                # Hide suggestion box after insertion
                self.suggestion_box.place_forget()

                return "break"

        return None  # Allow normal Enter behavior if no suggestion is selected

    def select_word(self, event):
        """Select the word on double-click and keep the cursor visible."""
        self.code_editor.tag_remove("sel", "1.0", "end")  # Remove previous selections

        index = self.code_editor.index(tk.CURRENT)
        word_start = self.code_editor.search(r"\m\w", index, backwards=True, regexp=True)
        word_end = self.code_editor.search(r"\M\w", index, forwards=True, regexp=True)

        if not word_start:
            word_start = index
        if not word_end:
            word_end = index

        self.code_editor.tag_add("sel", word_start, word_end)

        # Ensure the cursor remains visible
        self.code_editor.config(insertontime=500)

    def enforce_max_width(self, event):
        current_width = self.folder_tree_frame.winfo_width()
        if current_width > 400:
            self.main_pane.sash_place(0, 400, 0)  

    def reopen_terminal(self, event=None):
        self.vertical_pane.add(self.terminal_frame, height=270,stretch="never")

    def on_key_release(self, event):
        self.update_line_numbers()
        self.show_suggestions(event)
        self.on_text_change(event)

    def indent_selected_text(self, event=None):
        """Indent selected text with Tab."""
        if self.code_editor.tag_ranges("sel"):
            sel_first = self.code_editor.index("sel.first")
            sel_last = self.code_editor.index("sel.last")

            # Get the selected lines
            start_line = int(sel_first.split('.')[0])
            end_line = int(sel_last.split('.')[0])

            # Indent each line in the selection
            for line in range(start_line, end_line + 1):
                self.code_editor.insert(f"{line}.0", "    ")

            # Restore the selection
            self.code_editor.tag_add("sel", sel_first, sel_last)
            return "break"
        else:
            # If no text is selected, insert a tab
            self.code_editor.insert(tk.INSERT, "    ")
            return "break"

    def unindent_selected_text(self, event=None):
        """Unindent selected text with Shift+Tab."""
        if self.code_editor.tag_ranges("sel"):
            sel_first = self.code_editor.index("sel.first")
            sel_last = self.code_editor.index("sel.last")

            # Get the selected lines
            start_line = int(sel_first.split('.')[0])
            end_line = int(sel_last.split('.')[0])

            # Unindent each line in the selection
            for line in range(start_line, end_line + 1):
                line_text = self.code_editor.get(f"{line}.0", f"{line}.4")
                if line_text.startswith("    "):
                    self.code_editor.delete(f"{line}.0", f"{line}.4")

            # Restore the selection
            self.code_editor.tag_add("sel", sel_first, sel_last)
            return "break"
        else:
            cursor_pos = self.code_editor.index(tk.INSERT)
            line = cursor_pos.split('.')[0]
            line_text = self.code_editor.get(f"{line}.0", f"{line}.4")
            if line_text.startswith("    "):
                self.code_editor.delete(f"{line}.0", f"{line}.4")
            return "break"

    def move_to_next_word_boundary(self, event):
        """Move the cursor to the next word boundary (end of word or next special character)."""
        cursor_pos = self.code_editor.index(tk.INSERT)
        line, col = map(int, cursor_pos.split("."))

        # Get the text of the current line
        line_text = self.code_editor.get(f"{line}.0", f"{line}.end")

        # If the current character is alphanumeric or underscore, skip to the end of the word
        if col < len(line_text) and (line_text[col].isalnum() or line_text[col] == "_"):
            while col < len(line_text) and (line_text[col].isalnum() or line_text[col] == "_"):
                col += 1
        else:
            # Move to the next character (special character or space)
            col += 1

        # Move the cursor to the new position
        self.code_editor.mark_set(tk.INSERT, f"{line}.{col}")
        return "break"

    def move_to_previous_word_boundary(self, event):
        """Move the cursor to the previous word boundary (start of word or previous special character)."""
        cursor_pos = self.code_editor.index(tk.INSERT)
        line, col = map(int, cursor_pos.split("."))

        # Get the text of the current line
        line_text = self.code_editor.get(f"{line}.0", f"{line}.end")

        # If the previous character is alphanumeric or underscore, skip to the start of the word
        if col > 0 and (line_text[col - 1].isalnum() or line_text[col - 1] == "_"):
            while col > 0 and (line_text[col - 1].isalnum() or line_text[col - 1] == "_"):
                col -= 1
        else:
            # Move to the previous character (special character or space)
            col -= 1

        # Move the cursor to the new position
        self.code_editor.mark_set(tk.INSERT, f"{line}.{col}")
        return "break"

    def make_file(self):
        if not self.folder_path:
            self.terminal_output(" [✖] No folder is opened.\n Please open a folder first.\n", error=True)
            return

        try:
            selected_item = self.file_tree.selection()
            parent_folder = self.folder_path  # Default to root folder
            parent_node = ""  # Default to root node

            if selected_item:
                selected_item = selected_item[0]
                item_values = self.file_tree.item(selected_item, "values")

                if item_values and item_values[0] == "": 
                    parent_node = self.file_tree.parent(selected_item)
                    parent_folder = self.file_tree.item(parent_node, "values")[0]

                elif item_values and os.path.isdir(item_values[0]):
                    parent_folder = item_values[0]
                    parent_node = selected_item
                else:
                    parent_folder = os.path.dirname(item_values[0]) if item_values else self.folder_path
                    parent_node = self.file_tree.parent(selected_item)

            file_name = self.custom_askstring("Make File", "Enter file name:")
            if not file_name:
                return

            if not re.match(r'^[\w\-. ]+$', file_name):
                self.terminal_output(f" [✖] Invalid file name. Use only letters, numbers, and .-_\n", error=True )
                return

            file_path = os.path.normpath(os.path.join(parent_folder, file_name))

            if os.path.exists(file_path):
                self.terminal_output(f"[✖] '{file_name}' already exists in this location.\n", error= True)
                return

            with open(file_path, "w") as f:
                f.write("")

            # Refresh only the parent node in the tree
            self.update_file_tree(parent_folder, parent_node)
            
            # Add new item to tree without expanding parent
            new_item = self.find_tree_item(file_path)
            if new_item:
                self.file_tree.selection_set(new_item)
                self.file_tree.see(new_item)

        except Exception as e:
            self.terminal_output(f"[X] Failed to create file: {str(e)}\n", error=True)

        if file_path:
            # ... file creation logic ...
            self.undo_stack.append({
                'type': 'create',
                'path': file_path,
                'is_directory': False
            })
            self.redo_stack.clear()

    def find_tree_item(self, path, parent=""):
        """Recursively search tree items to find one matching the given path."""
        children = self.file_tree.get_children(parent)
        for child in children:
            item_path = self.file_tree.item(child, "values")[0]
            if item_path == path:
                return child
            # Search recursively in folders
            if self.file_tree.item(child, "tags")[0] == "folder":
                result = self.find_tree_item(path, parent=child)
                if result:
                    return result
        return None

    def custom_askstring(self, title, prompt):
        dialog = self.CustomInputDialog(self,self.root, title, prompt)
        return dialog.show()

    def make_folder(self):
        """Create new folder in current directory structure with validation"""
        if not self.folder_path:
            self.terminal_output("[✖] No folder opened.\nPlease open a folder first.\n", error=True)
            return

        try:
            # Get parent directory from selection
            selected_item = self.file_tree.selection()
            parent_folder = self.folder_path
            parent_node = ""

            if selected_item:
                selected_item = selected_item[0]
                item_values = self.file_tree.item(selected_item, "values")
                
                if item_values and os.path.isdir(item_values[0]):
                    parent_folder = item_values[0]
                    parent_node = selected_item
                else:
                    parent_node = self.file_tree.parent(selected_item)
                    if parent_node:
                        parent_folder = self.file_tree.item(parent_node, "values")[0]

            # Get folder name with input validation
            folder_name = self.custom_askstring("New Folder", "Enter folder name:")
            if not folder_name:
                return

            # Validate folder name
            if not re.match(r'^[^<>:"/\\|?*]{1,255}$', folder_name):
                self.terminal_output("[✖] Invalid folder name.\n"
                    "Cannot contain: <>:\"/\\|?* or be empty\n",error=True)
                return

            # Create normalized path
            folder_path = os.path.normpath(os.path.join(parent_folder, folder_name))

            # Check if folder exists
            if os.path.exists(folder_path):
                self.terminal_output(f"[✖] '{folder_name}' already exists in this location.\n",error=True)
                return

            # Attempt to create folder
            os.makedirs(folder_path, exist_ok=False)

            # Update tree view
            self.update_file_tree(parent_folder, parent_node)
            self.file_tree.item(parent_node, open=True)  # Expand parent node

            # Select and scroll to new item
            new_item = self.find_tree_item(folder_path)
            if new_item:
                self.file_tree.selection_set(new_item)
                self.file_tree.see(new_item)

        except FileExistsError:
            self.terminal_output(f"[✖] Folder '{folder_name}' was created by another process.\n",error=True)
        except OSError as e:
            self.terminal_output(f"[✖] Failed to create folder:\n{str(e)}\n", error=True)
        except Exception as e:
            self.terminal_output(f"[✖] Unexpected error creating folder:\n{str(e)}\n",error=True)
        
        if folder_path:
            # ... folder creation logic ...
            self.undo_stack.append({
                'type': 'create',
                'path': folder_path,
                'is_directory': True
            })
            self.redo_stack.clear()

    def truncate_folder_name(self, folder_name, max_length=20):
        """Truncate the folder name if it exceeds the maximum length."""
        if len(folder_name) > max_length:
            return folder_name[:max_length - 3] + "..."  # Truncate and add ellipsis
        return folder_name

    def read_output_stream(self, stream, error):
        try:
            for line in iter(stream.readline, ''):
                self.terminal_output(line, error)

                # Check if the process is requesting input (common prompts end with colon)
                if line.strip().endswith(":") or "input" in line.lower():
                    self.terminal_input.config(state='normal')
                    self.terminal_input.focus_set()  # Focus input box
                    self.terminal_output("[ Waiting for user input... ]\n")
            stream.close()
        except Exception as e:
            self.terminal_output(f"Error reading output: {e}\n", error=True)

    def check_process_status(self):
        """Checks if the process is still running and updates the terminal."""
        # Process any pending output in the queue
        while not self.output_queue.empty():
            output, is_error = self.output_queue.get_nowait()
            self.terminal_output(output, error=is_error)

        # Check if the process is still running
        if self.process and self.process.poll() is None:
            # Schedule the next check
            self.root.after(100, self.check_process_status)
        else:
            # Process has finished
            self.process = None
            self.stop_code()
            self.stop_button.pack_forget()  # Hide stop button
            self.terminal_output("Process Finished...\n", error=False)
            self.stop_button.pack_forget()
            self.run_button.pack(side=tk.RIGHT, padx=5, pady=5)
            self.terminal_input.config(state='normal')

    def create_styled_entry(self, parent):
        entry = tk.Entry(
            parent,
            font=("Consolas", 12),
            bg="#2d2d30",
            fg="#d4d4d4",
            insertbackground="white",
            relief="flat",
            borderwidth=2,
            highlightthickness=1,
            highlightcolor=self.ACCENT_COLOR,
            highlightbackground="#3e3e42"
        )
        return entry

    def show_context_menu(self, event):
        item = self.file_tree.identify_row(event.y)
        if item:
            self.file_tree.selection_set(item)
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Cut         Ctrl+X", command=self.cut_items)
            menu.add_command(label="Copy      Ctrl+C", command=self.copy_items)
            menu.add_command(label="Paste     Ctrl+V", command=self.paste_items)
            menu.add_separator()
            menu.add_command(label="Rename", command=self.rename_item)
            menu.post(event.x_root, event.y_root)

    def rename_item(self):
        
        if self.rename_entry:  # Prevent multiple rename entries
            return

        item = self.file_tree.selection()
        if not item:
            return
        
        item = item[0]
        text = self.file_tree.item(item, "text").strip()

        if text == "(Empty Folder)":
            self.terminal_output("[X] Cannot rename '(Empty Folder)' placeholder.\n",error=True)
            return
        
        values = self.file_tree.item(item, "values")

        if not values:
            self.terminal_output("[✖] Cannot rename this item\n",error=True)
            return
        
        path = values[0]

        # Clear text temporarily during rename
        self.file_tree.item(item, text=" ")
        
        # Get bounding box for first column
        bbox = self.file_tree.bbox(item, "#0")
        if not bbox:
            return

        # Create styled entry
        self.rename_entry = self.create_styled_entry(self.file_tree)
        self.rename_entry.insert(0, text)
        
        # Configure events
        self.rename_entry.bind("<Return>", lambda e: self.finish_rename(item, path))
        self.rename_entry.bind("<FocusOut>", lambda e: self.finish_rename(item, path))
        self.rename_entry.bind("<Escape>", lambda e: self.cancel_rename(item, text))
        
        # Position entry over the item text
        self.rename_entry.place(
            x=bbox[0]-2,  # Adjust for better alignment
            y=bbox[1]-1,
            width=bbox[2]+4,
            height=bbox[3]+2
        )
        
        # Select all text and focus
        self.rename_entry.select_range(0, tk.END)
        self.rename_entry.focus_set()

    def on_rename_complete(self, item, entry, old_path):
        new_name = entry.get().strip()
        entry.destroy()
        
        if not new_name:
            return

        try:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            os.rename(old_path, new_path)
            self.file_tree.item(item, text=f" {new_name}", values=(new_path,))
            self.update_file_tree(self.folder_path)  # Refresh the tree view
            
            # Update editor if renaming currently open file
            if self.current_file == old_path:
                self.current_file = new_path
                self.root.title(f"Python Editor - {new_name}")
                
        except Exception as e:
            self.terminal_output(f"Failed to rename: \nThe '{new_name}' already Exixts...\n",error=True)
            self.file_tree.item(item, text=f" {os.path.basename(old_path)}")

    def start_rename_via_shortcut(self, event=None):
        if not self.rename_entry:  # Prevent multiple rename entries
            self.rename_item()

    def finish_rename(self, item, old_path):
        if not self.rename_entry:
            return

        new_name = self.rename_entry.get().strip()
        self.rename_entry.destroy()
        self.rename_entry = None

        if not new_name:
            self.file_tree.item(item, text=f" {os.path.basename(old_path)}")
            return

        try:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            os.rename(old_path, new_path)
            
            # Update tree item
            self.file_tree.item(item, 
                text=f" {new_name}",
                values=(new_path,)
            )
            
            # Update current file if it was renamed
            if self.current_file == old_path:
                self.current_file = new_path
                self.root.title(f"VS Code Like Python Editor - {new_name}")
                
            # Refresh parent directory in tree
            parent_node = self.file_tree.parent(item)
            if parent_node:
                parent_path = self.file_tree.item(parent_node, "values")[0]
            else:
                parent_path = self.folder_path
            self.update_file_tree(parent_path, parent_node)

        except Exception as e:
            self.terminal_output(f"Failed to rename: \nThe '{new_name}' already Exixts...\n",error=True)
            self.file_tree.item(item, text=f" {os.path.basename(old_path)}")

    def cancel_rename(self, item, original_text):
        if self.rename_entry:
            self.rename_entry.destroy()
            self.rename_entry = None
        self.file_tree.item(item, text=f" {original_text}")

    def get_selected_paths(self):
        """Return list of paths for all selected items"""
        valid_paths = []
        for item in self.file_tree.selection():
            try:
                if self.file_tree.exists(item):
                    values = self.file_tree.item(item, "values")
                    if values and values[0]:
                        # Normalize path and strip whitespace
                        clean_path = os.path.normpath(values[0].strip())
                        valid_paths.append(clean_path)
            except tk.TclError:
                continue
        return valid_paths
    
    def confirm_delete(self, paths):
        """Show confirmation dialog for deletion"""
        item_list = "\n".join(f"• {os.path.basename(p)}" for p in paths)
        return messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to permanently delete these items?\n{item_list}",
            parent=self.root
        )
    
    def delete_items(self, event=None):
        """Delete selected items with backup for undo support"""
        expanded_paths = self.get_expanded_paths() # Capture expanded paths before any changes

        selected_items = self.file_tree.selection()
        if not selected_items:
            return

        paths = self.get_selected_paths()
        if not paths:
            return
        
        for path in paths:
            if path in self.opened_files:
                self.close_tab(path)

        # Sort paths by depth (deepest first) for proper deletion order
        paths.sort(key=lambda p: p.count(os.sep), reverse=True)

        # Create backup directory if it doesn't exist
        backup_root = os.path.join(tempfile.gettempdir(), "editor_undo_backups")
        os.makedirs(backup_root, exist_ok=True)

        # Create unique backup directory for this deletion batch
        batch_id = str(uuid.uuid4())
        backup_dir = os.path.join(backup_root, batch_id)
        os.makedirs(backup_dir, exist_ok=True)

        deletion_batch = []
        error_occurred = False

        # Process deletion with backup
        for path in paths:
            try:
                if not os.path.exists(path):
                    continue

                # Preserve directory structure in backup
                rel_path = os.path.relpath(path, start=self.folder_path)
                backup_path = os.path.join(backup_dir, rel_path)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)

                # Move to backup instead of deleting
                shutil.move(path, backup_path)
                
                deletion_batch.append({
                    'original_path': path,
                    'backup_path': backup_path,
                    'is_directory': os.path.isdir(path)
                })

            except Exception as e:
                error_occurred = True
                self.terminal_output(f"Failed to delete {os.path.basename(path)}:\n{str(e)}\n", error=True)

        if error_occurred:
            try:
                shutil.rmtree(backup_dir)
            except:
                pass
            return

        if deletion_batch:
            self.undo_stack.append({
                'type': 'delete',
                'batch': deletion_batch,
                'backup_dir': backup_dir
            })
            self.redo_stack.clear()
            if len(self.deletion_history) > 50:
                oldest = self.deletion_history.pop(0)
                try:
                    shutil.rmtree(os.path.dirname(oldest[0]['backup_path']))
                except:
                    pass

        # Handle open files in deleted items
        open_files = [p for p in paths if p == self.current_file]
        if open_files:
            self.current_file = None
            self.code_editor.delete("1.0", tk.END)
            self.filename_label.config(text="")
            self.root.title("VS Code Like Python Editor")

        # Update UI
        self.file_tree.delete(*self.file_tree.get_children())
        self.update_file_tree(self.folder_path, restore_expanded=True)

        if self.current_file and not os.path.exists(self.current_file):
            self.current_file = None
            self.code_editor.delete("1.0", tk.END)
            self.filename_label.config(text="")
            self.root.title("VS Code Like Python Editor")
        self.terminal_output(f"Deleted {len(deletion_batch)} item(s) (Ctrl+Z to undo)\n")
        self.restore_expanded_paths(expanded_paths)

        # Clear selection
        self.file_tree.selection_set(())

    def on_drag_start(self, event):

        self.dragged_items = self.file_tree.selection()  # Get all selected items
        if not self.dragged_items:
            return
            
        # Verify all dragged items have valid paths
        self.valid_drag_items = []
        for item in self.dragged_items:
            values = self.file_tree.item(item, "values")
            if values and values[0] and os.path.exists(values[0]):
                self.valid_drag_items.append(item)
        
        if not self.valid_drag_items:
            return
            
        self.drag_start_pos = (event.x, event.y)
        self.dragging = False

    def on_drag_motion(self, event):
        """Handle drag motion with visual feedback."""
        if not hasattr(self, 'drag_start_pos') or not self.valid_drag_items:
            return
        # Calculate movement distance
        dx = abs(event.x - self.drag_start_pos[0])
        dy = abs(event.y - self.drag_start_pos[1])
        if dx > 5 or dy > 5 and not self.dragging:
            self.dragging = True
            self.file_tree.config(cursor="hand2")
        
        if self.dragging:
            # Highlight drop target
            item = self.file_tree.identify_row(event.y)
            if item:
                tags = self.file_tree.item(item, "tags")
                if "folder" in tags:
                    self.file_tree.selection_set(item)
                else:
                    parent = self.file_tree.parent(item)
                    if parent:
                        self.file_tree.selection_set(parent)

    def on_drag_release(self, event):
        """Finalize drop operation with proper validation"""
        if not hasattr(self, 'dragging') or not self.dragging:
            return

        try:
            # Get valid dragged items with proper paths
            valid_dragged = []
            for item_id in self.dragged_items:
                values = self.file_tree.item(item_id, "values")
                if not values or not values[0]:
                    continue
                path = values[0].strip()
                if os.path.exists(path):
                    valid_dragged.append((item_id, path))

            if not valid_dragged:
                return

            # Get target folder path with validation
            target_item = self.file_tree.identify_row(event.y)
            target_path = self.folder_path
            
            if target_item:
                target_values = self.file_tree.item(target_item, "values")
                if target_values and target_values[0]:
                    target_path = target_values[0].strip()
                    if not os.path.isdir(target_path):
                        parent = self.file_tree.parent(target_item)
                        if parent:
                            parent_values = self.file_tree.item(parent, "values")
                            if parent_values and parent_values[0]:
                                target_path = parent_values[0].strip()

            moved_items = []
            for item_id, source_path in valid_dragged:
                try:
                    if not os.path.exists(source_path):
                        continue

                    # Prevent moving into self or root
                    if (os.path.commonpath([source_path, target_path]) == 
                        os.path.normpath(source_path)):
                        continue

                    item_name = os.path.basename(source_path)
                    dest_path = os.path.join(target_path, item_name)

                    if os.path.exists(dest_path):
                        raise FileExistsError(f"'{item_name}' exists")

                    shutil.move(source_path, dest_path)
                    moved_items.append(source_path)

                    # Update tree items
                    parent_node = self.file_tree.parent(item_id)
                    if parent_node:
                        parent_path = self.file_tree.item(parent_node, "values")[0]
                        self.update_file_tree(parent_path, parent_node)

                except Exception as e:
                    self.terminal_output(f"Move Error: {str(e)}\n", error=True)

            if moved_items:
                # Full refresh to ensure consistency
                self.update_file_tree(self.folder_path)
                self.terminal_output(f"Moved {len(moved_items)} items\n")

        except Exception as e:
            self.terminal_output(f"Drag Error: {str(e)}\n", error=True)
        finally:
            # Cleanup and reset
            self.file_tree.config(cursor="")
            if hasattr(self, 'drag_start_pos'):
                del self.drag_start_pos
            if hasattr(self, 'dragged_items'):
                del self.dragged_items
            if hasattr(self, 'dragging'):
                del self.dragging

    def get_expanded_paths(self):
        expanded = set()
        def traverse(parent):
            for child in self.file_tree.get_children(parent):
                child_path = self.file_tree.item(child, "values")[0]
                if self.file_tree.item(child, "open"):
                    expanded.add(child_path)
                    traverse(child)
        traverse('')
        return expanded

    def restore_expanded_paths(self, paths):
        def traverse(parent):
            for child in self.file_tree.get_children(parent):
                child_path = self.file_tree.item(child, "values")[0]
                if child_path in paths:
                    self.file_tree.item(child, open=True)
                    traverse(child)
        traverse('')

    def focus_file_in_tree(self):
        if not self.current_file:
            return
        
        def recursive_search(tree, node):
            # Loop through each child node
            for child in tree.get_children(node):
                values = tree.item(child, "values")
                if values and values[0] == self.current_file:
                    # File found, select & focus
                    tree.selection_set(child)
                    tree.see(child)
                    return True
                # Search deeper
                if recursive_search(tree, child):
                    return True
            return False
        
        recursive_search(self.file_tree, "")

    def find_tree_child_node(self, parent, target_path):
        """Recursive helper for node search."""
        for child in self.file_tree.get_children(parent):
            child_path = os.path.normpath(self.file_tree.item(child, "values")[0])
            if child_path == target_path:
                return child
            if "folder" in self.file_tree.item(child, "tags"):
                result = self.find_tree_child_node(child, target_path)
                if result:
                    return result
        return None

    def open_search_bar(self, event=None):
        if hasattr(self, 'search_window') and self.search_window.winfo_exists():
            return  # Already open

        self.search_window = tk.Toplevel(self.root)
        self.search_window.overrideredirect(True)  # REMOVE default top bar!
        self.search_window.configure(bg="#a4ffee")
        self.search_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100))
        self.search_window.attributes('-topmost', True)  # Stay on top

        # Custom title bar (optional, if you want to move/drag)
        self.title_bar = tk.Frame(self.search_window, bg="#a4ffee", relief='raised', bd=0)
        self.title_bar.pack(fill=tk.X)

        self.title_label = tk.Label(self.title_bar,text="",bg='#a4ffee')
        self.title_label.pack(side=tk.LEFT, padx=10)

        # Make draggable
        self.title_bar.bind("<Button-1>", self.start_move_search)
        self.title_bar.bind("<B1-Motion>", self.do_move_search)

        self.search_window_label = tk.Label(self.search_window, text="Find: ", bg="#a4ffee", fg="#0038b8", font=("Consolas", 15, 'bold'))
        self.search_window_label.pack(side=tk.LEFT, padx=5, pady=10)
        
        self.text_search_entry = tk.Entry(self.search_window, font=("Consolas", 12), bg="#190a0b", fg="white", insertbackground="white", border=5, borderwidth=3)
        self.text_search_entry.pack(side=tk.LEFT, padx=5, pady=10)
        self.text_search_entry.focus()

        self.search_btn = tk.Button(self.search_window, text="🔍", command=self.search_text, bg="#a4ffee",activebackground='#a4ffee', fg="green", font=("Consolas", 25), border=0,borderwidth=0)
        self.search_btn.pack(side=tk.LEFT, padx=1, pady=5)

        self.close_btn = tk.Button(self.search_window, text="❌", command=self.close_search_bar, bg="#a4ffee",activebackground='#a4ffee', fg="red", font=("Consolas", 15), border=0,borderwidth=0)
        self.close_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.text_search_entry.bind("<KeyRelease>", self.real_time_search) 
        
        self.text_search_entry.bind("<Return>", lambda e: self.search_text())

    def close_search_bar(self):
        self.code_editor.tag_remove('search_match', "1.0", tk.END)  # Remove all highlights
        if hasattr(self, 'search_window') and self.search_window.winfo_exists():
            self.search_window.destroy()

        # Add this line to clear the count cache
        if hasattr(self, 'character_count'):
            del self.character_count

    def search_text(self):
        self.code_editor.tag_remove('search_match', "1.0", tk.END)
        word = self.text_search_entry.get()
        count = 0

        if word:
            idx = "1.0"
            while True:
                idx = self.code_editor.search(word, idx, nocase=False, stopindex=tk.END)
                if not idx:
                    break
                end_idx = f"{idx}+{len(word)}c"
                self.code_editor.tag_add('search_match', idx, end_idx)
                idx = end_idx
                count += 1

            # Truncate displayed text to first 10 characters
            displayed_text = word[:10] + '...' if len(word) > 10 else word
            self.character_count = f"{displayed_text} : {count} matches"

            if hasattr(self, 'count_label'):
                self.count_label.config(text=self.character_count)
            else:
                self.count_label = tk.Label(self.title_bar, text=self.character_count,
                                        bg='#a4ffee', font=("Consolas", 12), 
                                        foreground='#212157')
                self.count_label.pack(side=tk.TOP, pady=5)

            self.code_editor.tag_config('search_match', background="yellow", foreground=self.BLACK)

    def start_move_search(self, event):
        self.search_window.x = event.x
        self.search_window.y = event.y

    def do_move_search(self, event):
        x = event.x_root - self.search_window.x
        y = event.y_root - self.search_window.y
        self.search_window.geometry(f"+{x}+{y}")

    def select_all_files_folders(self, event=None):
        selected_items = self.file_tree.selection()
        
        if not selected_items:
            return "break"

        # Get the parent folder of the first selected item
        parent = self.file_tree.parent(selected_items[0])
        
        # Get all children (files/folders) under that parent
        all_children = self.file_tree.get_children(parent)
        
        # Select all children
        self.file_tree.selection_set(all_children)
        
        return "break"

    def check_for_errors(self):
            """Check code for syntax errors using ast and pyflakes"""
            self.code_editor.tag_remove("error", "1.0", tk.END)
            code = self.code_editor.get("1.0", tk.END)
            
            # Basic syntax check with ast
            try:
                ast.parse(code)
            except SyntaxError as e:
                # Get exact error position
                lineno = e.lineno or 1
                col_offset = e.offset or 0
                
                # Calculate start/end positions
                start = f"{lineno}.{col_offset-1}"
                end = f"{lineno}.{col_offset}"
                
                # Highlight specific error character
                self.highlight_error(start, end)

    def highlight_error(self, start_pos, end_pos):
        """Highlight specific error range"""
        try:
            self.code_editor.tag_add("error", start_pos, end_pos)
            # Add custom underline style
            self.code_editor.tag_config("error", 
                                    underline=True,
                                    underlinefg="red",
                                    foreground="red")
        except tk.TclError:
            pass  # Handle invalid positions gracefully

    def filter_tree(self, event=None):
        if hasattr(self, '_filter_after_id'):
            self.root.after_cancel(self._filter_after_id)
        self._filter_after_id = self.root.after(300, self._perform_real_filter)

    def _perform_real_filter(self):
        search_text = self.tree_search_entry.get().strip().lower()

        # Add check for folder_path
        if not self.folder_path:
            self.terminal_output("[✖] No folder opened. Please open a folder first.\n", error=True)
            return
        
        if not search_text:
            self.file_tree.delete(*self.file_tree.get_children())
            self.update_file_tree(self.folder_path, restore_expanded=False)
            return

        # Walk through directory and find matches
        matched = set()
        hierarchy = set()

        for root, dirs, files in os.walk(self.folder_path):
            for name in dirs + files:
                if search_text in name.lower():
                    full_path = os.path.join(root, name)
                    matched.add(full_path)
                    # Add parent directories to hierarchy
                    current = full_path
                    while os.path.dirname(current) != self.folder_path:
                        current = os.path.dirname(current)
                        hierarchy.add(current)
                    hierarchy.add(full_path)

        # Clear current tree
        self.file_tree.delete(*self.file_tree.get_children())

        # Build directory structure
        path_map = defaultdict(list)
        for path in hierarchy:
            parent = os.path.dirname(path)
            path_map[parent].append(path)


        self.file_tree.delete(*self.file_tree.get_children())
        
        def build_tree(parent_node, parent_path):
            for child_path in sorted(path_map.get(parent_path, []), key=lambda x: os.path.basename(x).lower()):
                is_dir = os.path.isdir(child_path)
                node = self.file_tree.insert(
                    parent_node, "end",
                    text=" " + os.path.basename(child_path),
                    values=[child_path],
                    tags=("folder" if is_dir else "file",),
                    image=self.folder_icon if is_dir else self.get_file_icon(child_path),
                    open = True
                )
                if is_dir:
                    build_tree(node, child_path)

        # Start building from root
        build_tree("", self.folder_path)

    def get_file_icon(self, path):
        # Your existing icon selection logic from update_file_tree
        ext = os.path.splitext(path)[1].lower()
        return {
            '.py': self.python_icon,
            '.html': self.html_icon,
            # ... add all other extensions
        }.get(ext, self.file_icon)
    
    def clear_placeholder(self,event):
            if self.tree_search_entry.get() == "Search":
                self.tree_search_entry.delete(0, tk.END)
                self.tree_search_entry.config(fg="white")  # Normal text color     
       
    def add_placeholder(self,event):
        if self.tree_search_entry.get() == "":
            self.tree_search_entry.insert(0, "Search")
            self.tree_search_entry.config(fg="gray")  # Placeholder color
    
    def check_click_outside_suggestion_box(self, event):
        # Check if suggestion box is visible
        if self.suggestion_box.winfo_ismapped():
            # Get mouse click coordinates
            x, y = event.x_root, event.y_root

            # Get suggestion box position
            sug_x = self.suggestion_box.winfo_rootx()
            sug_y = self.suggestion_box.winfo_rooty()
            sug_width = self.suggestion_box.winfo_width()
            sug_height = self.suggestion_box.winfo_height()

            # If click is outside suggestion box
            if not (sug_x <= x <= sug_x + sug_width and sug_y <= y <= sug_y + sug_height):
                self.suggestion_box.place_forget()  # Hide it
    
    def real_time_search(self, event=None):
        self.search_text()
        if hasattr(self, 'search_window') and self.search_window.winfo_exists():
            self.search_window.after(10, self.update_search_count)

    def update_search_count(self):
        if hasattr(self, 'count_label') and self.count_label.winfo_exists():
            self.count_label.config(text=self.character_count)

    def on_tree_click(self, event):
        """Track if Ctrl/Shift is pressed during a treeview click."""
        ctrl_pressed = (event.state & 0x0004) != 0  # Check Ctrl key
        shift_pressed = (event.state & 0x0001) != 0  # Check Shift key
        self.ctrl_shift_pressed_during_click = ctrl_pressed or shift_pressed

    def start_file_monitor(self):
        if self.folder_path:
            self.stop_file_monitor()
            self.event_handler = self.FileChangeHandler(self)
            self.observer = Observer()
            self.observer.schedule(self.event_handler, self.folder_path, recursive=True)
            self.observer.start()
            self.root.after(100, self.check_for_file_changes)

    def stop_file_monitor(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

    def check_for_file_changes(self):
        if self.should_update:
            self.update_file_tree(self.folder_path)
            self.should_update = False
        self.root.after(500, self.check_for_file_changes)

    def cut_items(self, event=None):
        selected_items = self.file_tree.selection()
        if not selected_items:
            return

        # Clear clipboard
        self.clipboard["operation"] = "cut"
        self.clipboard["paths"] = []

        # Remove previous 'cut_item' tags
        for item in self.file_tree.get_children():
            self.file_tree.item(item, tags=tuple(tag for tag in self.file_tree.item(item, "tags") if tag != "cut_item"))

        for item in selected_items:
            path = self.file_tree.item(item, "values")[0]
            if path:
                self.clipboard["paths"].append(path)
                # Apply yellow background to cut items
                current_tags = self.file_tree.item(item, "tags")
                if "cut_item" not in current_tags:
                    self.file_tree.item(item, tags=current_tags + ("cut_item",))

        self.file_tree.selection_remove(selected_items)  # Deselect after cutting

    def copy_items(self, event=None):
        expanded_paths = self.get_expanded_paths()
        self.clipboard["operation"] = "copy"
        self.clipboard["paths"] = self.get_selected_paths()
        self.restore_expanded_paths(expanded_paths)

    def paste_items(self, event=None):
        if not self.clipboard["paths"] or not self.clipboard["operation"]:
            return
        
        expanded_paths = self.get_expanded_paths()
        target_item = self.file_tree.selection()
        target_path = self.folder_path
        if target_item:
            target_values = self.file_tree.item(target_item[0], "values")
            if target_values and os.path.isdir(target_values[0]):
                target_path = target_values[0]
        try:
            for src_path in self.clipboard["paths"]:
                dest_path = os.path.join(target_path, os.path.basename(src_path))
                if self.clipboard["operation"] == "copy":
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dest_path)
                    else:
                        shutil.copy2(src_path, dest_path)
                elif self.clipboard["operation"] == "cut":
                    shutil.move(src_path, dest_path)

                    # Update tabs if file was moved
                    if src_path in self.opened_files:
                        index = self.opened_files.index(src_path)
                        self.opened_files[index] = dest_path  # Update opened files list
                        
                        # Update tab_buttons
                        if src_path in self.tab_buttons:
                            tab_info = self.tab_buttons.pop(src_path)
                            self.tab_buttons[dest_path] = tab_info
                            tab_container, label, btn = tab_info
                            label.config(text=os.path.basename(dest_path))
                            # Update bindings to new path
                            label.bind("<Button-1>", lambda e, fp=dest_path: self.switch_to_tab(fp))
                            btn.bind("<Button-1>", lambda e, fp=dest_path: self.close_tab(fp))
                            # Update current_file if active
                            if self.current_file == src_path:
                                self.current_file = dest_path
                                self.filename_label.config(text=os.path.basename(dest_path))
                
            self.update_file_tree(self.folder_path)
            self.restore_expanded_paths(expanded_paths | {target_path})  # Keep target expanded

        except Exception as e:
            self.terminal_output(f"Failed to paste {str(e)}\n",error=True)

        finally:
            # Clear clipboard after paste operation
            if self.clipboard["operation"] == "cut":
                self.clipboard = {"operation": None, "paths": []}
        
        self.update_file_tree(self.folder_path)

    def on_mousewheel(self,event):
        # For Windows
        self.file_tree.yview_scroll(int(-1*(event.delta/120)), "units")

    def save_sidebar_state(self):
        self.expanded_items = []
        for item in self.file_tree.get_children():
            self.save_expanded_recursive(item)
        self.selected_items = self.file_tree.selection()
        self.tree_scroll_position = self.file_tree.yview()
        
    def save_expanded_recursive(self, item):
        if self.file_tree.item(item, "open"):
            self.expanded_items.append(item)
        for child in self.file_tree.get_children(item):
            self.save_expanded_recursive(child)

    def restore_sidebar_state(self):
        # Restore expanded folders
        for item in self.expanded_items:
            if self.file_tree.exists(item):
                self.file_tree.item(item, open=True)
        # Restore selection
        if hasattr(self, 'selected_items'):
            self.file_tree.selection_set(self.selected_items)
        # Restore scroll
        if hasattr(self, 'tree_scroll_position'):
            self.file_tree.yview_moveto(self.tree_scroll_position[0])

    def toggle_sidebar(self,event=None):
        if self.sidebar_visible:
            self.save_sidebar_state()
            self.main_pane.forget(self.folder_tree_frame)
            self.sidebar_visible = False
        else:
            # Remove all panes temporarily
            panes = list(self.main_pane.panes())
            for pane in panes:
                self.main_pane.forget(pane)

            # Re-add folder_tree_frame first (left side)
            self.main_pane.add(self.folder_tree_frame)
            # Re-add vertical pane (editor + terminal)
            self.main_pane.add(self.vertical_pane,)
            self.restore_sidebar_state()
            self.sidebar_visible = True

    def scroll_tabs_x(self, event):
        direction = -1 if event.delta > 0 else 1
        self.file_tab_canvas.xview_scroll(direction * 2, "units")

    def bind_mousewheel(self, event):
        self.editor_frame.bind_all("<Shift-MouseWheel>", self.scroll_tabs_x)
        self.editor_frame.bind_all("<MouseWheel>", self.scroll_tabs_x)

    def unbind_mousewheel(self, event):
        self.editor_frame.unbind_all("<Shift-MouseWheel>")
        self.editor_frame.unbind_all("<MouseWheel>")

    def add_file_tab(self, file_path):
        if file_path in self.opened_files:
            self.highlight_tab(file_path)
            return

        self.opened_files.append(file_path)
        tab_id = len(self.opened_files)
        
        tab_container = tk.Frame(self.tab_frame, bg=self.BLACK, padx=5)
        tab_container.pack(side=tk.LEFT, padx=1, pady=2)
        
        label = tk.Label(tab_container, text=os.path.basename(file_path), 
                       bg=self.BLACK, fg="white", font=("Consolas", 12))
        label.pack(side=tk.LEFT)
        label.bind("<Button-1>", lambda e, fp=file_path: self.switch_to_tab(fp))
        
        close_btn = tk.Label(tab_container, text=" X ", fg="white", 
                           bg=self.BLACK, font=("Consolas", 12))
        close_btn.pack(side=tk.LEFT)
        close_btn.bind("<Button-1>", lambda e, fp=file_path: self.close_tab(fp))
        
        self.tab_buttons[file_path] = (tab_container, label, close_btn)
        self.highlight_tab(file_path)
        self.update_tab_scroll()
        
        # Show scrollbar if needed
        if self.tab_frame.winfo_reqwidth() > self.file_tab_canvas.winfo_width():
            self.canvas_scrollbar.pack(side=tk.TOP, fill=tk.X)

    def switch_to_tab(self, file_path):
        if file_path == self.current_file:
            return
        
        if not os.path.exists(file_path):
            self.terminal_output(f"File moved or deleted. Closing tab.\n", error=True)
            self.close_tab(file_path)
            return
            
        self.current_file = file_path
        self.load_file(file_path)
        self.highlight_tab(file_path)
        self.focus_file_in_tree()

    def highlight_tab(self, file_path):
        for fp, (container, label, btn) in self.tab_buttons.items():
            bg = "#fbff53" if fp == file_path else "#151515"
            fg = "#ff0000" if fp == file_path else "white"
            container.config(bg=bg)
            label.config(bg=bg, fg=fg)
            btn.config(bg=bg, fg=fg)

    def close_tab(self, file_path):
        if file_path not in self.opened_files:
            return
            
        self.opened_files.remove(file_path)
        self.tab_buttons[file_path][0].destroy()
        del self.tab_buttons[file_path]
        
        if file_path == self.current_file:
            if self.opened_files:
                self.switch_to_tab(self.opened_files[-1])
            else:
                self.current_file = None
                self.code_editor.delete("1.0", tk.END)
                self.filename_label.config(text="")
        
        self.update_tab_scroll()
        self.update_line_numbers()

    def update_tab_scroll(self):
        self.tab_frame.update_idletasks()
        self.file_tab_canvas.configure(scrollregion=self.file_tab_canvas.bbox("all"))
        # Hide scrollbar if not needed
        if self.tab_frame.winfo_reqwidth() <= self.file_tab_canvas.winfo_width():
            self.canvas_scrollbar.pack_forget()

    def toggle_all_folders(self, event=None):
        if not hasattr(self, 'folders_expanded'):
            self.folders_expanded = False  # Initial state
        all_items = self.file_tree.get_children()

        def expand_all(items):
            for item in items:
                self.file_tree.item(item, open=True)
                expand_all(self.file_tree.get_children(item))

        def collapse_all(items):
            for item in items:
                self.file_tree.item(item, open=False)
                collapse_all(self.file_tree.get_children(item))

        if not self.folders_expanded:
            expand_all(all_items)
            self.folders_expanded = True
        else:
            collapse_all(all_items)
            self.folders_expanded = False

    def terminal_delete_clear(self,event=None):
        self.terminal.config(state="normal")
        self.terminal.delete("1.0", tk.END)
        self.terminal.config(state="disabled")
        return 'break'

    def move_line(self, direction):
        cursor_index = self.code_editor.index(tk.INSERT)
        line_num, col = map(int, cursor_index.split("."))

        if direction == "up" and line_num > 1:
            swap_line_num = line_num - 1
        elif direction == "down" and line_num < int(self.code_editor.index("end-1c").split(".")[0]):
            swap_line_num = line_num + 1
        else:
            return

        # Get line contents
        current_line = self.code_editor.get(f"{line_num}.0", f"{line_num}.end") + "\n"
        swap_line = self.code_editor.get(f"{swap_line_num}.0", f"{swap_line_num}.end") + "\n"

        # Swap lines
        self.code_editor.delete(f"{swap_line_num}.0", f"{swap_line_num}.end+1c")
        self.code_editor.insert(f"{swap_line_num}.0", current_line)

        self.code_editor.delete(f"{line_num}.0", f"{line_num}.end+1c")
        self.code_editor.insert(f"{line_num}.0", swap_line)

        # Restore the cursor to its original position
        self.code_editor.mark_set(tk.INSERT, f"{line_num}.{col}")

    def open_new_terminal(self,event=None):
        self.reopen_terminal()
        self.terminal_delete_clear()
        return 'break'

    def insert_new_line_below(self, event=None):
        """Insert new line below with proper indentation"""
        cursor_pos = self.code_editor.index(tk.INSERT)
        line, col = map(int, cursor_pos.split('.'))
        
        # Get current line text
        line_text = self.code_editor.get(f"{line}.0", f"{line}.end")
        
        # Get current indentation
        leading_whitespace = re.match(r'^[ \t]*', line_text).group()
        
        # Check if we should add extra indentation (e.g., line ends with :)
        extra_indent = ""
        if line_text.strip().endswith(':'):
            extra_indent = '    '  # 4 spaces
        
        # Insert new line with combined indentation
        new_indent = leading_whitespace + extra_indent
        self.code_editor.insert(f"{line}.end", f"\n{new_indent}")
        
        # Move cursor to new line at indentation end
        new_line = line + 1
        self.code_editor.mark_set(tk.INSERT, f"{new_line}.{len(new_indent)}")
        return "break"

    def duplicate_line(self, event=None):
        """Duplicates the current line and inserts it below, keeping cursor on the duplicated line."""
        cursor_index = self.code_editor.index(tk.INSERT)
        line_num, col_num = cursor_index.split(".")
        line_start = f"{line_num}.0"
        line_end = f"{line_num}.end"
        line_content = self.code_editor.get(line_start, line_end)
        
        new_line_num = str(int(line_num) + 1)
        new_cursor_pos = f"{new_line_num}.{col_num}"
        
        self.code_editor.insert(line_end, "\n" + line_content)
        self.code_editor.mark_set("insert", new_cursor_pos)  # Move cursor to duplicated line
        
        return "break"

    def modify_selection(self, direction, word_jump):
        # Get current positions
        current_pos = self.code_editor.index(tk.INSERT)
        anchor_pos = self.selection_anchor or current_pos

        # Calculate new cursor position
        new_pos = self.calculate_new_position(current_pos, direction, word_jump)

        # Update selection
        self.update_selection_range(anchor_pos, new_pos)

        # Move cursor and maintain anchor
        self.code_editor.mark_set(tk.INSERT, new_pos)
        if not self.selection_anchor:
            self.selection_anchor = anchor_pos

        # Update anchor if crossing over
        if self.position_changed_direction(anchor_pos, current_pos, new_pos):
            self.selection_anchor = current_pos

        return "break"

    def calculate_new_position(self, pos, direction, word_jump):
        line, col = map(int, pos.split('.'))
        line_text = self.code_editor.get(f"{line}.0", f"{line}.end")
        max_col = len(line_text)

        if word_jump:
            new_line, new_col = line, col
            if direction == "left":
                if col == 0 and line > 1:  # Move to previous line
                    new_line -= 1
                    prev_line_text = self.code_editor.get(f"{new_line}.0", f"{new_line}.end")
                    new_col = self.find_previous_word_boundary(prev_line_text, len(prev_line_text))
                else:
                    new_col = self.find_previous_word_boundary(line_text, col)
            else:
                if col >= max_col and line < int(self.code_editor.index('end-1c').split('.')[0]):  # Move to next line
                    new_line += 1
                    next_line_text = self.code_editor.get(f"{new_line}.0", f"{new_line}.end")
                    new_col = self.find_next_word_boundary(next_line_text, 0)
                else:
                    new_col = self.find_next_word_boundary(line_text, col)
        else:
            if direction == "left":
                if col == 0 and line > 1:  # Move to previous line
                    new_line = line - 1
                    prev_line_text = self.code_editor.get(f"{new_line}.0", f"{new_line}.end")
                    new_col = len(prev_line_text)
                else:
                    new_line = line
                    new_col = max(0, col - 1)
            else:
                if col >= max_col and line < int(self.code_editor.index('end-1c').split('.')[0]):  # Move to next line
                    new_line = line + 1
                    new_col = 0
                else:
                    new_line = line
                    new_col = min(max_col, col + 1)

        return f"{new_line}.{new_col}"

    def find_previous_word_boundary(self, text, start_pos):
        if start_pos == 0:
            return 0
        
        # If at beginning of empty line, return 0
        if not text:
            return 0
        
        # Adjust for line transitions
        if start_pos > len(text):
            start_pos = len(text)
        
        pos = start_pos - 1
        # Skip whitespace
        while pos > 0 and text[pos].isspace():
            pos -= 1
        
        # Handle word characters
        if text[pos].isalnum() or text[pos] == '_':
            while pos > 0 and (text[pos-1].isalnum() or text[pos-1] == '_'):
                pos -= 1
        else:  # Handle special characters
            while pos > 0 and not (text[pos-1].isalnum() or text[pos-1] == '_'):
                pos -= 1
        
        return pos

    def find_next_word_boundary(self, text, start_pos):
        if start_pos >= len(text):
            return len(text)
        
        # If at end of empty line, return 0
        if not text:
            return 0
        
        pos = start_pos
        # Skip whitespace
        while pos < len(text) and text[pos].isspace():
            pos += 1
        
        # Handle word characters
        if pos < len(text) and (text[pos].isalnum() or text[pos] == '_'):
            while pos < len(text) and (text[pos].isalnum() or text[pos] == '_'):
                pos += 1
        else:  # Handle special characters
            while pos < len(text) and not (text[pos].isalnum() or text[pos] == '_'):
                pos += 1
        
        return pos

    def update_selection_range(self, anchor, cursor):
        self.code_editor.tag_remove("sel", "1.0", "end")
        if anchor != cursor:
            start = min(anchor, cursor, key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1])))
            end = max(anchor, cursor, key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1])))
            self.code_editor.tag_add("sel", start, end)

    def compare_positions(self, pos1, pos2):
        line1, col1 = map(int, pos1.split('.'))
        line2, col2 = map(int, pos2.split('.'))
        return (line1 < line2) or (line1 == line2 and col1 < col2)

    def position_changed_direction(self, anchor, old_pos, new_pos):
        anchor_before_old = self.compare_positions(anchor, old_pos)
        anchor_before_new = self.compare_positions(anchor, new_pos)
        return anchor_before_old != anchor_before_new

    def handle_mouse_click(self, event):
        # Reset selection anchor on click
        self.selection_anchor = None
        self.code_editor.tag_remove("sel", "1.0", "end")

    def extract_code(self, text):
        if '```python' in text:
            parts = text.split('```python')
            if len(parts) > 1:
                return parts[1].split('```')[0].strip()
        elif '```' in text:
            parts = text.split('```')
            if len(parts) >= 3:
                return parts[1].strip()
        return text

    def handle_ai_query(self, event=None):
        """Handle AI code generation request"""
        query = self.AI_search_entry.get().strip()
        if not query:
            self.terminal_output("Please enter your AI query\n", error=True)
            return
        
        # Clear search entry
        self.AI_search_entry.delete(0, tk.END)
        
        self.reopen_terminal()
        # Show processing message
        self.terminal_output("\n[AI] Generating code...Please Wait...\n", error=False)
        
        # Run in background thread
        threading.Thread(target=self.generate_ai_code, args=(query,), daemon=True).start()

    def generate_ai_code(self, query):
        """Generate code using Gemini AI"""
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                query,
                generation_config=self.generation_config
            )
            
            extracted_code = self.extract_code(response.text)
            
            # Update UI in main thread
            self.root.after(0, self.insert_ai_generated_code, extracted_code, response.text)
            
        except Exception as e:
            self.root.after(0, self.show_ai_error, str(e))

    def insert_ai_generated_code(self, code, full_response):
        """Insert generated code into editor"""
        # Copy to clipboard
        pyperclip.copy(code)
        
        # Insert at current cursor position
        self.code_editor.insert(tk.INSERT, code)
        
        # Show full response in terminal
        self.terminal_output(f"[AI Response]\n{full_response}\n", error=False)
        self.terminal_output(f"[Code inserted at cursor position]\n", error=False)
        
        # Flash code insertion point
        self.bg_label.place_forget()
        self.update_line_numbers()
        self.highlight_syntax()
        self.highlight_code_insertion()
        
    def highlight_code_insertion(self):
        """Visual feedback for code insertion"""
        cursor_pos = self.code_editor.index(tk.INSERT)
        self.code_editor.tag_add("ai_code", cursor_pos + "-1c linestart", cursor_pos + " lineend")
        self.code_editor.tag_config("ai_code", background="#2b2b2b")
        self.root.after(2000, lambda: self.code_editor.tag_remove("ai_code", "1.0", tk.END))

    def show_ai_error(self, error_msg):
        """Show error message for AI failures"""
        self.terminal_output(f"[AI Error] {error_msg}\n", error=True)

    def cut_whole_line(self, event):
        cursor_index = self.code_editor.index("insert")
        line_start = f"{cursor_index.split('.')[0]}.0"
        line_end = f"{cursor_index.split('.')[0]}.end"
        
        # Select and cut the entire line
        self.root.clipboard_clear()
        # self.code_editor.tag_add("sel", line_start, line_end)
        self.root.clipboard_append(self.code_editor.get(line_start, line_end))
        self.code_editor.delete(line_start, line_end)

        return "break"  # Prevent default Ctrl+X behavior

    def wrap_selected_text(self, event):
            """Wraps selected text with brackets or quotes when a key is pressed."""
            char = event.char
            pairs = {'"': '"', "'": "'", "(": ")", "{": "}", "[": "]"}

            # Get current selection
            try:
                start = self.code_editor.index(tk.SEL_FIRST)
                end = self.code_editor.index(tk.SEL_LAST)
                selected_text = self.code_editor.get(start, end)
            except tk.TclError:
                return  # No selection, do nothing

            if char in pairs:
                self.code_editor.delete(start, end)  # Remove selected text
                self.code_editor.insert(start, f"{char}{selected_text}{pairs[char]}")  # Wrap with the character
                new_end = self.code_editor.index(f"{start} + {len(selected_text) + 2} chars")
                self.code_editor.tag_add(tk.SEL, start, new_end)  # Update selection

            return "break"  # Prevent default character insertion

    def handle_external_drop(self, event):
        # Handle Windows path formatting with curly braces
        raw_paths = event.data.split()
        cleaned_paths = [p.strip('{}').replace('\\', '/') for p in raw_paths]
        
        for path in cleaned_paths:
            if os.path.isdir(path):
                self.folder_path = os.path.abspath(path)
                folder_name = os.path.basename(self.folder_path)
                self.folder_name_label.config(
                    text=self.truncate_folder_name(folder_name),
                    fg='#ffff00',
                    font=self.font_style
                )
                self.file_tree.delete(*self.file_tree.get_children())
                self.update_file_tree(self.folder_path)
                self.start_file_monitor()
                break  # Only process first valid folder
            elif os.path.isfile(path):
                self.open_file(path)
                break

    def schedule_import_check(self):
        if self.import_check_timer:
            self.root.after_cancel(self.import_check_timer)
        self.import_check_timer = self.root.after(300, self.check_imports)

    def check_imports(self):
        """Real-time import validation with alias handling"""
        self.code_editor.tag_remove("missing_module", "1.0", "end")
        
        try:
            start_idx = self.code_editor.index("@0,0")
            end_idx = self.code_editor.index("@0,10000")
            visible_text = self.code_editor.get(start_idx, end_idx)

            for match in self.import_pattern.finditer(visible_text):
                modules = []
                if match.group(1):  # from ... import
                    base_module = match.group(1).split('.')[0]
                    modules.append(base_module)
                elif match.group(2):  # import ...
                    for m in re.split(r',\s*', match.group(2)):
                        # Handle "as" aliases and split multi-imports
                        module = m.split(' as ')[0].strip()
                        if '.' in module:  # Handle submodules
                            module = module.split('.')[0]
                        modules.append(module)

                for module in modules:
                    if module and not self.is_module_available(module):
                        self.highlight_missing_module(match.start(), start_idx, module)

        except Exception as e:
            self.terminal_output(f"Import check error: {str(e)}\n")

    def is_module_available(self, module_name):
        """Check if a module is installed"""
        if module_name in sys.builtin_module_names:
            return True
        try:
            return importlib.util.find_spec(module_name) is not None
        except ModuleNotFoundError:
            return False
        except Exception as e:
            return False

    def highlight_missing_module(self, offset, start_idx, module):
        """Highlight missing module in visible area"""
        line_start = self.code_editor.index(f"{start_idx}+{offset}c linestart")
        line_end = self.code_editor.index(f"{line_start} lineend")
        line_text = self.code_editor.get(line_start, line_end)
        
        # Find exact module position
        start = line_text.find(module)
        if start != -1:
            end = start + len(module)
            start_pos = f"{line_start}+{start}c"
            end_pos = f"{line_start}+{end}c"
            self.code_editor.tag_add("missing_module", start_pos, end_pos)

    def open_replace_dialog(self, event=None):
        if hasattr(self, 'replace_dialog') and self.replace_dialog.winfo_exists():
            if self.replace_dialog.state() == 'withdrawn':
                self.replace_dialog.deiconify()
            self.replace_dialog.lift()
            self.replace_dialog.focus_set()
            return
                
        self.replace_dialog = self.ReplaceDialog(self)
        self.replace_dialog.protocol("WM_DELETE_WINDOW", self.replace_dialog.on_close)

    def get_script(self):
        """Create Jedi Script with proper environment"""
        code = self.code_editor.get("1.0", tk.END)
        path = self.current_file if self.current_file else None  # Use None for unsaved files
        return jedi.Script(code=code, path=path)

    def get_current_word(self, event):
        """More reliable word detection using Jedi"""
        try:
            x, y = event.x, event.y
            index = self.code_editor.index(f"@{x},{y}")
            line, col = map(int, index.split('.'))
            col += 1  # Jedi columns are 1-based
            
            script = self.get_script()
            names = script.get_references(line, col)
            
            if names:
                return names[0].name
            return self.code_editor.get(f"{index} wordstart", f"{index} wordend")
        except Exception as e:
            return self.code_editor.get(f"{index} wordstart", f"{index} wordend")
        
    def find_definition_position(self, word):
        """Find the line number where the function is defined"""
        content = self.code_editor.get("1.0", tk.END)
        for lineno, line in enumerate(content.split('\n'), 1):
            if re.match(fr'^\s*def\s+{word}\s*\(', line):
                return lineno
        return None

    def jump_to_definition(self, event):
        """Improved Ctrl+Click navigation with proper file handling"""
        try:
            # Get click position
            x, y = event.x, event.y
            index = self.code_editor.index(f"@{x},{y}")
            line, col = map(int, index.split('.'))
            col += 1  # Jedi columns are 1-based

            # Get Jedi script
            script = self.get_script()
            defs = script.goto(line, col, follow_imports=False)

            if not defs:
                self.terminal_output("No definition found\n", error=True)
                return

            first_def = defs[0]
            
            # Handle different definition types
            if first_def.type == 'keyword':
                self.terminal_output(f"'{first_def.name}' is a Python keyword\n")
                return
                
            if first_def.in_builtin_module():
                self.terminal_output(f"'{first_def.name}' is a built-in symbol\n")
                return

            # Check if definition is in current file
            if first_def.module_path != self.current_file:
                if self.current_file:
                    rel_path = os.path.relpath(first_def.module_path, os.path.dirname(self.current_file))
                else:
                    rel_path = first_def.module_path
                self.terminal_output(f"Definition in: {rel_path}\n")
                return

            # Calculate position in editor (Jedi uses 1-based line numbers)
            def_line = first_def.line
            target_index = f"{def_line}.0"

            # Move cursor and scroll to location
            self.code_editor.mark_set(tk.INSERT, target_index)
            self.code_editor.see(target_index)
            
            # Highlight the definition line
            self.code_editor.tag_remove("definition_highlight", "1.0", tk.END)
            self.code_editor.tag_add("definition_highlight", 
                                f"{def_line}.0", f"{def_line}.end")
            self.root.after(2000, lambda: self.code_editor.tag_remove(
                "definition_highlight", "1.0", tk.END))

        except Exception as e:
            self.terminal_output(f"Navigation error: {str(e)}\n", error=True)




    def change_dark_blue_theme(self,e = None):
    
        BACK_GROUND = "#001a33" 
        RUN_BTN = "#1a4897"
        TEXT_WHITE = "white"
        self.BLACK = BACK_GROUND
        FOLDER_NAME_COLOR = '#02f795'
        DATA_TYPE = "#9aff35"   # datatypes = {"str", "int", "float", "bool", "list", "tuple", "dict", "set", "complex", "bytes", "range", "enumerate"} 
        KEYWORD1 = "#fb468a" # keywords1 = {"for", "while", "if", "else", "elif", "try", "except", "finally", "break", "continue", "return", "import", "from", "as", "with", 'input', "lambda", "yield", "global", "nonlocal", "pass", "raise", 'do'}
        KEYWORD2 = "#9CDCFE" #  keywords2 = {"and", "or", "not", "is", "in", "def", 'print', "class", 'True', 'False', 'None', 'NOTE'}
        NON_DATA_TYPE = '#32e79e'
        BRACKET = "#FFD700"
        LINE_NUMBER = '#7c7cef'
        COMMENT = "red"
        
        # =========*******=========*******=========******============
        
        # Top bar
        self.root.config(bg=BACK_GROUND)

        self.top_frame.config(bg=BACK_GROUND)
        self.filename_label.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        self.run_button.config(bg=RUN_BTN, fg=TEXT_WHITE, activebackground=BACK_GROUND)
        self.stop_button.config(bg="red", fg=TEXT_WHITE, activebackground=BACK_GROUND)
        self.AI_search_entry.config(bg=BACK_GROUND, fg=TEXT_WHITE,insertbackground=TEXT_WHITE)
        
        self.file_explorer_toggle_btn.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.word_search_btn.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.toggle_folder_btn.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.file_tree.tag_configure("placeholder", foreground=BACK_GROUND, background=BACK_GROUND)

        self.style.configure(
                            "Treeview", 
                            background=BACK_GROUND, 
                            fieldbackground=BACK_GROUND, 
                            bordercolor="#654321"
                            )
        self.style.configure("Treeview.Heading",
                            background=BACK_GROUND, 
                            )
        self.style.map("Treeview",
                        background=[("selected", BACK_GROUND)]
                       )
        self.style.configure("Custom.Treeview", background=BACK_GROUND,foreground=self.CYAN)
        self.style.configure(
            "Vertical.TScrollbar",
            background=self.CYAN, 
            darkcolor=BACK_GROUND,
            lightcolor=BACK_GROUND,
            troughcolor=BACK_GROUND,
            bordercolor=BACK_GROUND,
            arrowcolor=BACK_GROUND, 
        )
        self.style.map(
            "Vertical.TScrollbar",
            background=[('active', 'magenta')],
            arrowcolor=[('active', self.CYAN)]
        )
        self.style.configure(
            "Horizontal.TScrollbar",
            gripcount=0,
            background=self.CYAN, 
            darkcolor=BACK_GROUND,
            lightcolor=BACK_GROUND,
            troughcolor=BACK_GROUND, 
            bordercolor=BACK_GROUND,
            arrowcolor=BACK_GROUND, 
        )
        self.style.map(
            "Horizontal.TScrollbar",
            background=[('active', 'magenta')], # cyan
            arrowcolor=[('active', self.CYAN)]
        )

        # File tree
        self.folder_tree_frame.config(bg=BACK_GROUND, highlightbackground=BACK_GROUND)

        self.button_frame.config(bg=BACK_GROUND)
        self.button_frame1.config(bg=BACK_GROUND)
        self.folder_name_label.config(bg=BACK_GROUND, fg=FOLDER_NAME_COLOR)
        self.search_frame.config(bg=BACK_GROUND)
        self.tree_search_entry.config(bg=BACK_GROUND, fg=TEXT_WHITE, highlightbackground=BACK_GROUND,insertbackground=TEXT_WHITE)
        self.make_file_button.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.make_folder_button.config(bg=BACK_GROUND,activebackground=BACK_GROUND)

        self.terminal_frame.config(bg=BACK_GROUND)
        self.close_button_frame.config(bg=BACK_GROUND)
        self.close_button.config(bg=BACK_GROUND,activebackground='red',activeforeground=BACK_GROUND)
        self.terminal_delete_button.config(bg=BACK_GROUND,activebackground='red')

        # Editor area
        self.editor_frame.config(bg=BACK_GROUND)
        self.file_tab_canvas.config(bg=BACK_GROUND,highlightcolor=self.CYAN,highlightbackground=self.CYAN)
        self.tab_frame.config(bg=BACK_GROUND)
        self.line_numbers.config(bg=BACK_GROUND, fg=LINE_NUMBER)

        self.code_editor.config(bg=BACK_GROUND, fg=TEXT_WHITE,insertbackground=TEXT_WHITE)
        self.bg_label.config(bg = BACK_GROUND)
        self.suggestion_box.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        self.terminal.config(bg=BACK_GROUND, fg='red')
        self.terminal_label.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        
        # Tabs
        for fp, (container, label, btn) in self.tab_buttons.items():
            container.config(bg=BACK_GROUND)
            label.config(bg=BACK_GROUND, fg=TEXT_WHITE)
            btn.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        # Terminal
        self.terminal_input.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        # Menu bar
        self.menu_bar.config(bg=BACK_GROUND)

        self.file_menu.config(bg=BACK_GROUND,foreground=TEXT_WHITE)
        self.file_menu.delete(0, 'end') 
        self.file_menu.add_command(label="Open File",accelerator="Ctrl+O", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.open_file)
        self.file_menu.add_command(label="Open Folder",accelerator="Ctrl+Shift+O", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.open_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save",accelerator="Ctrl+S", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.save_file)
        self.file_menu.add_command(label="Save As",accelerator="Ctrl+Shift+S", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.save_as_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='red', command=self.exit_editor)

        self.edit_menu.config(bg=BACK_GROUND,foreground=TEXT_WHITE)
        self.edit_menu.delete(0, 'end') 
        self.edit_menu.add_command(label="Undo",accelerator="Ctrl+Z", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.safe_undo)
        self.edit_menu.add_command(label="Redo",accelerator="Ctrl+Y", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.safe_redo)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut",accelerator="Ctrl+X", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.cut_text)
        self.edit_menu.add_command(label="Copy",accelerator="Ctrl+C", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.copy_text)
        self.edit_menu.add_command(label="Paste",accelerator="Ctrl+V", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.paste_text)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Rename",accelerator="F2", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.start_rename_via_shortcut)
        self.edit_menu.add_command(label="Search",accelerator="F3", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.open_search_bar)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Zoom In",accelerator="Ctrl++", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.increase_text_size)
        self.edit_menu.add_command(label="Zoom Out",accelerator="Ctrl+-", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.decrease_text_size)

        self.run_menu.config(bg=BACK_GROUND,foreground=TEXT_WHITE)
        self.run_menu.delete(0, 'end') 
        self.run_menu.add_command(label="Run",accelerator="Alt+S", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.run_code)
        self.run_menu.add_separator()
        self.run_menu.add_command(label="Stop Running... ",accelerator="Ctrl+Q", font=self.menu_bar_font_style, background='red', foreground='white', command=self.stop_code)

        self.terminal_menu.config(bg=BACK_GROUND,fg=TEXT_WHITE)
        self.terminal_menu.delete(0, 'end')
        self.terminal_menu.add_command(label="Show Terminal",accelerator="Ctrl+Shift+T", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.reopen_terminal)
        self.terminal_menu.add_command(label="Clear Terminal",accelerator="Ctrl+Shift+C", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.terminal_delete_clear)
        self.terminal_menu.add_separator()
        self.terminal_menu.add_command(label="New Terminal",accelerator="Ctrl+Shift+`", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='white', command=self.open_new_terminal)

        self.theme_menu.config(background=BACK_GROUND,fg=TEXT_WHITE)
        self.theme_menu.delete(0, 'end')
        self.theme_menu.add_command(label="Dark Blue    ",image=self.dark_blue_icon, compound='right', command=self.change_dark_blue_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Black        ",image=self.black_icon, compound='right',command=self.change_dark_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Dark Green   ",image=self.dark_green_icon, compound='right',command=self.change_dark_green_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Dark Gray    ",image=self.dark_gray_icon, compound='right',command=self.change_dark_gray_theme)
                     
        self.syntax_colors = {
            "data_type": DATA_TYPE,  # Teal
            "keyword1": KEYWORD1,   # Blue
            "keyword2": KEYWORD2,   # Light Blue
            "non_data_type": NON_DATA_TYPE,  # magenta
            "bracket":BRACKET     # Gold
        }
        self.syntax_colors.update({
            "comment": COMMENT,
            "comment_bracket": COMMENT,
        })
        self.code_editor.tag_config("comment", foreground=self.syntax_colors["comment"])
        self.code_editor.tag_config("comment_bracket", foreground=self.syntax_colors["comment_bracket"])
        # Force syntax re-highlight
        self._highlight_syntax()
        if hasattr(self, 'replace_dialog') and self.replace_dialog.winfo_exists():
            self.replace_dialog.update_theme()
        self.root.update()
        
    def change_dark_theme(self,e = None):
    
        BACK_GROUND = "black"
        RUN_BTN = "#3e3e3e"
        TEXT_WHITE = "white"
        self.BLACK = BACK_GROUND
        FOLDER_NAME_COLOR = 'yellow'
        DATA_TYPE = "#03f34a" # datatypes = {"str", "int", "float", "bool", "list", "tuple", "dict", "set", "complex", "bytes", "range", "enumerate"} 
        KEYWORD1 = "#ff00ff" # keywords1 = {"for", "while", "if", "else", "elif", "try", "except", "finally", "break", "continue", "return", "import", "from", "as", "with", 'input', "lambda", "yield", "global", "nonlocal", "pass", "raise", 'do'}
        KEYWORD2 = "blue" #  keywords2 = {"and", "or", "not", "is", "in", "def", 'print', "class", 'True', 'False', 'None', 'NOTE'}
        NON_DATA_TYPE = 'cyan'
        BRACKET = "yellow"
        LINE_NUMBER = '#7bdc5e'
        COMMENT = "green"
        
        # =========*******=========*******=========******============
        
        # Top bar
        self.root.config(bg=BACK_GROUND)

        self.top_frame.config(bg=BACK_GROUND)
        self.filename_label.config(background=BACK_GROUND, fg=TEXT_WHITE)
        self.run_button.config(bg=RUN_BTN, fg=TEXT_WHITE, activebackground=BACK_GROUND)
        self.stop_button.config(bg="red", fg=TEXT_WHITE, activebackground=BACK_GROUND)
        self.AI_search_entry.config(bg=BACK_GROUND, fg=TEXT_WHITE,insertbackground=TEXT_WHITE)
        
        self.file_explorer_toggle_btn.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.word_search_btn.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.toggle_folder_btn.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.file_tree.tag_configure("placeholder", foreground=BACK_GROUND, background=BACK_GROUND)

        
        self.style.configure(
                            "Treeview", 
                            background=BACK_GROUND, 
                            fieldbackground=BACK_GROUND, 
                            bordercolor="#654321"
                            )
        self.style.configure("Treeview.Heading",
                            background=BACK_GROUND, 
                            )
        self.style.map("Treeview",
                        background=[("selected", BACK_GROUND)]
                       )
        self.style.configure("Custom.Treeview", background=BACK_GROUND,foreground=self.CYAN)
        self.style.configure(
            "Vertical.TScrollbar",
            background=self.CYAN, 
            darkcolor=BACK_GROUND,
            lightcolor=BACK_GROUND,
            troughcolor=BACK_GROUND,
            bordercolor=BACK_GROUND,
            arrowcolor=BACK_GROUND, 
        )
        self.style.map(
            "Vertical.TScrollbar",
            background=[('active', 'magenta')],
            arrowcolor=[('active', self.CYAN)]
        )
        self.style.configure(
            "Horizontal.TScrollbar",
            gripcount=0,
            background=self.CYAN, 
            darkcolor=BACK_GROUND,
            lightcolor=BACK_GROUND,
            troughcolor=BACK_GROUND, 
            bordercolor=BACK_GROUND,
            arrowcolor=BACK_GROUND, 
        )
        self.style.map(
            "Horizontal.TScrollbar",
            background=[('active', 'magenta')], # cyan
            arrowcolor=[('active', self.CYAN)]
        )

        # File tree
        self.folder_tree_frame.config(bg=BACK_GROUND, highlightbackground=BACK_GROUND)

        self.button_frame.config(bg=BACK_GROUND)
        self.button_frame1.config(bg=BACK_GROUND)
        self.folder_name_label.config(bg=BACK_GROUND, fg=FOLDER_NAME_COLOR)
        self.search_frame.config(bg=BACK_GROUND)
        self.tree_search_entry.config(bg=BACK_GROUND, fg=TEXT_WHITE, highlightbackground=BACK_GROUND,insertbackground=TEXT_WHITE)
        self.make_file_button.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.make_folder_button.config(bg=BACK_GROUND,activebackground=BACK_GROUND)

        self.terminal_frame.config(bg=BACK_GROUND)
        self.close_button_frame.config(bg=BACK_GROUND)
        self.close_button.config(bg=BACK_GROUND,activebackground='red',activeforeground=BACK_GROUND)
        self.terminal_delete_button.config(bg=BACK_GROUND,activebackground='red')

        # Editor area
        self.editor_frame.config(bg=BACK_GROUND)
        self.file_tab_canvas.config(bg=BACK_GROUND,highlightcolor=self.CYAN,highlightbackground=self.CYAN)
        self.tab_frame.config(bg=BACK_GROUND)
        self.line_numbers.config(bg=BACK_GROUND, fg=LINE_NUMBER)




        self.code_editor.config(bg=BACK_GROUND, fg=TEXT_WHITE,insertbackground=TEXT_WHITE)
        self.bg_label.config(bg = BACK_GROUND)
        self.suggestion_box.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        self.terminal.config(bg=BACK_GROUND, fg='red')
        self.terminal_label.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        
        # Tabs
        for fp, (container, label, btn) in self.tab_buttons.items():
            container.config(bg=BACK_GROUND)
            label.config(bg=BACK_GROUND, fg=TEXT_WHITE)
            btn.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        
        # Terminal
        self.terminal_input.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        
        # Menu bar
        self.menu_bar.config(bg=BACK_GROUND)

        self.file_menu.config(bg=BACK_GROUND,foreground=TEXT_WHITE)
        self.file_menu.delete(0, 'end') 
        self.file_menu.add_command(label="Open File",accelerator="Ctrl+O", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.open_file)
        self.file_menu.add_command(label="Open Folder",accelerator="Ctrl+Shift+O", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.open_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save",accelerator="Ctrl+S", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.save_file)
        self.file_menu.add_command(label="Save As",accelerator="Ctrl+Shift+S", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.save_as_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='red', command=self.exit_editor)

        self.edit_menu.config(bg=BACK_GROUND,foreground=TEXT_WHITE)
        self.edit_menu.delete(0, 'end') 
        self.edit_menu.add_command(label="Undo",accelerator="Ctrl+Z", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.safe_undo)
        self.edit_menu.add_command(label="Redo",accelerator="Ctrl+Y", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.safe_redo)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut",accelerator="Ctrl+X", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.cut_text)
        self.edit_menu.add_command(label="Copy",accelerator="Ctrl+C", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.copy_text)
        self.edit_menu.add_command(label="Paste",accelerator="Ctrl+V", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.paste_text)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Rename",accelerator="F2", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.start_rename_via_shortcut)
        self.edit_menu.add_command(label="Search",accelerator="F3", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.open_search_bar)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Zoom In",accelerator="Ctrl++", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.increase_text_size)
        self.edit_menu.add_command(label="Zoom Out",accelerator="Ctrl+-", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.decrease_text_size)

        self.run_menu.config(bg=BACK_GROUND,foreground=TEXT_WHITE)
        self.run_menu.delete(0, 'end') 
        self.run_menu.add_command(label="Run",accelerator="Alt+S", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.run_code)
        self.run_menu.add_separator()
        self.run_menu.add_command(label="Stop Running... ",accelerator="Ctrl+Q", font=self.menu_bar_font_style, background='red', foreground=TEXT_WHITE, command=self.stop_code)

        self.terminal_menu.config(bg=BACK_GROUND,fg=TEXT_WHITE)
        self.terminal_menu.delete(0, 'end')
        self.terminal_menu.add_command(label="Show Terminal",accelerator="Ctrl+Shift+T", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.reopen_terminal)
        self.terminal_menu.add_command(label="Clear Terminal",accelerator="Ctrl+Shift+C", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.terminal_delete_clear)
        self.terminal_menu.add_separator()
        self.terminal_menu.add_command(label="New Terminal",accelerator="Ctrl+Shift+`", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.open_new_terminal)

        self.theme_menu.config(background=BACK_GROUND,fg=TEXT_WHITE)
        self.theme_menu.delete(0, 'end')
        self.theme_menu.add_command(label="Dark Blue    ",image=self.dark_blue_icon, compound='right', command=self.change_dark_blue_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Black        ",image=self.black_icon, compound='right',command=self.change_dark_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Dark Green   ",image=self.dark_green_icon, compound='right',command=self.change_dark_green_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Dark Gray    ",image=self.dark_gray_icon, compound='right',command=self.change_dark_gray_theme)
        
          
   
        self.syntax_colors = {
            "data_type": DATA_TYPE,  # Teal
            "keyword1": KEYWORD1,   # Blue
            "keyword2": KEYWORD2,   # Light Blue
            "non_data_type": NON_DATA_TYPE,  # magenta
            "bracket":BRACKET     # Gold
        }
        self.syntax_colors.update({
            "comment": COMMENT,
            "comment_bracket": COMMENT,
        })
        self.code_editor.tag_config("comment", foreground=self.syntax_colors["comment"])
        self.code_editor.tag_config("comment_bracket", foreground=self.syntax_colors["comment_bracket"])
        # Force syntax re-highlight
        self._highlight_syntax()
        
        self.root.update()
        if hasattr(self, 'replace_dialog') and self.replace_dialog.winfo_exists():
            self.replace_dialog.update_theme()
                
    def change_dark_green_theme(self,e = None):
    
        BACK_GROUND = "#062000"
        RUN_BTN = "#3a5f23"
        TEXT_WHITE = "white"
        self.BLACK = BACK_GROUND
        FOLDER_NAME_COLOR = '#71fa0c'
        DATA_TYPE = "#fc83fc" # datatypes = {"str", "int", "float", "bool", "list", "tuple", "dict", "set", "complex", "bytes", "range", "enumerate"} 
        KEYWORD1 = "#ff40ff" # keywords1 = {"for", "while", "if", "else", "elif", "try", "except", "finally", "break", "continue", "return", "import", "from", "as", "with", 'input', "lambda", "yield", "global", "nonlocal", "pass", "raise", 'do'}
        KEYWORD2 = "#8af4af" #  keywords2 = {"and", "or", "not", "is", "in", "def", 'print', "class", 'True', 'False', 'None', 'NOTE'}
        NON_DATA_TYPE = '#ff8040'
        BRACKET = "yellow"
        LINE_NUMBER = '#1ab5c6'
        COMMENT = 'red'
        
        # =========*******=========*******=========******============

        
        
        # Top bar
        self.root.config(bg=BACK_GROUND)

        self.top_frame.config(bg=BACK_GROUND)
        self.filename_label.config(background=BACK_GROUND, fg=TEXT_WHITE)
        self.run_button.config(bg=RUN_BTN, fg=TEXT_WHITE, activebackground=BACK_GROUND)
        self.stop_button.config(bg="red", fg=TEXT_WHITE, activebackground=BACK_GROUND)
        self.AI_search_entry.config(bg=BACK_GROUND, fg=TEXT_WHITE,insertbackground=TEXT_WHITE)
        
        self.file_explorer_toggle_btn.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.word_search_btn.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.toggle_folder_btn.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.file_tree.tag_configure("placeholder", foreground=BACK_GROUND, background=BACK_GROUND)



        self.style.configure(
                            "Treeview", 
                            background=BACK_GROUND, 
                            fieldbackground=BACK_GROUND, 
                            bordercolor="#654321"
                            )
        self.style.configure("Treeview.Heading",
                            background=BACK_GROUND, 
                            )
        self.style.map("Treeview",
                        background=[("selected", BACK_GROUND)]
                       )
        self.style.configure("Custom.Treeview", background=BACK_GROUND,foreground=self.CYAN)
        self.style.configure(
            "Vertical.TScrollbar",
            background=self.CYAN, 
            darkcolor=BACK_GROUND,
            lightcolor=BACK_GROUND,
            troughcolor=BACK_GROUND,
            bordercolor=BACK_GROUND,
            arrowcolor=BACK_GROUND, 
        )
        self.style.map(
            "Vertical.TScrollbar",
            background=[('active', 'magenta')],
            arrowcolor=[('active', self.CYAN)]
        )
        self.style.configure(
            "Horizontal.TScrollbar",
            gripcount=0,
            background=self.CYAN, 
            darkcolor=BACK_GROUND,
            lightcolor=BACK_GROUND,
            troughcolor=BACK_GROUND, 
            bordercolor=BACK_GROUND,
            arrowcolor=BACK_GROUND, 
        )
        self.style.map(
            "Horizontal.TScrollbar",
            background=[('active', 'magenta')], # cyan
            arrowcolor=[('active', self.CYAN)]
        )

        # File tree
        self.folder_tree_frame.config(bg=BACK_GROUND, highlightbackground=BACK_GROUND)

        self.button_frame.config(bg=BACK_GROUND)
        self.button_frame1.config(bg=BACK_GROUND)
        self.folder_name_label.config(bg=BACK_GROUND, fg=FOLDER_NAME_COLOR)
        self.search_frame.config(bg=BACK_GROUND)
        self.tree_search_entry.config(bg=BACK_GROUND, fg=TEXT_WHITE, highlightbackground=BACK_GROUND,insertbackground=TEXT_WHITE)
        self.make_file_button.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.make_folder_button.config(bg=BACK_GROUND,activebackground=BACK_GROUND)

        self.terminal_frame.config(bg=BACK_GROUND)
        self.close_button_frame.config(bg=BACK_GROUND)
        self.close_button.config(bg=BACK_GROUND,activebackground='red',activeforeground=BACK_GROUND)
        self.terminal_delete_button.config(bg=BACK_GROUND,activebackground='red')

        # Editor area
        self.editor_frame.config(bg=BACK_GROUND)
        self.file_tab_canvas.config(bg=BACK_GROUND,highlightcolor=self.CYAN,highlightbackground=self.CYAN)
        self.tab_frame.config(bg=BACK_GROUND)
        self.line_numbers.config(bg=BACK_GROUND, fg=LINE_NUMBER)




        self.code_editor.config(bg=BACK_GROUND, fg=TEXT_WHITE,insertbackground=TEXT_WHITE)
        self.bg_label.config(bg = BACK_GROUND)
        self.suggestion_box.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        self.terminal.config(bg=BACK_GROUND, fg='red')
        self.terminal_label.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        
        # Tabs
        for fp, (container, label, btn) in self.tab_buttons.items():
            container.config(bg=BACK_GROUND)
            label.config(bg=BACK_GROUND, fg=TEXT_WHITE)
            btn.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        
        # Terminal
        self.terminal_input.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        
        # Menu bar
        self.menu_bar.config(bg=BACK_GROUND)

        self.file_menu.config(bg=BACK_GROUND,foreground=TEXT_WHITE)
        self.file_menu.delete(0, 'end') 
        self.file_menu.add_command(label="Open File",accelerator="Ctrl+O", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.open_file)
        self.file_menu.add_command(label="Open Folder",accelerator="Ctrl+Shift+O", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.open_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save",accelerator="Ctrl+S", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.save_file)
        self.file_menu.add_command(label="Save As",accelerator="Ctrl+Shift+S", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.save_as_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='red', command=self.exit_editor)

        self.edit_menu.config(bg=BACK_GROUND,foreground=TEXT_WHITE)
        self.edit_menu.delete(0, 'end') 
        self.edit_menu.add_command(label="Undo",accelerator="Ctrl+Z", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.safe_undo)
        self.edit_menu.add_command(label="Redo",accelerator="Ctrl+Y", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.safe_redo)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut",accelerator="Ctrl+X", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.cut_text)
        self.edit_menu.add_command(label="Copy",accelerator="Ctrl+C", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.copy_text)
        self.edit_menu.add_command(label="Paste",accelerator="Ctrl+V", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.paste_text)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Rename",accelerator="F2", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.start_rename_via_shortcut)
        self.edit_menu.add_command(label="Search",accelerator="F3", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.open_search_bar)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Zoom In",accelerator="Ctrl++", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.increase_text_size)
        self.edit_menu.add_command(label="Zoom Out",accelerator="Ctrl+-", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.decrease_text_size)

        self.run_menu.config(bg=BACK_GROUND,foreground=TEXT_WHITE)
        self.run_menu.delete(0, 'end') 
        self.run_menu.add_command(label="Run",accelerator="Alt+S", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.run_code)
        self.run_menu.add_separator()
        self.run_menu.add_command(label="Stop Running... ",accelerator="Ctrl+Q", font=self.menu_bar_font_style, background='red', foreground=TEXT_WHITE, command=self.stop_code)

        self.terminal_menu.config(bg=BACK_GROUND,fg=TEXT_WHITE)
        self.terminal_menu.delete(0, 'end')
        self.terminal_menu.add_command(label="Show Terminal",accelerator="Ctrl+Shift+T", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.reopen_terminal)
        self.terminal_menu.add_command(label="Clear Terminal",accelerator="Ctrl+Shift+C", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.terminal_delete_clear)
        self.terminal_menu.add_separator()
        self.terminal_menu.add_command(label="New Terminal",accelerator="Ctrl+Shift+`", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.open_new_terminal)

        self.theme_menu.config(background=BACK_GROUND,fg=TEXT_WHITE)
        self.theme_menu.delete(0, 'end')
        self.theme_menu.add_command(label="Dark Blue    ",image=self.dark_blue_icon, compound='right', command=self.change_dark_blue_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Black        ",image=self.black_icon, compound='right',command=self.change_dark_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Dark Green   ",image=self.dark_green_icon, compound='right',command=self.change_dark_green_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Dark Gray    ",image=self.dark_gray_icon, compound='right',command=self.change_dark_gray_theme)
        
          
   
        self.syntax_colors = {
            "data_type": DATA_TYPE,  # Teal
            "keyword1": KEYWORD1,   # Blue
            "keyword2": KEYWORD2,   # Light Blue
            "non_data_type": NON_DATA_TYPE,  # magenta
            "bracket":BRACKET     # Gold
        }
        self.syntax_colors.update({
            "comment": COMMENT,
            "comment_bracket": COMMENT,
        })
        self.code_editor.tag_config("comment", foreground=self.syntax_colors["comment"])
        self.code_editor.tag_config("comment_bracket", foreground=self.syntax_colors["comment_bracket"])

        self._highlight_syntax()
        
        self.root.update()
        if hasattr(self, 'replace_dialog') and self.replace_dialog.winfo_exists():
            self.replace_dialog.update_theme()
                        
    def change_dark_gray_theme(self,e = None):
    
        BACK_GROUND = "#242424"
        RUN_BTN = "#939393"
        TEXT_WHITE = "white"
        self.BLACK = BACK_GROUND
        FOLDER_NAME_COLOR = '#fa43c8'
        DATA_TYPE = "#00ffff" # datatypes = {"str", "int", "float", "bool", "list", "tuple", "dict", "set", "complex", "bytes", "range", "enumerate"} 
        KEYWORD1 = "#ffff00" # keywords1 = {"for", "while", "if", "else", "elif", "try", "except", "finally", "break", "continue", "return", "import", "from", "as", "with", 'input', "lambda", "yield", "global", "nonlocal", "pass", "raise", 'do'}
        KEYWORD2 = "#ff0000" #  keywords2 = {"and", "or", "not", "is", "in", "def", 'print', "class", 'True', 'False', 'None', 'NOTE'}
        NON_DATA_TYPE = '#ff77bb'
        BRACKET = "#ff8040"
        LINE_NUMBER = '#00ff00'
        COMMENT = '#00ff00'
        
        # =========*******=========*******=========******============
       
        
        # Top bar
        self.root.config(bg=BACK_GROUND)

        self.top_frame.config(bg=BACK_GROUND)
        self.filename_label.config(background=BACK_GROUND, fg=TEXT_WHITE)
        self.run_button.config(bg=RUN_BTN, fg=TEXT_WHITE, activebackground=BACK_GROUND)
        self.stop_button.config(bg="red", fg=TEXT_WHITE, activebackground=BACK_GROUND)
        self.AI_search_entry.config(bg=BACK_GROUND, fg=TEXT_WHITE,insertbackground=TEXT_WHITE)
        
        self.file_explorer_toggle_btn.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.word_search_btn.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.toggle_folder_btn.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.file_tree.tag_configure("placeholder", foreground=BACK_GROUND, background=BACK_GROUND)



        self.style.configure(
                            "Treeview", 
                            background=BACK_GROUND, 
                            fieldbackground=BACK_GROUND, 
                            bordercolor="#654321"
                            )
        self.style.configure("Treeview.Heading",
                            background=BACK_GROUND, 
                            )
        self.style.map("Treeview",
                        background=[("selected", BACK_GROUND)]
                       )
        self.style.configure("Custom.Treeview", background=BACK_GROUND,foreground=self.CYAN)
        self.style.configure(
            "Vertical.TScrollbar",
            background=self.CYAN, 
            darkcolor=BACK_GROUND,
            lightcolor=BACK_GROUND,
            troughcolor=BACK_GROUND,
            bordercolor=BACK_GROUND,
            arrowcolor=BACK_GROUND, 
        )
        self.style.map(
            "Vertical.TScrollbar",
            background=[('active', 'magenta')],
            arrowcolor=[('active', self.CYAN)]
        )
        self.style.configure(
            "Horizontal.TScrollbar",
            gripcount=0,
            background=self.CYAN, 
            darkcolor=BACK_GROUND,
            lightcolor=BACK_GROUND,
            troughcolor=BACK_GROUND, 
            bordercolor=BACK_GROUND,
            arrowcolor=BACK_GROUND, 
        )
        self.style.map(
            "Horizontal.TScrollbar",
            background=[('active', 'magenta')], # cyan
            arrowcolor=[('active', self.CYAN)]
        )

        # File tree
        self.folder_tree_frame.config(bg=BACK_GROUND, highlightbackground=BACK_GROUND)

        self.button_frame.config(bg=BACK_GROUND)
        self.button_frame1.config(bg=BACK_GROUND)
        self.folder_name_label.config(bg=BACK_GROUND, fg=FOLDER_NAME_COLOR)
        self.search_frame.config(bg=BACK_GROUND)
        self.tree_search_entry.config(bg=BACK_GROUND, fg=TEXT_WHITE, highlightbackground=BACK_GROUND,insertbackground=TEXT_WHITE)
        self.make_file_button.config(bg=BACK_GROUND,activebackground=BACK_GROUND)
        self.make_folder_button.config(bg=BACK_GROUND,activebackground=BACK_GROUND)

        self.terminal_frame.config(bg=BACK_GROUND)
        self.close_button_frame.config(bg=BACK_GROUND)
        self.close_button.config(bg=BACK_GROUND,activebackground='red',activeforeground=BACK_GROUND)
        self.terminal_delete_button.config(bg=BACK_GROUND,activebackground='red')

        # Editor area
        self.editor_frame.config(bg=BACK_GROUND)
        self.file_tab_canvas.config(bg=BACK_GROUND,highlightcolor=self.CYAN,highlightbackground=self.CYAN)
        self.tab_frame.config(bg=BACK_GROUND)
        self.line_numbers.config(bg=BACK_GROUND, fg=LINE_NUMBER)




        self.code_editor.config(bg=BACK_GROUND, fg=TEXT_WHITE,insertbackground=TEXT_WHITE)
        self.bg_label.config(bg = BACK_GROUND)
        self.suggestion_box.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        self.terminal.config(bg=BACK_GROUND, fg='red')
        self.terminal_label.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        
        # Tabs
        for fp, (container, label, btn) in self.tab_buttons.items():
            container.config(bg=BACK_GROUND)
            label.config(bg=BACK_GROUND, fg=TEXT_WHITE)
            btn.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        
        # Terminal
        self.terminal_input.config(bg=BACK_GROUND, fg=TEXT_WHITE)
        
        # Menu bar
        self.menu_bar.config(bg=BACK_GROUND)

        self.file_menu.config(bg=BACK_GROUND,foreground=TEXT_WHITE)
        self.file_menu.delete(0, 'end') 
        self.file_menu.add_command(label="Open File",accelerator="Ctrl+O", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.open_file)
        self.file_menu.add_command(label="Open Folder",accelerator="Ctrl+Shift+O", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.open_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save",accelerator="Ctrl+S", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.save_file)
        self.file_menu.add_command(label="Save As",accelerator="Ctrl+Shift+S", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.save_as_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", font=self.menu_bar_font_style, background=BACK_GROUND, foreground='red', command=self.exit_editor)

        self.edit_menu.config(bg=BACK_GROUND,foreground=TEXT_WHITE)
        self.edit_menu.delete(0, 'end') 
        self.edit_menu.add_command(label="Undo",accelerator="Ctrl+Z", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.safe_undo)
        self.edit_menu.add_command(label="Redo",accelerator="Ctrl+Y", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.safe_redo)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut",accelerator="Ctrl+X", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.cut_text)
        self.edit_menu.add_command(label="Copy",accelerator="Ctrl+C", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.copy_text)
        self.edit_menu.add_command(label="Paste",accelerator="Ctrl+V", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.paste_text)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Rename",accelerator="F2", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.start_rename_via_shortcut)
        self.edit_menu.add_command(label="Search",accelerator="F3", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.open_search_bar)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Zoom In",accelerator="Ctrl++", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.increase_text_size)
        self.edit_menu.add_command(label="Zoom Out",accelerator="Ctrl+-", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.decrease_text_size)

        self.run_menu.config(bg=BACK_GROUND,foreground=TEXT_WHITE)
        self.run_menu.delete(0, 'end') 
        self.run_menu.add_command(label="Run",accelerator="Alt+S", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.run_code)
        self.run_menu.add_separator()
        self.run_menu.add_command(label="Stop Running... ",accelerator="Ctrl+Q", font=self.menu_bar_font_style, background='red', foreground=TEXT_WHITE, command=self.stop_code)

        self.terminal_menu.config(bg=BACK_GROUND,fg=TEXT_WHITE)
        self.terminal_menu.delete(0, 'end')
        self.terminal_menu.add_command(label="Show Terminal",accelerator="Ctrl+Shift+T", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.reopen_terminal)
        self.terminal_menu.add_command(label="Clear Terminal",accelerator="Ctrl+Shift+C", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.terminal_delete_clear)
        self.terminal_menu.add_separator()
        self.terminal_menu.add_command(label="New Terminal",accelerator="Ctrl+Shift+`", font=self.menu_bar_font_style, background=BACK_GROUND, foreground=TEXT_WHITE, command=self.open_new_terminal)

        self.theme_menu.config(background=BACK_GROUND,fg=TEXT_WHITE)
        self.theme_menu.delete(0, 'end')
        self.theme_menu.add_command(label="Dark Blue    ",image=self.dark_blue_icon, compound='right', command=self.change_dark_blue_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Black        ",image=self.black_icon, compound='right',command=self.change_dark_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Dark Green   ",image=self.dark_green_icon, compound='right',command=self.change_dark_green_theme)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="Dark Gray    ",image=self.dark_gray_icon, compound='right',command=self.change_dark_gray_theme)
        
          
   
        self.syntax_colors = {
            "data_type": DATA_TYPE,  # Teal
            "keyword1": KEYWORD1,   # Blue
            "keyword2": KEYWORD2,   # Light Blue
            "non_data_type": NON_DATA_TYPE,  # magenta
            "bracket":BRACKET     # Gold
        }
        self.syntax_colors.update({
            "comment": COMMENT,
            "comment_bracket": COMMENT,
        })
        self.code_editor.tag_config("comment", foreground=self.syntax_colors["comment"])
        self.code_editor.tag_config("comment_bracket", foreground=self.syntax_colors["comment_bracket"])

        if hasattr(self, 'replace_dialog') and self.replace_dialog.winfo_exists():
            self.replace_dialog.update_theme()
        
        self._highlight_syntax()
        
        self.root.update()
        















if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Execute the script passed as an argument
        script_path = sys.argv[1]
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        exec(script_content, {'__name__': '__main__'})
    else:
        # Start the editor GUI
        
        root = TkinterDnD.Tk()
        VSCodeLikeEditor(root)
        root.mainloop()



