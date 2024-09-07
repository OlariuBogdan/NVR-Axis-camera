import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import Button, Label
from PIL import Image, ImageTk

def check_camera_connection(ip):
    response = os.system(f"ping -c 1 {ip}" if os.name != 'nt' else f"ping -n 1 {ip}")
    return response == 0

def resize_frame(frame, size):
    return cv2.resize(frame, size)

def add_number_to_frame(frame, number):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    font_color = (255, 0, 0)  # Red color for the text
    thickness = 2
    text_size = cv2.getTextSize(str(number), font, font_scale, thickness)[0]
    text_x = frame.shape[1] - text_size[0] - 10  # 10 pixels from the right edge
    text_y = text_size[1] + 10  # 10 pixels from the top edge

    cv2.putText(frame, str(number), (text_x, text_y), font, font_scale, font_color, thickness)
    return frame

def update_frame():
    frames = []
    for i, cap in enumerate(captures):
        ret, frame = cap.read()
        if ret:
            frame_with_number = add_number_to_frame(frame, i + 1)
            frame_resized = resize_frame(frame_with_number, (400, 300))
            frames.append(frame_resized)
            # Write the frame to the corresponding video file
            video_writers[i].write(frame)
        else:
            print(f"Nu se poate citi fluxul video. Verifică conexiunea și URL-ul.")
            frames.append(np.zeros((300, 400, 3), dtype=np.uint8))

    if len(frames) == 4:
        top_row = np.hstack(frames[:2])
        bottom_row = np.hstack(frames[2:])
        combined_frame = np.vstack([top_row, bottom_row])
        
        combined_frame_rgb = cv2.cvtColor(combined_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(combined_frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)

        label.imgtk = imgtk
        label.config(image=imgtk)
    else:
        print("Nu toate cadrele au fost primite.")

    root.after(30, update_frame)

def toggle_fullscreen(camera_index=None):
    global fullscreen, fullscreen_window, fullscreen_label
    if camera_index is None:
        fullscreen = not fullscreen
        root.attributes("-fullscreen", fullscreen)
        if not fullscreen:
            root.attributes("-fullscreen", False)
    else:
        if fullscreen_window is not None:
            fullscreen_window.destroy()

        fullscreen_window = tk.Toplevel(root)
        fullscreen_window.attributes("-fullscreen", True)
        fullscreen_window.bind("<Escape>", end_fullscreen)

        fullscreen_label = Label(fullscreen_window)
        fullscreen_label.pack(fill=tk.BOTH, expand=True)

        def update_fullscreen_frame():
            ret, frame = captures[camera_index].read()
            if ret:
                frame_resized = resize_frame(frame, (fullscreen_window.winfo_width(), fullscreen_window.winfo_height()))
                frame_with_number = add_number_to_frame(frame_resized, camera_index + 1)
                frame_rgb = cv2.cvtColor(frame_with_number, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)

                fullscreen_label.imgtk = imgtk
                fullscreen_label.config(image=imgtk)
            
            fullscreen_window.after(30, update_fullscreen_frame)

        update_fullscreen_frame()

def end_fullscreen(event=None):
    global fullscreen, fullscreen_window
    fullscreen = False
    root.attributes("-fullscreen", False)
    if fullscreen_window is not None:
        fullscreen_window.destroy()
    fullscreen_window = None

def open_video_folder():
    os.startfile(output_dir)

camera_ips = ["192.168.99.110", "192.168.99.111", "192.168.99.112", "192.168.99.113"]
user = "root"
password = "root"
rtsp_urls = [f"rtsp://{user}:{password}@{ip}/axis-media/media.amp" for ip in camera_ips]

captures = []
video_writers = []

# Create directory for video files
output_dir = "videos"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for i, rtsp_url in enumerate(rtsp_urls):
    if check_camera_connection(camera_ips[i]):
        print(f"Camera {camera_ips[i]} este disponibilă, încercăm conectarea prin RTSP...")
        cap = cv2.VideoCapture(rtsp_url)
        
        if cap.isOpened():
            captures.append(cap)
            # Define codec and create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out_filename = os.path.join(output_dir, f"camera_{i + 1}.avi")
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            video_writer = cv2.VideoWriter(out_filename, fourcc, 20.0, (width, height))
            video_writers.append(video_writer)
            print(f"Conectat cu succes la {camera_ips[i]}")
        else:
            print(f"Nu s-a putut conecta la {camera_ips[i]}. Verifică URL-ul și datele de autentificare.")
    else:
        print(f"Camera {camera_ips[i]} nu este disponibilă în rețea.")

if len(captures) == 0:
    print("Nicio cameră nu a fost conectată.")
else:
    root = tk.Tk()
    root.title("Vizualizare Camere Video")
    root.geometry("1200x720")

    label = Label(root)
    label.pack(fill=tk.BOTH, expand=True)

    buttons_frame = tk.Frame(root)
    buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

    buttons_frame.grid_rowconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure([0, 1, 2, 3], weight=1)

    for i, ip in enumerate(camera_ips):
        button = Button(buttons_frame, text=f"Fullscreen Camera {i+1}", command=lambda i=i: toggle_fullscreen(i))
        button.grid(row=0, column=i, padx=10, pady=5, sticky='ew')

    open_folder_button = Button(buttons_frame, text="Open Video Folder", command=open_video_folder)
    open_folder_button.grid(row=0, column=len(camera_ips), padx=10, pady=5, sticky='ew')

    fullscreen_window = None
    fullscreen = False
    update_frame()

    root.mainloop()

    for cap in captures:
        cap.release()
    for video_writer in video_writers:
        video_writer.release()
    cv2.destroyAllWindows()
