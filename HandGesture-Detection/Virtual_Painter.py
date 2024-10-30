import cv2
import mediapipe as mp
import numpy as np
import os
import math

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# For webcam input:
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FPS, 10)
width, height = 1280, 720
cap.set(3, width)
cap.set(4, height)

# Image that will contain the drawing and then passed to the camera image
imgCanvas = np.zeros((height, width, 3), np.uint8)

# Getting all header images in a list
folderPath = 'Hand Tracking Project/Header'
myList = os.listdir(folderPath)
overlayList = [cv2.imread(f'{folderPath}/{imPath}') for imPath in myList]

# Presettings
header = overlayList[0]
drawColor = (0, 0, 255)
thickness = 20
tipIds = [4, 8, 12, 16, 20]
xp, yp = [0, 0]

# Improved detection and tracking confidence
with mp_hands.Hands(min_detection_confidence=0.9, min_tracking_confidence=0.8, max_num_hands=1) as hands:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            break

        # Flip image and convert color
        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = hands.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Draw hands if detected
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                points = [[int(lm.x * width), int(lm.y * height)] for lm in hand_landmarks.landmark]

                if points:
                    x1, y1 = points[8]  # Index finger
                    x2, y2 = points[12] # Middle finger
                    x3, y3 = points[4]  # Thumb
                    x4, y4 = points[20] # Pinky

                    # Finger state tracking for gestures
                    fingers = [
                        points[tipIds[0]][0] < points[tipIds[0] - 1][0],  # Thumb
                        points[tipIds[1]][1] < points[tipIds[1] - 2][1],  # Index
                        points[tipIds[2]][1] < points[tipIds[2] - 2][1],  # Middle
                        points[tipIds[3]][1] < points[tipIds[3] - 2][1],  # Ring
                        points[tipIds[4]][1] < points[tipIds[4] - 2][1]   # Pinky
                    ]

                    ## Selection Mode
                    if fingers[1] and fingers[2] and not any(fingers[i] for i in [0, 3, 4]):
                        xp, yp = [x1, y1]
                        if y1 < 125:
                            if 170 < x1 < 295:
                                header = overlayList[0]
                                drawColor = (0, 0, 255)
                            elif 436 < x1 < 561:
                                header = overlayList[1]
                                drawColor = (255, 0, 0)
                            elif 700 < x1 < 825:
                                header = overlayList[2]
                                drawColor = (0, 255, 0)
                            elif 980 < x1 < 1105:
                                header = overlayList[3]
                                drawColor = (0, 0, 0)
                        cv2.rectangle(image, (x1-10, y1-15), (x2+10, y2+23), drawColor, cv2.FILLED)

                    ## Standby Mode
                    if fingers[1] and fingers[4] and not any(fingers[i] for i in [0, 2, 3]):
                        cv2.line(image, (xp, yp), (x4, y4), drawColor, 5)
                        xp, yp = [x1, y1]

                    ## Draw Mode
                    if fingers[1] and not any(fingers[i] for i in [0, 2, 3, 4]):
                        cv2.circle(image, (x1, y1), int(thickness/2), drawColor, cv2.FILLED)
                        if xp == 0 and yp == 0:
                            xp, yp = [x1, y1]
                        cv2.line(imgCanvas, (xp, yp), (x1, y1), drawColor, thickness)
                        xp, yp = [x1, y1]

                    ## Clear canvas when hand is closed
                    if all(f == 0 for f in fingers):
                        imgCanvas = np.zeros((height, width, 3), np.uint8)
                        xp, yp = [x1, y1]

                    ## Adjust thickness
                    if fingers[0] and fingers[1] and not any(fingers[i] for i in [2, 3, 4]):
                        r = int(math.sqrt((x1 - x3)**2 + (y1 - y3)**2) / 3)
                        cv2.circle(image, ((x1 + x3) // 2, (y1 + y3) // 2), int(r/2), drawColor, -1)
                        if fingers[4]:
                            thickness = r

        # Overlay header and combine canvas with main image
        image[0:125, 0:width] = header
        imgGray = cv2.cvtColor(imgCanvas, cv2.COLOR_BGR2GRAY)
        _, imgInv = cv2.threshold(imgGray, 5, 255, cv2.THRESH_BINARY_INV)
        imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
        img = cv2.bitwise_and(image, imgInv)
        img = cv2.bitwise_or(img, imgCanvas)

        cv2.imshow('Hand Tracking Paint', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
