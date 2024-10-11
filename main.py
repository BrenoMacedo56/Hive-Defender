import cv2
import cvzone
import math
import time

from ultralytics import YOLO
from typing import List
from twilio.rest import Client  # Imports the Twilio library for sending messages


class VarroaDetector:
    """
       Class for detecting the presence of Varroa Mite (or other objects) in images/videos
       captured in real-time or from a video file using a YOLO object detection model.
    """

    def __init__(self, model_path: str, class_names: List[str], camera_id: int = 0, alert_duration: int = 20,
                 confidence_threshold: float = 0.5):
        """
        Initializes the Varroa detector with the provided parameters.

        :param model_path: Path to the trained YOLO model.
        :param class_names: List of class names that the model can detect.
        :param camera_id: camera id to be processed.
        :param alert_duration: Duration of the alert in seconds after a threat detection.
        :param confidence_threshold: Minimum confidence value to consider a detection valid.
        """
        self.cap = cv2.VideoCapture(camera_id)  # Opens the camera from the provided id
        self.cap.set(3, 1850)  # Width of the captured video (if applicable)
        self.cap.set(4, 1850)  # Height of the captured video (if applicable)

        self.model = YOLO(model_path)
        self.class_names = class_names
        self.alert_duration = alert_duration
        self.threat_detected = False  # Flag to check if a threat was detected
        self.threat_time = None  # Stores the time of the last detection
        self.confidence_threshold = confidence_threshold  # Minimum confidence for the detection to be considered valid

        self.prev_frame_time = 0  # Time of the previous frame (to calculate FPS)
        self.new_frame_time = 0  # Time of the current frame (to calculate FPS)

    def detect_threat(self, img: cv2.Mat) -> None:
        """
        Detects threats (e.g. Varroa Mite) in the provided image.

        :param img: The image on which the detection will be performed.
        """
        results = self.model(img, stream=True)

        # Iterates over the detection results
        for r in results:
            boxes = r.boxes
            for box in boxes:
                conf = math.ceil((box.conf[0] * 100)) / 100  # Detection confidence

                # Processes only detections with confidence >= the defined threshold
                if conf >= self.confidence_threshold:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                    w, h = x2 - x1, y2 - y1  # Width and height of the bounding box
                    cvzone.cornerRect(img, (x1, y1, w, h))  # Draws the rectangle on the image

                    cls = int(box.cls[0])  # Index of the detected class
                    label = self.class_names[cls]  # Class name

                    cvzone.putTextRect(img, f'{label} {conf}', (max(0, x1), max(35, y1)), scale=1, thickness=1)

                    # If a 'Mite' (Varroa) is detected and there's no active alert
                    if label == "Mite" and not self.threat_detected:
                        self.threat_detected = True  # Marks that a threat was detected
                        self.threat_time = time.time()  # Records the detection time
                        self._display_alert_text(img)  # Displays the alert on the image

                        # Sends a WhatsApp message
                        send_whatsapp_alert("Varroa Mite detected! Use chemical treatments or biological control.")

                        print("Threat: Varroa Mite detected!")
                        print("Recommendation: Use chemical treatments or biological control.")

    def _display_alert_text(self, img: cv2.Mat) -> None:
        """
        Displays an alert text on the image when a threat is detected.

        :param img: The image on which the alert will be displayed.
        """
        cvzone.putTextRect(img, "ALERT: Varroa Mite detected!", (20, 50), scale=2, thickness=2, colorR=(0, 0, 255))

    def display_fps(self, img: cv2.Mat) -> None:
        """
        Calculates and displays the frames per second (FPS) on the image.

        :param img: The image on which the FPS will be displayed.
        """
        self.new_frame_time = time.time()
        fps = 1 / (self.new_frame_time - self.prev_frame_time)  # Calculates the FPS
        self.prev_frame_time = self.new_frame_time
        cvzone.putTextRect(img, f"FPS: {fps:.2f}", (20, 100), scale=1, thickness=1)

    def display_alert(self, img: cv2.Mat) -> None:
        """
        Displays a visual alert if a threat was detected and the alert time hasn't expired.

        :param img: The image on which the alert will be displayed.
        """
        if self.threat_detected and (time.time() - self.threat_time <= self.alert_duration):
            self._display_alert_text(img)  # Keeps the alert visible for 'alert_duration' seconds
        elif self.threat_detected and (time.time() - self.threat_time > self.alert_duration):
            self.threat_detected = False  # Resets the alert after the defined time

    def release_resources(self) -> None:
        """
        Releases the camera/video resources and closes all OpenCV windows.
        """
        self.cap.release()
        cv2.destroyAllWindows()

    def execute(self) -> None:
        """
        Starts the main loop of video capture and detector processing.
        """
        while True:
            success, img = self.cap.read()  # Captures the image from the video
            if not success:
                break  # Breaks the loop if there's no image

            self.detect_threat(img)  # Detects threats in the image
            self.display_fps(img)  # Displays the FPS on the image
            self.display_alert(img)  # Displays the visual alert on the image, if there's a threat

            cv2.imshow("Image", img)  # Shows the processed image
            if cv2.waitKey(1) & 0xFF == ord('q'):  # Exits the loop if the 'q' key is pressed
                break

        self.release_resources()  # Releases the resources at the end of the loop


def send_whatsapp_alert(message: str):
    """
    Sends a WhatsApp alert using Twilio API.

    :param message: The content of the message to be sent.
    """
    # Your Twilio credentials
    account_sid = 'You Dont Need to Know ;)'
    auth_token = 'You Dont Need to Know ;)'
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body="""
        🐝 Alerta de Saúde Apícola - Hive-Defenders 🐝

        Prezado Apicultor,

        Identificamos a presença do ácaro Varroa destructor na colmeia #A123. Esta situação requer atenção imediata para garantir a saúde e produtividade de sua colônia.

        🔍 Ações Recomendadas:

        1. Inspeção Imediata:
           - Realize uma vistoria detalhada da colmeia afetada.
           - Verifique outras colmeias próximas para possível contaminação.

        2. Tratamento:
           - Considere a aplicação de ácido oxálico ou fórmico.
           - Consulte um especialista para determinar a dosagem adequada.

        3. Controle Biológico:
           - Avalie a introdução de ácaros predadores naturais.
           - Implemente técnicas de manejo integrado de pragas.

        4. Monitoramento Contínuo:
           - Aumente a frequência das inspeções nas próximas semanas.
           - Utilize fundos de colmeia com tela para contagem de ácaros.

        5. Fortalecimento da Colônia:
           - Garanta alimentação suplementar se necessário.
           - Considere a união de colônias fracas.

        ⚠️ Lembre-se: O tratamento precoce é crucial para prevenir a propagação e minimizar os danos à sua operação apícola.

        A equipe Hive-Defenders está à disposição para orientações adicionais. Entre em contato conosco pelo telefone (XX) XXXX-XXXX ou e-mail suporte@hive-defenders.com.

        Proteja suas abelhas, proteja seu investimento!

        Atenciosamente,
        Equipe Hive-Defenders
        """,
        media_url="https://i.pinimg.com/1200x/9d/d8/88/9dd888584a7891413b880a3770e04ddf.jpg",
        from_='whatsapp:+14155238886',
        to='whatsapp:You Dont Need to Know ;)'
    )

    print(f"Message sent with SID: {message.sid}")


def main():
    """
    Main function to initialize the detector and process the provided video.
    """
    model_path = "Trained_models/best1.pt"  # Path to the trained YOLO model
    class_names = ['Bee', 'Mite', 'pollen']  # Names of the classes that the model can detect

    detector = VarroaDetector(model_path, class_names, confidence_threshold=0.2)  # Initializes the detector
    detector.execute()  # Starts the detector execution


if __name__ == "__main__":
    main()  # Executes the code if the script is run directly