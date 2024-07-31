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

def calculate_vo2max(level, shuttles, age, sex):
    # VO2max formula from the beep test
    # Standard formula used for the beep test
    vo2max = (level * 6.0) + (shuttles / 10.0) - (age / 15.0)
    if sex == "Female":
        vo2max -= 2.0
    return vo2max

def rating(vo2max):
    if vo2max >= 60:
        return "Excellent"
    elif vo2max >= 50:
        return "Good"
    elif vo2max >= 40:
        return "Average"
    elif vo2max >= 30:
        return "Below Average"
    else:
        return "Poor"

class PlayerPanel:
    def __init__(self, parent, player_id, app):
        self.player_id = player_id
        self.app = app  # Store reference to the main app instance
        self.frame = tk.Frame(parent, borderwidth=2, relief=tk.SUNKEN)
        self.frame.grid(row=player_id-1, column=0, padx=10, pady=5, sticky='ew')

        self.label = tk.Label(self.frame, text=f"Player {self.player_id}: In Progress", font=("Arial", 12))
        self.label.pack(side=tk.LEFT, padx=10)

        self.complete_button = tk.Button(self.frame, text="Complete", font=("Arial", 12), command=self.mark_complete)
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

        # Initialize attributes
        self.level = 1
        self.shuttle = 1
        self.total_distance = 0
        self.speed = 0  # Initialize speed to avoid AttributeError
        self.running = False

        # Main Frame
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(padx=20, pady=20)

        # Title Label
        self.title_label = tk.Label(self.main_frame, text="20m Multi-Stage Fitness Test (Beep Test)", font=("Arial", 24))
        self.title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Info Frame
        self.info_frame = tk.Frame(self.main_frame)
        self.info_frame.grid(row=1, column=0, columnspan=3, pady=10)

        self.info_label = tk.Label(self.info_frame, text=f"Level: {self.level} Shuttle: {self.shuttle} Speed: {self.speed:.1f} km/h", font=("Arial", 18))
        self.info_label.pack()

        self.timer_label = tk.Label(self.info_frame, text="Time: 0.000 s", font=("Arial", 18))
        self.timer_label.pack()

        self.distance_label = tk.Label(self.info_frame, text="Total Distance: 0.0 m", font=("Arial", 18))
        self.distance_label.pack()

        self.countdown_label = tk.Label(self.info_frame, text="Get Ready: 10", font=("Arial", 18))
        self.countdown_label.pack()

        # Control Frame
        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.grid(row=2, column=0, columnspan=3, pady=10)

        self.start_button = tk.Button(self.control_frame, text="Start Test", font=("Arial", 16), command=self.start_test)
        self.start_button.grid(row=0, column=0, padx=10)

        self.stop_button = tk.Button(self.control_frame, text="Stop Test", font=("Arial", 16), command=self.stop_test, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=10)

        # Players Frame
        self.players_frame = tk.LabelFrame(self.main_frame, text="Players", padx=10, pady=10)
        self.players_frame.grid(row=3, column=0, padx=10, pady=10, sticky='n')

        # Initialize Player Panels with reference to the app instance
        self.players = [PlayerPanel(self.players_frame, i+1, self) for i in range(10)]

        # Result Display Frame (moved to the right side of Players)
        self.result_frame = tk.LabelFrame(self.main_frame, text="Results", padx=10, pady=10)
        self.result_frame.grid(row=3, column=1, padx=10, pady=10, sticky='n')

        self.result_display = tk.Text(self.result_frame, height=10, width=50, font=("Arial", 12))
        self.result_display.pack()

        # VO2max Calculator Frame
        self.vo2max_frame = tk.LabelFrame(self.main_frame, text="VO2max Calculator", padx=10, pady=10)
        self.vo2max_frame.grid(row=3, column=2, padx=10, pady=10, sticky='n')

        # Age Entry
        self.age_label = tk.Label(self.vo2max_frame, text="Enter your Age*: ")
        self.age_label.grid(row=0, column=0, sticky='w')
        self.age_entry = tk.Entry(self.vo2max_frame)
        self.age_entry.grid(row=0, column=1)

        # Sex Selection
        self.sex_label = tk.Label(self.vo2max_frame, text="Sex: ")
        self.sex_label.grid(row=1, column=0, sticky='w')

        self.sex_var = tk.StringVar(value="Male")
        self.sex_menu = tk.OptionMenu(self.vo2max_frame, self.sex_var, "Male", "Female")
        self.sex_menu.grid(row=1, column=1)

        # Level Entry
        self.level_label = tk.Label(self.vo2max_frame, text="Enter your level (e.g., 8): ")
        self.level_label.grid(row=2, column=0, sticky='w')
        self.level_entry = tk.Entry(self.vo2max_frame)
        self.level_entry.grid(row=2, column=1)

        # Number of Shuttles Entry
        self.shuttles_label = tk.Label(self.vo2max_frame, text="Enter number of shuttles (e.g., 5): ")
        self.shuttles_label.grid(row=3, column=0, sticky='w')
        self.shuttles_entry = tk.Entry(self.vo2max_frame)
        self.shuttles_entry.grid(row=3, column=1)

        # Calculate Button
        self.calculate_button = tk.Button(self.vo2max_frame, text="Calculate", command=self.calculate_vo2max)
        self.calculate_button.grid(row=4, column=0, columnspan=2, pady=10)

        # Result Display
        self.result_label = tk.Label(self.vo2max_frame, text="Your result (ml/kg/min): ")
        self.result_label.grid(row=5, column=0, sticky='w')
        self.result_value = tk.Label(self.vo2max_frame, text="")
        self.result_value.grid(row=5, column=1)

        self.rating_label = tk.Label(self.vo2max_frame, text="Rating: ")
        self.rating_label.grid(row=6, column=0, sticky='w')
        self.rating_value = tk.Label(self.vo2max_frame, text="")
        self.rating_value.grid(row=6, column=1)

    def start_test(self):
        self.level = 1
        self.shuttle = 1
        self.total_distance = 0
        self.speed = protocol[self.level][1]
        self.update_info()
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        threading.Thread(target=self.run_test).start()

    def run_test(self):
        countdown_time = 10
        while countdown_time > 0:
            self.countdown_label.config(text=f"Get Ready: {countdown_time}")
            self.root.update()
            time.sleep(1)
            countdown_time -= 1

        self.countdown_label.config(text="Start!")
        time.sleep(1)

        time_per_shuttle = calculate_time_per_shuttle(self.speed)
        shuttle_count = protocol[self.level][0]
        self.total_distance = shuttle_count * 20

        while self.running and self.level <= 21:
            self.info_label.config(text=f"Level: {self.level} Shuttle: {self.shuttle} Speed: {self.speed:.1f} km/h")
            self.root.update()

            for _ in range(shuttle_count):
                if not self.running:
                    return
                self.info_label.config(text=f"Level: {self.level} Shuttle: {self.shuttle} Speed: {self.speed:.1f} km/h")
                self.root.update()

                start_time = time.time()
                pygame.mixer.music.load("beep.wav")  # Ensure the beep.wav file is in the same directory
                pygame.mixer.music.play()
                time.sleep(time_per_shuttle)
                pygame.mixer.music.stop()
                elapsed_time = time.time() - start_time

                self.timer_label.config(text=f"Time: {elapsed_time:.3f} s")
                self.total_distance = self.shuttle * 20
                self.update_info()

            if self.shuttle == shuttle_count:
                self.level += 1
                if self.level in protocol:
                    shuttle_count = protocol[self.level][0]
                    self.speed = protocol[self.level][1]
                    time_per_shuttle = calculate_time_per_shuttle(self.speed)
                self.shuttle = 1
            else:
                self.shuttle += 1

        self.stop_test()

    def stop_test(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.info_label.config(text=f"Test Stopped: Level {self.level} Shuttle {self.shuttle} Distance {self.total_distance:.1f} m")
        self.timer_label.config(text="Time: 0.000 s")  # Show exact time when stopped

    def update_info(self):
        self.info_label.config(text=f"Level: {self.level} Shuttle: {self.shuttle} Speed: {self.speed:.1f} km/h")
        self.distance_label.config(text=f"Total Distance: {self.total_distance:.1f} m")
        self.root.update()

    def show_result(self, player_id, result):
        self.result_display.insert(tk.END, f"Player {player_id} - {result}\n")
        self.result_display.yview(tk.END)

    def calculate_vo2max(self):
        try:
            age = int(self.age_entry.get())
            sex = self.sex_var.get()  # Use the selected option
            level = int(self.level_entry.get())
            shuttles = int(self.shuttles_entry.get())

            vo2max = calculate_vo2max(level, shuttles, age, sex)
            self.result_value.config(text=f"{vo2max:.1f}")
            self.rating_value.config(text=rating(vo2max))
        except ValueError:
            self.result_value.config(text="Invalid input")
            self.rating_value.config(text="")

if __name__ == "__main__":
    root = tk.Tk()
    app = MSFTApp(root)
    root.mainloop()
