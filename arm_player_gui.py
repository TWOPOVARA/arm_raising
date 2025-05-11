import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import signal
import time
from contextlib import suppress
from pathlib import Path
import cv2
import mediapipe as mp
import platform

x = 55
audio_proc = None

def start_audio(file_path: Path):
    global audio_proc
    if audio_proc and audio_proc.poll() is None:
        return

    if platform.system() == "Darwin":
        cmd = ["afplay", str(file_path)]
    elif platform.system() == "Windows":
        cmd = ["powershell", "-c", f"(New-Object Media.SoundPlayer '{file_path}').PlaySync();"]
    else:
        cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(file_path)]

    audio_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def stop_audio():
    global audio_proc
    if audio_proc and audio_proc.poll() is None:
        with suppress(ProcessLookupError):
            audio_proc.send_signal(signal.SIGTERM)
        audio_proc = None

def arm_above_shoulder(landmarks, wrist_id, shoulder_id, img_h) -> bool:
    wrist = landmarks[wrist_id]
    shoulder = landmarks[shoulder_id]
    return (
        wrist.visibility > 0.75
        and shoulder.visibility > 0.75
        and (wrist.y * img_h) < (shoulder.y * img_h)
    )

def run_pose_loop(audio_file: Path):
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(model_complexity=1)

    def try_open_camera(max_index=4):
        for i in range(max_index):
            cam = cv2.VideoCapture(i)
            if cam.isOpened():
                print(f"✅ Using camera index: {i}")
                return cam
        return None

    cam = try_open_camera()

    if not cam or not cam.isOpened():
        messagebox.showerror("Error", "No working webcam found.")
        return

    if not cam.isOpened():
        messagebox.showerror("Error", "Cannot open webcam.")
        return

    playing = False
    last_action = 0.0
    COOLDOWN = 2.0

    try:
        while True:
            ok, frame = cam.read()
            if not ok or frame is None or frame.size == 0:
                print("⚠️ Invalid frame — skipping")
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)
            img_h = frame.shape[0]

            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                left_up = arm_above_shoulder(lm, 15, 11, img_h)
                right_up = arm_above_shoulder(lm, 16, 12, img_h)
                now = time.time()

                if (left_up or right_up) and not playing and now - last_action > COOLDOWN:
                    start_audio(audio_file)
                    playing = True
                    last_action = now
                    print("▶️ Playing")

                elif (not left_up and not right_up) and playing and now - last_action > COOLDOWN:
                    stop_audio()
                    playing = False
                    last_action = now
                    print("⏸ Stopped")

            mp.solutions.drawing_utils.draw_landmarks(
                frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
            )

            window_name = "Raise your arm to play — press q to quit"
            try:
                cv2.imshow(window_name, frame)
            except cv2.error as e:
                print(f"❌ OpenCV display error: {e}")
                break

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        if cam:
            cam.release()
        cv2.destroyAllWindows()
        pose.close()
        stop_audio()

def select_file():
    file_path = filedialog.askopenfilename(
        title="Choose MP3 File",
        filetypes=[("Audio files", "*.mp3")]
    )
    if not file_path:
        return

    run_pose_loop(Path(file_path))  # no threading


# GUI Setup
window = tk.Tk()
window.title("Arm Audio Controller")
window.geometry("300x150")
label = tk.Label(window, text="Select an MP3 file to control with your arm")
label.pack(pady=10)
btn = tk.Button(window, text="Choose MP3", command=select_file)
btn.pack(pady=20)

window.mainloop()