from pathlib import Path
from tracker import Tracker
import cv2
import depthai as dai
import numpy as np
import time
import blobconverter
import math
import serial


# nn data, being the bounding box locations, are in <0..1> range - they need to be normalized with frame width/height
def frameNorm(frame, bbox):
    normVals = np.full(len(bbox), frame.shape[0])
    normVals[::2] = frame.shape[1]
    return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)


def displayFrame(name, frame, detections):
    color = (255, 0, 0)
    for detection in detections:
        bbox = frameNorm(frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
        cv2.putText(frame, labelMap[detection.label], (bbox[0] + 10, bbox[1] + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5,
                    255)
        cv2.putText(frame, f"{int(detection.confidence * 100)}%", (bbox[0] + 10, bbox[1] + 40),
                    cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
    # Show the frame
    cv2.imshow(name, frame)


nnPath = blobconverter.from_openvino(xml="stick_tiny_YOLO_v4/yolov4_tiny_sticks.xml",
                                     bin="stick_tiny_YOLO_v4/yolov4_tiny_sticks.bin",
                                     data_type="FP16",
                                     shaves=6,
                                     version="2021.3",
                                     use_cache=True)

if not Path(nnPath).exists():
    import sys

    raise FileNotFoundError(f'Required file/s not found, please run "{sys.executable} install_requirements.py"')

"""
Initialise Tracker
"""
# Variables initialization
track_colors = {}
np.random.seed(0)

# build array for all tracks and classes
track_classes = {}

tracker_KF = Tracker(dist_thresh=250,
                     max_frames_to_skip=60,
                     max_trace_length=300,
                     trackIdCount=0,
                     use_kf=True,
                     std_acc=10,
                     x_std_meas=0.5,
                     y_std_meas=0.5,
                     dt=1 / 60)

max_allowed_deviation = 50

print("INITIALISED TRACKER!")

found_arduino = False
try:
    ser = serial.Serial("COM8", 115200, timeout=None)
    time.sleep(2)
    print("Opened connection to 2DTreadMill Arduino")
    found_arduino = True
except:
    print("Failed to open Serial Port! Double check your ODT is connected correctly!")
    print("Running Oak-D demo mode in...")
    for i in range(3):
        print(3-i)
        time.sleep(1)

# some necessary defenitions
font = cv2.FONT_HERSHEY_SIMPLEX

labelMap = ["stick insect"]

syncNN = False

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and outputs
camRgb = pipeline.create(dai.node.ColorCamera)
detectionNetwork = pipeline.create(dai.node.YoloDetectionNetwork)
xoutRgb = pipeline.create(dai.node.XLinkOut)
nnOut = pipeline.create(dai.node.XLinkOut)

xoutRgb.setStreamName("rgb")
nnOut.setStreamName("nn")

# Properties
# camRgb.setPreviewSize(320, 320)
camRgb.setPreviewSize(416, 416)
camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
camRgb.setInterleaved(False)
camRgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
camRgb.setFps(60)

# Network specific settings
detectionNetwork.setConfidenceThreshold(0.65)
detectionNetwork.setNumClasses(1)
detectionNetwork.setCoordinateSize(4)
detectionNetwork.setAnchors([10, 14, 23, 27, 37, 58, 81, 82, 135, 169, 344, 319])

# for 320 x 320
# detectionNetwork.setAnchorMasks({"side20": [1, 2, 3], "side10": [3, 4, 5]})
# 416 x 416
detectionNetwork.setAnchorMasks({"side26": [1, 2, 3], "side13": [3, 4, 5]})
detectionNetwork.setIouThreshold(0.5)
detectionNetwork.setBlobPath(nnPath)
detectionNetwork.setNumInferenceThreads(2)
detectionNetwork.input.setBlocking(False)

# Linking
camRgb.preview.link(detectionNetwork.input)
if syncNN:
    detectionNetwork.passthrough.link(xoutRgb.input)
else:
    camRgb.preview.link(xoutRgb.input)

detectionNetwork.out.link(nnOut.input)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:
    # Output queues will be used to get the rgb frames and nn data from the outputs defined above
    qRgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
    qDet = device.getOutputQueue(name="nn", maxSize=4, blocking=False)

    frame = None
    detections = []
    startTime = time.monotonic()
    counter = 0
    color2 = (255, 255, 255)

    while True:
        if syncNN:
            inRgb = qRgb.get()
            inDet = qDet.get()
        else:
            inRgb = qRgb.tryGet()
            inDet = qDet.tryGet()

        if inRgb is not None:
            frame = inRgb.getCvFrame()
            cv2.putText(frame, "NN fps: {:.2f}".format(counter / (time.monotonic() - startTime)),
                        (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4, color2)

        if inDet is not None:
            detections = inDet.detections
            counter += 1

        centres = []
        bounding_boxes = []
        predicted_classes = []

        if frame is not None:
            for detection in detections:
                bbox = frameNorm(frame=frame,
                                 bbox=(detection.xmin,
                                       detection.ymin,
                                       detection.xmax,
                                       detection.ymax))
                centres.append([[(bbox[0] + bbox[2]) / 2],
                                [(bbox[1] + bbox[3]) / 2]])
                bounding_boxes.append([bbox[0],
                                       bbox[2],
                                       bbox[1],
                                       bbox[3]])
                predicted_classes.append(labelMap[detection.label])

                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (150, 20, 150), 2)
                cv2.putText(frame, labelMap[detection.label], (bbox[0], bbox[1] - 10), font, 0.4, (150, 20, 150))

            if len(centres) > -1:

                # Track object using Kalman Filter
                tracker_KF.Update(centres,
                                  predicted_classes=predicted_classes,
                                  bounding_boxes=bounding_boxes)

                # For identified object tracks draw tracking line
                # Use various colors to indicate different track_id
                for i in range(len(tracker_KF.tracks)):
                    if len(tracker_KF.tracks[i].trace) > 1:
                        mname = "track_" + str(tracker_KF.tracks[i].track_id)

                        if mname not in track_colors:
                            track_colors[mname] = np.random.randint(low=100, high=255, size=3).tolist()

                        # draw direction of movement onto footage
                        x_t, y_t = tracker_KF.tracks[i].trace[-1]
                        tracker_KF_velocity = 5 * (tracker_KF.tracks[i].trace[-1] - tracker_KF.tracks[i].trace[-2])
                        x_t_future, y_t_future = tracker_KF.tracks[i].trace[-1] + tracker_KF_velocity * 0.1
                        cv2.arrowedLine(frame, (int(x_t), int(y_t)), (int(x_t_future), int(y_t_future)),
                                        (np.array(track_colors[mname]) - np.array([70, 70, 70])).tolist(), 3,
                                        tipLength=0.75)

                        for j in range(len(tracker_KF.tracks[i].trace) - 1):

                            # Draw trace line on preview
                            x1 = tracker_KF.tracks[i].trace[j][0][0]
                            y1 = tracker_KF.tracks[i].trace[j][1][0]
                            x2 = tracker_KF.tracks[i].trace[j + 1][0][0]
                            y2 = tracker_KF.tracks[i].trace[j + 1][1][0]
                            if mname not in track_colors:
                                track_colors[mname] = np.random.randint(low=100, high=255, size=3).tolist()
                            cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)),
                                     track_colors[mname], 2)

                        cv2.putText(frame,
                                    mname,
                                    (int(x1) - int(30 / 2),
                                     int(y1) - 30), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.4,
                                    track_colors[mname], 2)

                        # get distance from centre, plot deviation, and send motor commands
                        x_dev = (frame.shape[0] / 2) - x_t[0]
                        y_dev = (frame.shape[1] / 2) - y_t[0]

                        print("Deviation from centre: X", x_dev, "| Y", y_dev)

                        abs_deviation = math.sqrt(x_dev ** 2 + y_dev ** 2)
                        if abs_deviation >= max_allowed_deviation:
                            color_dev = (100, 20, 255)
                        else:
                            color_dev = (50, 255, 50)

                        cv2.arrowedLine(frame, (int(x_t), int(y_t)),
                                        (int(frame.shape[0] / 2), int(frame.shape[0] / 2)),
                                        color_dev, 2,
                                        tipLength=0.1)

                        # mark image centre
                        cv2.circle(frame, (int(frame.shape[0] / 2), int(frame.shape[1] / 2)),
                                   max_allowed_deviation, color_dev, 3)

                        cv2.rectangle(frame, (0, 0), (120, 50), (0, 0, 0), -1)

                        cv2.putText(frame, "X dev: " + str(x_dev),
                                    (2, 20), cv2.FONT_HERSHEY_TRIPLEX, 0.4, color_dev)
                        cv2.putText(frame, "Y dev: " + str(y_dev),
                                    (2, 40), cv2.FONT_HERSHEY_TRIPLEX, 0.4, color_dev)

                        # only write out motor commands once, for the most probable track
                        if found_arduino:
                            if i == 0:
                                x_dev_out, y_dev_out = int(x_dev[0][0]), int(y_dev[0][0])
                                command = "X " + str(x_dev_out) + " Y " + str(y_dev_out) + "      \n"
                                ser.write(command.encode(encoding='UTF-8'))

                                line = ser.readline()
                                if line:
                                    string = line.decode()
                                    print(string[:-2])

            cv2.imshow("preview", frame)

            if cv2.waitKey(1) == ord('q'):
                break

    cv2.destroyAllWindows()

    print("Stopping motors...")

    if found_arduino:
        for i in range(100):
            time.sleep(0.02)
            command = "X " + str(0.5) + " Y " + str(0.5) + "        \n"
            ser.write(command.encode(encoding='UTF-8'))
            line = ser.readline()

        print("\nMotors stopped. Closing OAK connection...")

print("Closed OAK connection.")
