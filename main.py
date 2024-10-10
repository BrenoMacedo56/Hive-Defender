import cv2
import cvzone
import math
import time
from ultralytics import YOLO
from typing import List


class VarroaDetector:
    def __init__(self, model_path: str, class_names: List[str], camera_id: int = 0, alert_duration: int = 20,
                 confidence_threshold: float = 0.5):
        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(3, 1850)
        self.cap.set(4, 1850)

        self.model = YOLO(model_path)
        self.class_names = class_names
        self.alert_duration = alert_duration
        self.threat_detected = False
        self.threat_time = None
        self.confidence_threshold = confidence_threshold

        self.prev_frame_time = 0
        self.new_frame_time = 0

    def detect_threat(self, img: cv2.Mat) -> None:
        results = self.model(img, stream=True)

        for r in results:
            boxes = r.boxes
            for box in boxes:
                conf = math.ceil((box.conf[0] * 100)) / 100

                # Only process detections with confidence >= threshold
                if conf >= self.confidence_threshold:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    w, h = x2 - x1, y2 - y1
                    cvzone.cornerRect(img, (x1, y1, w, h))

                    cls = int(box.cls[0])
                    label = self.class_names[cls]

                    cvzone.putTextRect(img, f'{label} {conf}', (max(0, x1), max(35, y1)), scale=1, thickness=1)

                    if label == "Mite" and not self.threat_detected:
                        self.threat_detected = True
                        self.threat_time = time.time()
                        self._display_alert_text(img)
                        print("Threat: Varroa Mite detected!")
                        print("Recommendation: Use chemical treatments or biological control.")

    def _display_alert_text(self, img: cv2.Mat) -> None:
        cvzone.putTextRect(img, "ALERT: Varroa Mite detected!", (20, 50), scale=2, thickness=2, colorR=(0, 0, 255))

    def display_fps(self, img: cv2.Mat) -> None:
        self.new_frame_time = time.time()
        fps = 1 / (self.new_frame_time - self.prev_frame_time)
        self.prev_frame_time = self.new_frame_time
        cvzone.putTextRect(img, f"FPS: {fps:.2f}", (20, 100), scale=1, thickness=1)

    def display_alert(self, img: cv2.Mat) -> None:
        if self.threat_detected and (time.time() - self.threat_time <= self.alert_duration):
            self._display_alert_text(img)
        elif self.threat_detected and (time.time() - self.threat_time > self.alert_duration):
            self.threat_detected = False

    def release_resources(self) -> None:
        self.cap.release()
        cv2.destroyAllWindows()

    def execute(self) -> None:
        while True:
            success, img = self.cap.read()
            if not success:
                break

            self.detect_threat(img)
            self.display_fps(img)
            self.display_alert(img)

            cv2.imshow("Image", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.release_resources()

def main():
    model_path = "Trained_models/best1.pt"
    class_names = ['Bee', 'Mite', 'pollen']

    detector = VarroaDetector(model_path, class_names, confidence_threshold=0.7)
    detector.execute()

if __name__ == "__main__":
    main()