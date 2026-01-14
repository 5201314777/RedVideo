from ultralytics import YOLO
import cv2

class PersonDetector:
    def __init__(self):
        self.model = YOLO("../../yolov8s.pt")

    def detect(self, frame):
        print("YOLO detect called")
        results = self.model(frame, conf=0.4, classes=[0])
        boxes = []
        for r in results:
            for box in r.boxes.xyxy:
                boxes.append(box.cpu().numpy())
        return boxes
