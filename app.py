import cv2
import mediapipe as mp
import serial
import time
import os
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 1. Initialize Serial Communication (COM5)
try:
    arduino = serial.Serial('COM5', 9600, timeout=1)
    time.sleep(2)  # Give Arduino time to reset
    print("Connected to Arduino!")
except Exception as e:
    print("Could not connect to Arduino. Running in simulation mode...")
    arduino = None

# 2. Set up modern MediaPipe Hand Landmarker
model_path = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')

if not os.path.exists(model_path):
    print(f"ERROR: 'hand_landmarker.task' not found at {model_path}")
    print("Please download it and place it in the same folder as this script.")
    exit()

base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7
)
detector = vision.HandLandmarker.create_from_options(options)

# 3. Start Video Capture
cap = cv2.VideoCapture(0)

# Track the last sent command to avoid spamming the Arduino serial port
last_state = None

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Ignoring empty camera frame.")
        continue

    # Flip horizontally for natural mirror feel
    frame = cv2.flip(frame, 1)
    
    # Modern MediaPipe needs images converted to its own format
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    # Process the frame
    detection_result = detector.detect(mp_image)

    # 4. Strict Gesture Parsing
    if detection_result.hand_landmarks:
        hand_landmarks = detection_result.hand_landmarks[0]
        
        fingers = []

        # --- THUMB LOGIC ---
        # Checks if thumb tip (4) is extended away from the base of the index finger (5)
        # Using absolute distance handles both front-of-palm and back-of-hand positions
        thumb_tip_x = hand_landmarks[4].x
        index_base_x = hand_landmarks[5].x
        thumb_base_x = hand_landmarks[2].x
        
        if abs(thumb_tip_x - index_base_x) > abs(thumb_base_x - index_base_x):
            fingers.append(1)
        else:
            fingers.append(0)

        # --- 4 FINGERS LOGIC (Index, Middle, Ring, Pinky) ---
        finger_tips = [8, 12, 16, 20]
        finger_knuckles = [6, 10, 14, 18]

        for i in range(4):
            # In MediaPipe Y coordinates, lower values mean higher up on the screen
            if hand_landmarks[finger_tips[i]].y < hand_landmarks[finger_knuckles[i]].y:
                fingers.append(1) # Open
            else:
                fingers.append(0) # Tucked/Closed

        total_fingers = fingers.count(1)

        # --- MATCHING YOUR SPECIFIC GESTURES ---
        
        # 1. OPEN PALM (All 5 fingers extended)
        if total_fingers == 5:
            cv2.putText(frame, "PALM DETECTED: LIGHT ON", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if last_state != '1':
                if arduino: 
                    arduino.write(b'1')
                last_state = '1'
        
        # 2. CLOSED FIST (All fingers tucked in)
        elif total_fingers == 0:
            cv2.putText(frame, "FIST DETECTED: LIGHT OFF", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            if last_state != '0':
                if arduino: 
                    arduino.write(b'0')
                last_state = '0'
                
        # If your hand is mid-movement, it simply prints the intermediate finger count on screen
        else:
            cv2.putText(frame, "WAITING FOR GESTURE...", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    # 5. Display the camera window
    cv2.imshow("Webcam Light Control", frame)

    # Press 'q' to quit cleanly
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up resources
cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()