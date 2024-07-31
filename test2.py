import tkinter as tk
from tkinter import messagebox
import pygame
import time
import threading
import csv
import matplotlib.pyplot as plt
import numpy as np

# Initialize Pygame for audio playback
pygame.mixer.init()

# Protocol definitions
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
        self.app = app
        self.frame = tk.Frame(parent, borderwidth=2, relief=tk.SUNKEN)
        self.frame.grid(row=player_id-1, column=0, padx=10, pady=5, sticky='ew')

        self.label = tk.Label(self.frame, text=f"Player {self.player_id}: In Progress", font=("Arial", 12))
        self.label.pack(side=tk.LEFT, padx=10)

        self.complete_button = tk.Button(self.frame, text="Complete", font=("Arial", 12), command=self.mark_complete)
        self.complete_button.pack(side=tk.RIGHT, padx=10)

        self.result = None

    def mark_complete(self):
        if self.app.level and self.app.shuttle and self.app.total_distance is not None:
            self.result = f"Level {self.app.level} Shuttle {self.app.shuttle - 1} Distance {self.app.total_distance:.1f} m"
            self.label.config(text=f"Player {self.player_id}: Completed")
            self.complete_button.config(state=tk.DISABLED)
            self.app.show_result(self.player_id, self.result)
            self.app.update_player_record(self.player_id, self.result)

class MSFTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("20m Multi-Stage Fitness Test (Beep Test)")

        # Initialize attributes
        self.level = 1
        self.shuttle = 1
        self.total_distance = 0
        self.speed = 0
        self.running = False
        self.records = {}

        # Main Frame
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(padx=20, pady=20)

        # Title Label
        self.title_label = tk.Label(self.main_frame, text="20m Multi-Stage Fitness Test (Beep Test)", font=("Arial", 24))
        self.title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Info Frame
        self.info_frame = tk.Frame(self.main_frame)
        self.info_frame.grid(row=1, column=0, columnspan=2, pady=10)

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
        self.control_frame.grid(row=2, column=0, columnspan=2, pady=10)

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

        # Statistics Frame
        self.stats_frame = tk.LabelFrame(self.main_frame, text="Statistics", padx=10, pady=10)
        self.stats_frame.grid(row=4, column=0, columnspan=2, pady=10)

        self.stats_label = tk.Label(self.stats_frame, text="Average Speed: 0.0 km/h\nTotal Distance Covered: 0.0 m", font=("Arial", 12))
        self.stats_label.pack()

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
        self.countdown_label.config(text=f"Get Ready: {seconds}")
        self.root.update()
        while seconds > 0:
            time.sleep(1)
            seconds -= 1
            self.countdown_label.config(text=f"Get Ready: {seconds}")
            self.root.update()
        self.countdown_label.config(text="Go!")
        self.root.update()
        time.sleep(1)  # Show "Go!" for 1 second before starting the test
        self.countdown_label.config(text="")
        self.root.update()
        self.running = True
        threading.Thread(target=self.run_test).start()

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

    def update_timer(self, time_per_shuttle):
        start_time = time.time()
        while time.time() - start_time < time_per_shuttle and self.running:
            elapsed_time = time.time() - start_time
            self.timer_label.config(text=f"Time: {elapsed_time:.3f} s")
            self.root.update()
            time.sleep(0.01)

    def update_info(self):
        self.info_label.config(text=f"Level: {self.level} Shuttle: {self.shuttle} Speed: {self.speed:.1f} km/h")
        self.distance_label.config(text=f"Total Distance: {self.total_distance:.1f} m")
        self.update_statistics()
        self.root.update()

    def update_statistics(self):
        if self.records:
            average_speed = np.mean([float(record.split()[4]) for record in self.records.values()])
            total_distance = np.sum([float(record.split()[6]) for record in self.records.values()])
            self.stats_label.config(text=f"Average Speed: {average_speed:.1f} km/h\nTotal Distance Covered: {total_distance:.1f} m")

    def update_player_record(self, player_id, result):
        self.records[player_id] = result

    def show_result(self, player_id, result):
        self.result_display.insert(tk.END, f"Player {player_id} - {result}\n")
        self.result_display.yview(tk.END)

    def export_results(self):
        with open("results.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Player ID", "Result"])
            for player_id, result in self.records.items():
                writer.writerow([player_id, result])

    def plot_performance(self):
        players = list(self.records.keys())
        distances = [float(record.split()[6]) for record in self.records.values()]
        plt.figure(figsize=(10, 6))
        plt.bar(players, distances, color='blue')
        plt.xlabel('Player ID')
        plt.ylabel('Total Distance (m)')
        plt.title('Performance of Players')
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = MSFTApp(root)
    root.mainloop()
