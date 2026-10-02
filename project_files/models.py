from pathlib import Path

from ultralytics import YOLO


class Model:
    def __init__(self, image_path, model_path="model.pt"):
        self.model = YOLO(model_path)
        self.image_path = image_path
        self.results = []

    def predict(self, image_path, save_path="output.jpg"):
        self.image_path = image_path
        self.results = list(self.model(image_path, stream=True))

        output_path = Path(save_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.results:
            self.results[0].save(filename=str(output_path))

        return self.results

    def get_results(self, image_path=None):
        if image_path:
            self.image_path = image_path

        details = []
        for result in self.results:
            boxes = result.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]
                confidence = float(box.conf[0])
                details.append((label, confidence, cls_id))

            break

        return details

