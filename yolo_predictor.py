from ultralytics import YOLO

# Must match the imgsz the model was trained with
IMGSZ = 640


class YoloPredictor:
    """Thin wrapper around an Ultralytics YOLO detector.

    predict() returns (boxes, labels, probs): xyxy pixel boxes, class indices that
    index into `class_names`, and confidences. All three are CPU tensors.
    """

    def __init__(self, model_path, device=None, imgsz=IMGSZ):
        self.model = YOLO(model_path)
        self.device = device
        self.imgsz = imgsz
        self.class_names = [self.model.names[i] for i in sorted(self.model.names)]

    def predict(self, image, top_k=-1, prob_threshold=0.3):
        # `image` is a BGR numpy array (same convention as cv2.imread)
        results = self.model.predict(
            image,
            conf=prob_threshold,
            max_det=top_k if top_k > 0 else 300,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )[0]

        boxes = results.boxes
        return boxes.xyxy.cpu(), boxes.cls.cpu().long(), boxes.conf.cpu()
