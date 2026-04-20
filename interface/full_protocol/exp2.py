#!/usr/bin/env python3
"""
Experiment logger + video recorder with MediaPipe Hand Detection
– AVI (XVID) recording with timestamp overlay + preview
– AprilTag 36h11 trial-ID
– LED feedback, audio cue
Press 'q' (console or preview) or Ctrl-C to quit
"""

import serial, time, csv, re, threading, keyboard, cv2
from datetime import datetime
from pathlib import Path
from pupil_apriltags import Detector
import pygame
import numpy as np
import mediapipe as mp ### MEDIAPIPE INTEGRATION ###

# ═════ USER SETTINGS ═════
SERIAL_PORT = "COM3"
BAUD        = 115200
CAM_INDEX   = 1          # 0 = laptop cam, 1 = IPEVO VZ-R
FRAME_W, FRAME_H = 1280, 720
VIDEO_FPS   = 20.0
AUDIO_PATH  = Path("certainty_fr.mp3")
START_AUDIO_PATH = Path("start.mp3")
LED_PULSE   = 0.15
AUDIO_DELAY = 0.0009
HAND_LANDMARKS_IN_ZONE = 10 # Number of hand landmarks needed to trigger exploration
# ═══════════════════════════

# ═════ CONSTANTS ═════
TAG_SIZE_MM = 22.0
TRIAL_WIDTH_MM = 297.088
TRIAL_HEIGHT_MM = 105.086
# ══════════════════════

# Initialize audio
pygame.mixer.init()
start_sound = pygame.mixer.Sound(str(START_AUDIO_PATH))
certainty_sound = pygame.mixer.Sound(str(AUDIO_PATH))

# ─── helpers ────────────────────
iso_now = lambda: datetime.now().isoformat(timespec="milliseconds")

def flash_led(ser, cmd, dur=LED_PULSE):
    ser.write(f"{cmd}\n".encode())
    time.sleep(dur)
    ser.write(f"{cmd.replace('on','off')}\n".encode())

def play_audio():
    certainty_sound.play()

def play_start_audio():
    start_sound.play()

# ─── maps / regex ─────────────
LED_CMD  = {f"butx{i}": f"led{i}on" for i in range(1,6)}
CERT_MAP = {f"butx{i}": str(i)      for i in range(1,6)}
CHOICE_MAP = {"butp0":"L", "butp1":"R"}
BTN_RE   = re.compile(r"^(butx[0-5]|butp[0-1])on_")

# ─── Detectors & thread-safe variables ──────────────

at_detector = Detector(families="tag36h11")
latest_frame, frame_lock = None, threading.Lock()
exploration_zone, zone_lock = None, threading.Lock()
hand_in_zone_event = threading.Event()
display_info, display_info_lock = {}, threading.Lock()

### MEDIAPIPE INTEGRATION ###
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=2,
                       min_detection_confidence=0.5,
                       min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

def detect_tag_and_set_zone(frame):
    global exploration_zone
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    tags = at_detector.detect(g)
    if tags:
        tag = tags[0]
        center = tag.center.astype(int)
        corners = tag.corners.astype(int)
        
        pixel_width = np.linalg.norm(corners[1] - corners[0])
        px_per_mm = pixel_width / TAG_SIZE_MM

        trial_w_px = int(TRIAL_WIDTH_MM * px_per_mm)
        trial_h_px = int(TRIAL_HEIGHT_MM * px_per_mm)

        x1 = int(center[0] - trial_w_px / 2); y1 = int(center[1] - trial_h_px / 2)
        x2 = int(center[0] + trial_w_px / 2); y2 = int(center[1] + trial_h_px / 2)

        with zone_lock:
            exploration_zone = (x1, y1, x2, y2)
        return str(tag.tag_id)
    with zone_lock:
        exploration_zone = None
    return "NA"

### MEDIAPIPE INTEGRATION: NEW HAND DETECTION ###

hand_zone_counter = 0
HAND_ZONE_THRESHOLD = 4  # Require 4 consecutive frames
trial_start_frame_counter = -1
DETECTION_START_FRAME_DELAY = 5  # Skip detection during these early frames

def detect_hand(frame):
    global hand_zone_counter, trial_start_frame_counter
    with zone_lock:
        zone = exploration_zone
    if zone is None:
        hand_zone_counter = 0
        return

    # Ignore detection for a few frames after start
    if 0 <= trial_start_frame_counter < DETECTION_START_FRAME_DELAY:
        trial_start_frame_counter += 1
        hand_zone_counter = 0
        return
    elif trial_start_frame_counter >= DETECTION_START_FRAME_DELAY:
        pass  # Ready to detect
    else:
        hand_zone_counter = 0
        return

    # Process with MediaPipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    hand_detected_in_zone = False
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            landmarks_inside = 0
            x1, y1, x2, y2 = zone

            for lm in hand_landmarks.landmark:
                lx, ly = int(lm.x * FRAME_W), int(lm.y * FRAME_H)
                if x1 <= lx <= x2 and y1 <= ly <= y2:
                    landmarks_inside += 1

            # Use updated threshold
            if landmarks_inside >= HAND_LANDMARKS_IN_ZONE:

                landmarks = [(int(lm.x * FRAME_W), int(lm.y * FRAME_H)) for lm in hand_landmarks.landmark]
                dists = []
                for i in range(len(landmarks)):
                    for j in range(i + 1, len(landmarks)):
                        dists.append(np.linalg.norm(np.array(landmarks[i]) - np.array(landmarks[j])))
                avg_dist = np.mean(dists)

                if avg_dist < 30:
                    continue


                hand_detected_in_zone = True
                break

    # Count consecutive frames
    if hand_detected_in_zone:
        hand_zone_counter += 1
    else:
        hand_zone_counter = 0

    # Confirm detection after threshold
    if hand_zone_counter >= HAND_ZONE_THRESHOLD:
        if not hand_in_zone_event.is_set():
            hand_in_zone_event.set()


# ─── camera thread (preview + recording) ────────

def cam_thread(evt: threading.Event, vid_path: Path):
    global latest_frame
    cam = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW) # CAP_DSHOW can improve stability on Windows
    cam.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_W)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
    if not cam.isOpened():
        print("[ERR] Could not open camera."); evt.set(); return

    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    vw = cv2.VideoWriter(str(vid_path), fourcc, VIDEO_FPS, (FRAME_W, FRAME_H))
    if not vw.isOpened():
        print("[ERR] Could not open VideoWriter."); cam.release(); evt.set(); return

    print(f"[INFO] Recording to {vid_path.name}")

    while not evt.is_set():
        ok, frame = cam.read()
        if not ok:
            print("[WARN] frame grab failed"); continue

        with frame_lock: latest_frame = frame.copy()
        
        # --- DETECTION & VISUAL OVERLAYS ---
        # Run hand detection. This will also draw the hand landmarks on the frame.
        detect_hand(frame)

        # 1. Add timestamp
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        cv2.putText(frame, ts, (10, FRAME_H-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

        # 2. Draw exploration zone
        with zone_lock:
            if exploration_zone:
                x1, y1, x2, y2 = exploration_zone
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2) # Yellow

        # 3. Draw dynamic info text
        with display_info_lock:
            if "exploration_start" in display_info and display_info["exploration_start"]:
                cv2.putText(frame, display_info["exploration_start"], (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        vw.write(frame)
        cv2.imshow("Preview (q = quit)", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            evt.set(); break

    cam.release(); vw.release(); cv2.destroyAllWindows()
    print("[INFO] Camera thread ended")


# ─── participant files ────────────
pid = input("Participant ID (e.g. 01): ").zfill(2)
CSV_PATH  = Path(f"p{pid}_trials.csv")
VIDEO_PATH= Path(f"p{pid}_video.avi")

new = not CSV_PATH.exists()
csv_f = open(CSV_PATH, "a", newline="")
writer = csv.writer(csv_f)
if new:
    writer.writerow(["trial_start","trial_id","exploration_start", "answer","answer_time",
                     "certainty_level","certainty_answer_time","double_press"])

# ─── serial and camera start ───────────────
ser = serial.Serial(SERIAL_PORT, BAUD, timeout=0.1)
print(f"[SER] Opened {SERIAL_PORT}")

cam_evt = threading.Event()
threading.Thread(target=cam_thread, args=(cam_evt, VIDEO_PATH),
                 daemon=True).start()

# ─── experiment state ───────────────
exp_started = in_trial = False
trial = {}

print('[INFO] Press q (preview window or console) to quit.')

try:
    while True:
        if cam_evt.is_set() or keyboard.is_pressed('q'):
            print("\n[EXIT] Quit."); break

        if hand_in_zone_event.is_set():
            if in_trial and not trial.get("exploration_start"):
                ts_iso = iso_now()
                trial["exploration_start"] = ts_iso
                print(f"[INFO] Hand entered exploration zone at {ts_iso}")

                with display_info_lock:
                    ts_str = datetime.fromisoformat(ts_iso).strftime('%H:%M:%S.%f')[:-3]
                    display_info['exploration_start'] = f"Exploration Start: {ts_str}"
            hand_in_zone_event.clear()

        if ser.in_waiting:
            line = ser.readline().decode(errors="ignore").strip()
            if not line: continue
            print("[ARD]", line)

            m_start = BTN_RE.match(line)
            is_new_trial_press = m_start and m_start.group(1) == "butx0"

            if line == "m_XP_starts" or is_new_trial_press:
                if in_trial: print("[WARN] prev trial discarded")
                
                # CRUCIAL: Reset all state for the new trial
                hand_in_zone_event.clear()
                with display_info_lock: display_info.clear()
                
                trial_start_frame_counter = 0  # Start counting detection frames
                
                with frame_lock:
                    frame_copy = None if latest_frame is None else latest_frame.copy()
                    
                tag_id = "NA"
                if frame_copy is not None:
                    tag_id = detect_tag_and_set_zone(frame_copy)
                        
                exp_started = in_trial = True
                trial = {"trial_start": iso_now(), "trial_id": tag_id, "exploration_start": "",
             "answer":"", "answer_time":"", "certainty_level":"", "certainty_answer_time":"",
             "double_press":"N"}
                        
                threading.Thread(target=flash_led, args=(ser, "led0on"), daemon=True).start()
                threading.Thread(target=play_start_audio, daemon=True).start()
                continue


            if not exp_started or not in_trial: continue

            m_btn = BTN_RE.match(line)
            if not m_btn: continue
            btn = m_btn.group(1)

            if btn in CHOICE_MAP:
                if not trial["answer"]:
                    trial["answer"] = CHOICE_MAP[btn]
                    trial["answer_time"] = iso_now()
                    flash_led(ser,"led1on" if btn=="butp0" else "led5on")
                    time.sleep(AUDIO_DELAY)
                    threading.Thread(target=play_audio, daemon=True).start()
                else: trial["double_press"] = "Y"
                continue

            if btn in CERT_MAP:
                if not trial["certainty_level"]:
                    trial["certainty_level"] = CERT_MAP[btn]
                    trial["certainty_answer_time"] = iso_now()
                    flash_led(ser, LED_CMD[btn])

                    writer.writerow(list(trial.values()))
                    csv_f.flush()
                    print("[SAVE] Trial logged")
                    
                    in_trial = False; trial = {}
                    with zone_lock: exploration_zone = None
                    with display_info_lock: display_info.clear()
                else: trial["double_press"] = "Y"
                continue

        time.sleep(0.02)

except KeyboardInterrupt:
    print("\n[EXIT] Ctrl+C")

finally:
    cam_evt.set()
    if csv_f: csv_f.close()
    if ser.is_open: ser.close()
    # Safely close MediaPipe hands object
    if 'hands' in globals():
        hands.close()
    print("[CLEAN] Closed all resources")