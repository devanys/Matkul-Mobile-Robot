import tkinter as tk
from tkinter import messagebox
import requests
import cv2
import threading

ESP32_IP = "http://"

def send_to_arduino(target_count1, target_count2):
    ser.write(f"{target_count1},{target_count2}\n".encode())

def stop_motors():
    ser.write("stop\n".encode())

def start_motor():
    try:
        target_count1 = int(entry_motor1.get())
        target_count2 = int(entry_motor2.get())

        send_to_arduino(target_count1, target_count2)
    except ValueError:
        messagebox.showerror("Error", "Masukkan nilai yang valid")

def start_camera():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow('Camera', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def read_encoder_values():
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode().strip()
            if ',' in data:
                count1, count2 = map(int, data.split(','))
                label_encoder1.config(text=f"Encoder Count Motor 1: {count1}")
                label_encoder2.config(text=f"Encoder Count Motor 2: {count2}")

root = tk.Tk()
root.title("Motor Control GUI")

frame = tk.Frame(root)
frame.pack(pady=20)

label_motor1 = tk.Label(frame, text="Motor 1 Target Count:")
label_motor1.grid(row=0, column=0, padx=10, pady=10)
entry_motor1 = tk.Entry(frame)
entry_motor1.grid(row=0, column=1, padx=10, pady=10)

label_motor2 = tk.Label(frame, text="Motor 2 Target Count:")
label_motor2.grid(row=1, column=0, padx=10, pady=10)
entry_motor2 = tk.Entry(frame)
entry_motor2.grid(row=1, column=1, padx=10, pady=10)

start_button = tk.Button(frame, text="Start Motor", command=start_motor)
start_button.grid(row=2, column=0, columnspan=2, pady=10)

stop_button = tk.Button(frame, text="Stop", command=stop_motors)
stop_button.grid(row=3, column=0, columnspan=2, pady=10)

camera_button = tk.Button(frame, text="Start Camera", command=lambda: threading.Thread(target=start_camera).start())
camera_button.grid(row=4, column=0, columnspan=2, pady=10)

label_encoder1 = tk.Label(frame, text="Encoder Count Motor 1: 0")
label_encoder1.grid(row=5, column=0, columnspan=2, pady=10)

label_encoder2 = tk.Label(frame, text="Encoder Count Motor 2: 0")
label_encoder2.grid(row=6, column=0, columnspan=2, pady=10)

threading.Thread(target=read_encoder_values, daemon=True).start()

root.mainloop()
