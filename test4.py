import tkinter as tk
import pygame
import time
import threading

# Initialize Pygame for audio playback
pygame.mixer.init()

# Updated Beep Test protocol
protocol = {
    1: (7, 8.0),
    2: (8, 9.0),
    3: (8, 9.5),
    4: (9, 10.0),
    5: (9, 10.5),
    6: (10, 11.0),
    7: (10, 11.5),
    8: (11, 12.0),
    9: (11, 12.5),
    10: (11, 13.0),
    11: (12, 13.5),
    12: (12, 14.0),
    13: (13, 14.5),
    14: (13, 15.0),
    15: (13, 15.5),
    16: (14, 16.0),
    17: (14, 16.5),
    18: (15, 17.0),
    19: (15, 17.5),
    20: (16, 18.0),
    21: (16, 18.5),
}

def calculate_time_per_shuttle(speed):
    distance = 20  # 20 meters
    time_per_shuttle = (distance / (speed * 1000 / 3600))  # speed in m/s
    return time_per_shuttle

class PlayerPanel:
    def __init__(self, parent, player_id, app):
        self.player_id = player_id
        self.app = app  # Store reference to the main app instance
        self.frame = tk.Frame(parent, borderwidth=2, relief=tk.RAISED, bg="#2E2E2E")
        self.frame.grid(row=player_id-1, column=0, padx=10, pady=5, sticky='ew')

        self.label = tk.Label(self.frame, text=f"Player {self.player_id}: In Progress", font=("Arial", 12), bg="#2E2E2E", fg="#FFFFFF")
        self.label.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

        self.complete_button = tk.Button(self.frame, text="Complete", font=("Arial", 12), command=self.mark_complete, bg="#4CAF50", fg="#FFFFFF", relief=tk.FLAT)
        self.complete_button.pack(side=tk.RIGHT, padx=10)

        self.result = None  # Store result here

    def mark_complete(self):
        if self.app.level and self.app.shuttle and self.app.total_distance is not None:
            self.result = f"Level {self.app.level} Shuttle {self.app.shuttle - 1} Distance {self.app.total_distance:.1f} m"
            self.label.config(text=f"Player {self.player_id}: Completed")
            self.complete_button.config(state=tk.DISABLED)
            self.app.show_result(self.player_id, self.result)

class MSFTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("20m Multi-Stage Fitness Test (Beep Test)")
        self.root.configure(bg="#333333")

        # Initialize attributes
        self.level = 1
        self.shuttle = 1
        self.total_distance = 0
        self.speed = 0  # Initialize speed to avoid AttributeError
        self.running = False

        

        # Make the window resizable
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Main Frame
        self.main_frame = tk.Frame(root, bg="#333333")
        self.main_frame.grid(sticky="nsew", padx=20, pady=20)

        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # Title Label
        self.title_label = tk.Label(self.main_frame, text="20m Multi-Stage Fitness Test (Beep Test)", font=("Arial", 24), bg="#333333", fg="#FFFFFF")
        self.title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Info Frame
        self.info_frame = tk.Frame(self.main_frame, bg="#444444")
        self.info_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")

        self.info_label = tk.Label(self.info_frame, text=f"Level: {self.level} Shuttle: {self.shuttle} Speed: {self.speed:.1f} km/h", font=("Arial", 18), bg="#444444", fg="#FFFFFF")
        self.info_label.pack()

        self.timer_label = tk.Label(self.info_frame, text="Time: 0.000 s", font=("Arial", 18), bg="#444444", fg="#FFFFFF")
        self.timer_label.pack()

        self.distance_label = tk.Label(self.info_frame, text="Total Distance: 0.0 m", font=("Arial", 18), bg="#444444", fg="#FFFFFF")
        self.distance_label.pack()

        # Control Frame
        self.control_frame = tk.Frame(self.main_frame, bg="#555555")
        self.control_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")

        self.start_button = tk.Button(self.control_frame, text="Start Test", font=("Arial", 16), command=self.start_test, bg="#2196F3", fg="#FFFFFF", relief=tk.FLAT)
        self.start_button.grid(row=0, column=0, padx=10, sticky="ew")

        self.stop_button = tk.Button(self.control_frame, text="Stop Test", font=("Arial", 16), command=self.stop_test, state=tk.DISABLED, bg="#F44336", fg="#FFFFFF", relief=tk.FLAT)
        self.stop_button.grid(row=0, column=1, padx=10, sticky="ew")

        self.control_frame.grid_columnconfigure(0, weight=1)
        self.control_frame.grid_columnconfigure(1, weight=1)

        # Players Frame
        self.players_frame = tk.LabelFrame(self.main_frame, text="Players", padx=10, pady=10, bg="#333333", fg="#FFFFFF")
        self.players_frame.grid(row=3, column=0, padx=10, pady=10, sticky='nsew')

        self.players_frame.grid_rowconfigure(0, weight=1)
        self.players_frame.grid_columnconfigure(0, weight=1)

        # Initialize Player Panels with reference to the app instance
        self.players = [PlayerPanel(self.players_frame, i+1, self) for i in range(10)]

        # Result Display Frame (moved to the right side of Players)
        self.result_frame = tk.LabelFrame(self.main_frame, text="Results", padx=10, pady=10, bg="#333333", fg="#FFFFFF")
        self.result_frame.grid(row=3, column=1, padx=10, pady=10, sticky='nsew')

        self.result_display = tk.Text(self.result_frame, height=10, width=50, font=("Arial", 12), bg="#2E2E2E", fg="#FFFFFF")
        self.result_display.pack(expand=True, fill=tk.BOTH)

        self.update_protocol()

    def update_protocol(self):
        if self.level in protocol:
            self.num_shuttles, self.speed = protocol[self.level]
            self.info_label.config(text=f"Level: {self.level} Shuttle: {self.shuttle} Speed: {self.speed:.1f} km/h")

    def start_test(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.show_countdown(10)

    def show_countdown(self, seconds):
        countdown_window = tk.Toplevel(self.root)
        countdown_window.title("Get Ready!")
        countdown_window.geometry("300x200")
        countdown_window.attributes("-topmost", True)

        countdown_window.configure(bg="#333333")

        label = tk.Label(countdown_window, text="Get Ready!", font=("Arial", 24), bg="#333333", fg="#FFFFFF")
        label.pack(expand=True)

        time_label = tk.Label(countdown_window, text=f"{seconds}", font=("Arial", 48), bg="#333333", fg="#FFFFFF")
        time_label.pack(expand=True)

        def update_countdown():
            nonlocal seconds
            while seconds > 0:
                time_label.config(text=f"{seconds}")
                countdown_window.update()
                time.sleep(1)
                seconds -= 1
            time_label.config(text="Go!")
            countdown_window.update()
            time.sleep(1)
            countdown_window.destroy()  # Close the countdown window
            self.running = True
            threading.Thread(target=self.run_test).start()

        # Start countdown update in a separate thread
        threading.Thread(target=update_countdown).start()

    def stop_test(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def run_test(self):
        while self.running and self.level <= len(protocol):
            time_per_shuttle = calculate_time_per_shuttle(self.speed)
            self.play_beep()
            self.update_timer(time_per_shuttle)

            self.shuttle += 1
            self.total_distance += 20  # Update total distance after each shuttle
            if self.shuttle > self.num_shuttles:
                self.shuttle = 1
                self.level += 1
                if self.level <= len(protocol):
                    self.update_protocol()  # Update speed and shuttles for the new level
                else:
                    self.running = False
            self.update_info()

    def play_beep(self):
        pygame.mixer.music.load("beep.mp3")
        pygame.mixer.music.play()

    def update_timer(self, duration):
        start_time = time.time()
        while self.running and (time.time() - start_time) < duration:
            remaining_time = duration - (time.time() - start_time)
            self.timer_label.config(text=f"Time: {remaining_time:.3f} s")
            self.root.update()
        self.timer_label.config(text="Time: 0.000 s")

    def update_info(self):
        self.info_label.config(text=f"Level: {self.level} Shuttle: {self.shuttle} Speed: {self.speed:.1f} km/h")
        self.distance_label.config(text=f"Total Distance: {self.total_distance:.1f} m")
        self.root.update()

    def show_result(self, player_id, result):
        self.result_display.insert(tk.END, f"Player {player_id} - {result}\n")
        self.result_display.yview(tk.END)

    

if __name__ == "__main__":
    root = tk.Tk()
    app = MSFTApp(root)
    root.mainloop()
