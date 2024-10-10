import cv2
import cvzone
import math
import time
from ultralytics import YOLO
from typing import List


class VarroaDetector:
    """
    Classe para detectar a presença de Varroa Mite (ou outros objetos) em imagens/vídeos
    capturados em tempo real utilizando um modelo de detecção de objetos YOLO.
    """

    def __init__(self, model_path: str, class_names: List[str], camera_id: int = 0, alert_duration: int = 20,
                 confidence_threshold: float = 0.5):
        """
        Inicializa o detector Varroa com os parâmetros fornecidos.

        :param model_path: Caminho para o modelo YOLO treinado.
        :param class_names: Lista com os nomes das classes que o modelo pode detectar.
        :param camera_id: ID da câmera usada para captura (padrão é 0, para webcam).
        :param alert_duration: Duração do alerta em segundos após a detecção de ameaça.
        :param confidence_threshold: Valor de confiança mínimo para considerar uma detecção válida.
        """
        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(3, 1850)  # Largura da imagem capturada
        self.cap.set(4, 1850)  # Altura da imagem capturada

        self.model = YOLO(model_path)
        self.class_names = class_names
        self.alert_duration = alert_duration
        self.threat_detected = False  # Flag para verificar se uma ameaça foi detectada
        self.threat_time = None  # Armazena o tempo da última detecção
        self.confidence_threshold = confidence_threshold  # Confiança mínima para a detecção ser considerada válida

        self.prev_frame_time = 0  # Tempo do quadro anterior (para calcular FPS)
        self.new_frame_time = 0  # Tempo do quadro atual (para calcular FPS)

    def detect_threat(self, img: cv2.Mat) -> None:
        """
        Detecta ameaças (ex. Varroa Mite) na imagem fornecida.

        :param img: A imagem na qual a detecção será realizada.
        """
        results = self.model(img, stream=True)

        # Itera sobre os resultados de detecção
        for r in results:
            boxes = r.boxes
            for box in boxes:
                conf = math.ceil((box.conf[0] * 100)) / 100  # Confiança da detecção

                # Processa apenas detecções com confiança >= ao limite definido
                if conf >= self.confidence_threshold:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  # Coordenadas do bounding box
                    w, h = x2 - x1, y2 - y1  # Largura e altura do bounding box
                    cvzone.cornerRect(img, (x1, y1, w, h))  # Desenha o retângulo na imagem

                    cls = int(box.cls[0])  # Índice da classe detectada
                    label = self.class_names[cls]  # Nome da classe

                    cvzone.putTextRect(img, f'{label} {conf}', (max(0, x1), max(35, y1)), scale=1, thickness=1)

                    # Se for detectado um 'Mite' (Varroa) e não houver alerta ativo
                    if label == "Mite" and not self.threat_detected:
                        self.threat_detected = True  # Marca que uma ameaça foi detectada
                        self.threat_time = time.time()  # Registra o tempo da detecção
                        self._display_alert_text(img)  # Exibe o alerta na imagem
                        print("Threat: Varroa Mite detected!")  # Alerta no terminal
                        print("Recommendation: Use chemical treatments or biological control.")  # Sugestão de ação

    def _display_alert_text(self, img: cv2.Mat) -> None:
        """
        Exibe um texto de alerta na imagem quando uma ameaça é detectada.

        :param img: A imagem na qual o alerta será exibido.
        """
        cvzone.putTextRect(img, "ALERT: Varroa Mite detected!", (20, 50), scale=2, thickness=2, colorR=(0, 0, 255))

    def display_fps(self, img: cv2.Mat) -> None:
        """
        Calcula e exibe os frames por segundo (FPS) na imagem.

        :param img: A imagem na qual o FPS será exibido.
        """
        self.new_frame_time = time.time()
        fps = 1 / (self.new_frame_time - self.prev_frame_time)  # Calcula o FPS
        self.prev_frame_time = self.new_frame_time
        cvzone.putTextRect(img, f"FPS: {fps:.2f}", (20, 100), scale=1, thickness=1)

    def display_alert(self, img: cv2.Mat) -> None:
        """
        Exibe um alerta visual se uma ameaça foi detectada e o tempo do alerta não tiver expirado.

        :param img: A imagem na qual o alerta será exibido.
        """
        if self.threat_detected and (time.time() - self.threat_time <= self.alert_duration):
            self._display_alert_text(img)  # Mantém o alerta visível por 'alert_duration' segundos
        elif self.threat_detected and (time.time() - self.threat_time > self.alert_duration):
            self.threat_detected = False  # Reseta o alerta após o tempo definido

    def release_resources(self) -> None:
        """
        Libera os recursos da câmera e fecha todas as janelas do OpenCV.
        """
        self.cap.release()
        cv2.destroyAllWindows()

    def execute(self) -> None:
        """
        Inicia o loop principal de captura de imagens e processamento do detector.
        """
        while True:
            success, img = self.cap.read()  # Captura a imagem da câmera
            if not success:
                break  # Interrompe o loop se não houver imagem

            self.detect_threat(img)  # Detecta ameaças na imagem
            self.display_fps(img)  # Exibe o FPS na imagem
            self.display_alert(img)  # Exibe o alerta visual na imagem, se houver uma ameaça

            cv2.imshow("Image", img)  # Mostra a imagem processada
            if cv2.waitKey(1) & 0xFF == ord('q'):  # Sai do loop se a tecla 'q' for pressionada
                break

        self.release_resources()  # Libera os recursos ao final do loop


def main():
    """
    Função principal para inicializar o detector e iniciar o processo de detecção de Varroa.
    """
    model_path = "Trained_models/best1.pt"  # Caminho para o modelo YOLO treinado
    class_names = ['Bee', 'Mite', 'pollen']  # Nomes das classes que o modelo pode detectar

    detector = VarroaDetector(model_path, class_names, confidence_threshold=0.7)  # Inicializa o detector
    detector.execute()  # Inicia a execução do detector


if __name__ == "__main__":
    main()  # Executa o código se o script for rodado diretamente
