import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import subprocess
import configparser
import time
import ctypes
import sys
from threading import Thread

class GameLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("WhyNot Launcher")
        self.root.geometry("640x480")

        icon_path = os.path.join(os.path.dirname(__file__), 'whynoticon.ico')
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        self.gradient_color1 = "#7d53de"
        self.gradient_color2 = "#4826b1"

        style = ttk.Style()
        style.theme_use('clam')  
        style.configure("TFrame", background=self.gradient_color1)
        style.configure("TNotebook", background=self.gradient_color1)
        style.configure("TNotebook.Tab", background=self.gradient_color1, foreground="white")
        style.map("TNotebook.Tab", background=[("selected", self.gradient_color2)], foreground=[("selected", "white")])

        self.config_file = "games.cfg"
        self.games = {}
        self.current_profile = "User"
        self.game_process = None
        self.start_time = None

        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(expand=1, fill="both")

        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab_control.pack(expand=1, fill="both", side=tk.TOP)

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.add_tab_button = ttk.Button(self.button_frame, text="+", width=3, command=self.add_game)
        self.add_tab_button.pack(padx=5, pady=5)

        self.remove_tab_button = ttk.Button(self.button_frame, text="-", width=3, command=self.remove_game)
        self.remove_tab_button.pack(padx=5, pady=5)

        self.profile_label = ttk.Label(self.main_frame, text=f"Profile: {self.current_profile}")
        self.profile_label.pack(side=tk.BOTTOM, pady=10)

        self.change_profile_button = ttk.Button(self.main_frame, text="Change Profile", command=self.change_profile)
        self.change_profile_button.pack(side=tk.BOTTOM, pady=5)

        self.tab_control.bind('<Configure>', self.reposition_buttons)

        self.load_config()

    def reposition_buttons(self, event=None):
        self.add_tab_button.lift(self.tab_control)
        self.remove_tab_button.lift(self.tab_control)

    def add_game(self):
        add_game_window = tk.Toplevel(self.root)
        add_game_window.title("Add Game")
        add_game_window.attributes('-topmost', True)  
        
        tk.Label(add_game_window, text="Path to .exe:").pack(pady=10)
        
        self.path_entry = tk.Entry(add_game_window, width=50)
        self.path_entry.pack(padx=10)
        
        browse_button = ttk.Button(add_game_window, text="Browse", command=self.browse_file)
        browse_button.pack(pady=5)

        add_button = ttk.Button(add_game_window, text="Add", command=lambda: self.create_game_tab(add_game_window))
        add_button.pack(pady=10)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
        if file_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, file_path)

    def create_game_tab(self, add_game_window):
        game_path = self.path_entry.get()
        if not os.path.isfile(game_path):
            messagebox.showerror("Error", "Invalid path to .exe file.")
            return
        
        game_name = os.path.basename(game_path).replace('.exe', '')
        
        if game_name in self.games:
            messagebox.showerror("Error", "Game already added.")
            return
        
        self.add_game_tab(game_name, game_path)
        self.games[game_name] = {"path": game_path, "time_spent": 0}
        self.save_config()

        add_game_window.destroy()
        self.reposition_buttons()

    def add_game_tab(self, game_name, game_path, time_spent=0):
        new_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(new_tab, text=game_name)
        
        tk.Label(new_tab, text=game_name, font=("Arial", 16), background=self.gradient_color1, foreground="white").pack(pady=10)
        
        time_label = tk.Label(new_tab, text=self.format_time(time_spent), font=("Arial", 12), background=self.gradient_color1, foreground="white")
        time_label.pack(pady=5)
        
        play_button = ttk.Button(new_tab, text="Play", command=lambda: self.play_game(game_name, game_path, time_label))
        play_button.pack(pady=10)

    def play_game(self, game_name, game_path, time_label):
        if not ctypes.windll.shell32.IsUserAnAdmin():
            if not messagebox.askyesno("Administrator privileges required", "This program needs to be run with administrator privileges to launch games. Do you want to continue?"):
                return
        
        self.start_time = time.time()
        try:
            self.game_process = subprocess.Popen(game_path, shell=True)
            Thread(target=self.wait_for_game_to_finish, args=(game_name, time_label)).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch game: {e}")

    def wait_for_game_to_finish(self, game_name, time_label):
        self.game_process.wait()
        end_time = time.time()
        time_spent = end_time - self.start_time


        self.games[game_name]["time_spent"] += time_spent
        self.save_config()

        time_label.config(text=self.format_time(self.games[game_name]['time_spent']))

    def save_config(self):
        config = configparser.ConfigParser()
        config['Profile'] = {'Name': self.current_profile}
        config['Games'] = {game: f"{self.games[game]['path']}|{self.games[game]['time_spent']}" for game in self.games}
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)

    def load_config(self):
        if os.path.exists(self.config_file):
            config = configparser.ConfigParser()
            config.read(self.config_file)
            if 'Profile' in config:
                self.current_profile = config['Profile'].get('Name', 'User')
                self.profile_label.config(text=f"Profile: {self.current_profile}")
            
            if 'Games' in config:
                for game_name, value in config['Games'].items():
                    path, time_spent = value.split('|')
                    self.games[game_name] = {"path": path, "time_spent": float(time_spent)}
                    self.add_game_tab(game_name, path, float(time_spent))

    def remove_game(self):
        selected_tab = self.tab_control.select()
        if not selected_tab:
            messagebox.showerror("Error", "No game selected.")
            return
        
        game_name = self.tab_control.tab(selected_tab, "text")
        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to remove {game_name}?")
        if confirm:
            self.tab_control.forget(selected_tab)
            if game_name in self.games:
                del self.games[game_name]
                self.save_config()

    def format_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"Time spent: {hours}h {minutes}m {seconds}s"

    def change_profile(self):
        new_profile_name = simpledialog.askstring("Change Profile", "Enter new profile name:")
        if new_profile_name:
            self.current_profile = new_profile_name
            self.profile_label.config(text=f"Profile: {self.current_profile}")
            self.save_profile(new_profile_name)

    def save_profile(self, profile_name):
        config = configparser.ConfigParser()
        config['Profile'] = {'Name': profile_name}
        config['Games'] = {game: f"{self.games[game]['path']}|{self.games[game]['time_spent']}" for game in self.games}
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)

if __name__ == "__main__":
    if not ctypes.windll.shell32.IsUserAnAdmin():
        messagebox.showinfo("Administrator privileges required", "This program needs to be run with administrator privileges to continue.")
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        if result > 32:  
            sys.exit(0)  
        else:
            sys.exit(1)  
    else:
        root = tk.Tk()
        app = GameLauncher(root)
        root.mainloop()
