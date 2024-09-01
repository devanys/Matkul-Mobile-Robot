import tkinter as tk
import math
import requests
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class RobotSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Simulator with Grid and Wheels")

        # Create a Canvas widget
        self.canvas = tk.Canvas(root, width=600, height=600, bg="white")
        self.canvas.pack(side=tk.LEFT)

        # Create a frame for PWM charts
        self.pwm_frame = tk.Frame(root)
        self.pwm_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create matplotlib figures for PWM charts
        self.fig_pwm_left = Figure(figsize=(3, 2), dpi=100)
        self.ax_pwm_left = self.fig_pwm_left.add_subplot(111)
        self.ax_pwm_left.set_title("PWM Left")
        self.ax_pwm_left.set_ylabel("PWM Value")
        self.ax_pwm_left.set_xlabel("Time")

        self.fig_pwm_right = Figure(figsize=(3, 2), dpi=100)
        self.ax_pwm_right = self.fig_pwm_right.add_subplot(111)
        self.ax_pwm_right.set_title("PWM Right")
        self.ax_pwm_right.set_ylabel("PWM Value")
        self.ax_pwm_right.set_xlabel("Time")

        # Embed matplotlib figures in Tkinter
        self.canvas_pwm_left = FigureCanvasTkAgg(self.fig_pwm_left, master=self.pwm_frame)
        self.canvas_pwm_left.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas_pwm_right = FigureCanvasTkAgg(self.fig_pwm_right, master=self.pwm_frame)
        self.canvas_pwm_right.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Draw grid on the canvas
        self.draw_grid()

        # Robot initial position and target
        self.robot_pos = [300, 300]  # Center of the grid
        self.robot_radius = 10
        self.target_pos = [300, 300]  # Default target same as initial position

        # Draw initial robot position
        self.robot = self.canvas.create_oval(
            self.robot_pos[0] - self.robot_radius,
            self.robot_pos[1] - self.robot_radius,
            self.robot_pos[0] + self.robot_radius,
            self.robot_pos[1] + self.robot_radius,
            fill="blue"
        )

        # Draw target position
        self.target = self.canvas.create_oval(
            self.target_pos[0] - self.robot_radius,
            self.target_pos[1] - self.robot_radius,
            self.target_pos[0] + self.robot_radius,
            self.target_pos[1] + self.robot_radius,
            fill="red"
        )

        # Draw wheels
        self.left_wheel = self.canvas.create_rectangle(
            self.robot_pos[0] - self.robot_radius - 15,
            self.robot_pos[1] - 5,
            self.robot_pos[0] - self.robot_radius - 5,
            self.robot_pos[1] + 5,
            fill="gray"
        )
        self.right_wheel = self.canvas.create_rectangle(
            self.robot_pos[0] + self.robot_radius + 5,
            self.robot_pos[1] - 5,
            self.robot_pos[0] + self.robot_radius + 15,
            self.robot_pos[1] + 5,
            fill="gray"
        )

        # Set up the IP address of the Arduino server
        self.server_ip = "192.168.1.3"  # Replace with your Arduino IP address

        # X and Y entry fields for target position
        self.x_label = tk.Label(root, text="Target X:")
        self.x_label.pack()
        self.x_entry = tk.Entry(root)
        self.x_entry.pack()

        self.y_label = tk.Label(root, text="Target Y:")
        self.y_label.pack()
        self.y_entry = tk.Entry(root)
        self.y_entry.pack()

        # Button to set target and start movement
        self.start_button = tk.Button(root, text="Set Target and Start", command=self.start_movement)
        self.start_button.pack()

        # Movement parameters
        self.moving = False
        self.move_speed = 2  # Adjusted for accuracy

        # PWM history for plotting
        self.pwm_left_history = []
        self.pwm_right_history = []

        # Start updating PWM values
        self.update_pwm_values()

    def draw_grid(self):
        # Draw a grid on the canvas
        for i in range(0, 600, 20):
            self.canvas.create_line([(i, 0), (i, 600)], fill='gray', tags='grid_line')
            self.canvas.create_line([(0, i), (600, i)], fill='gray', tags='grid_line')

    def update_target(self, x, y):
        self.target_pos = [300 + x, 300 - y]
        self.canvas.coords(self.target,
            self.target_pos[0] - self.robot_radius,
            self.target_pos[1] - self.robot_radius,
            self.target_pos[0] + self.robot_radius,
            self.target_pos[1] + self.robot_radius
        )
        requests.get(f"http://{self.server_ip}/setTarget?x={x}&y={y}")

    def start_movement(self):
        try:
            # Get the target x and y from the entry fields
            x = int(self.x_entry.get())
            y = int(self.y_entry.get())
            self.update_target(x, y)
            self.moving = True
            self.move_robot()
        except ValueError:
            print("Please enter valid integers for X and Y coordinates.")

    def move_robot(self):
        if not self.moving:
            return

        # Calculate the difference between the current position and target
        dx = self.target_pos[0] - self.robot_pos[0]
        dy = self.target_pos[1] - self.robot_pos[1]
        distance = math.sqrt(dx**2 + dy**2)

        # If the robot hasn't reached the target, continue moving
        if distance > 1:
            angle = math.atan2(dy, dx)
            move_dx = math.cos(angle) * self.move_speed
            move_dy = math.sin(angle) * self.move_speed

            self.robot_pos[0] += move_dx
            self.robot_pos[1] += move_dy

            # Update robot and wheels positions
            self.canvas.coords(self.robot, 
                self.robot_pos[0] - self.robot_radius,
                self.robot_pos[1] - self.robot_radius,
                self.robot_pos[0] + self.robot_radius,
                self.robot_pos[1] + self.robot_radius
            )

            self.update_wheels()

            # Update PWM values
            self.update_pwm_values()

            # Schedule the next movement update
            self.root.after(50, self.move_robot)
        else:
            # Stop the robot when it reaches the target
            self.moving = False
            print("Target reached. Robot stopped.")
            # Send a stop command to the Arduino
            requests.get(f"http://{self.server_ip}/stop")

    def update_wheels(self):
        # Update the wheel positions based on the robot's movement
        wheel_offset = 20  # Distance from robot center to wheels
        wheel_width = 10
        wheel_length = 30
        
        self.canvas.coords(self.left_wheel,
            self.robot_pos[0] - self.robot_radius - wheel_offset - wheel_length,
            self.robot_pos[1] - wheel_width / 2,
            self.robot_pos[0] - self.robot_radius - wheel_offset,
            self.robot_pos[1] + wheel_width / 2
        )
        self.canvas.coords(self.right_wheel,
            self.robot_pos[0] + self.robot_radius + wheel_offset,
            self.robot_pos[1] - wheel_width / 2,
            self.robot_pos[0] + self.robot_radius + wheel_offset + wheel_length,
            self.robot_pos[1] + wheel_width / 2
        )

    def update_pwm_values(self):
        try:
            # Request PWM values from Arduino
            response = requests.get(f"http://{self.server_ip}/getPWM")
            data = response.text.split('<br>')
            
            # Extract PWM values from the response
            pwm_left = int(data[0].split(': ')[1])
            pwm_right = int(data[1].split(': ')[1])
            
            # Add new PWM values to history
            self.pwm_left_history.append(pwm_left)
            self.pwm_right_history.append(pwm_right)
            
            # Keep history length manageable
            if len(self.pwm_left_history) > 100:
                self.pwm_left_history.pop(0)
                self.pwm_right_history.pop(0)

            # Update PWM charts
            self.ax_pwm_left.clear()
            self.ax_pwm_left.set_title("PWM Left")
            self.ax_pwm_left.set_ylabel("PWM Value")
            self.ax_pwm_left.set_xlabel("Time")
            self.ax_pwm_left.plot(self.pwm_left_history, color='blue')
            self.ax_pwm_left.set_ylim(min(self.pwm_left_history + [0]), max(self.pwm_left_history + [255]))

            self.ax_pwm_right.clear()
            self.ax_pwm_right.set_title("PWM Right")
            self.ax_pwm_right.set_ylabel("PWM Value")
            self.ax_pwm_right.set_xlabel("Time")
            self.ax_pwm_right.plot(self.pwm_right_history, color='red')
            self.ax_pwm_right.set_ylim(min(self.pwm_right_history + [0]), max(self.pwm_right_history + [255]))

            # Redraw the charts
            self.canvas_pwm_left.draw()
            self.canvas_pwm_right.draw()
        except Exception as e:
            print(f"Error retrieving PWM values: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RobotSimulator(root)
    root.mainloop()
