# framework/ocr_pipeline.py

from PIL import Image

class OcrPipeline:
    def __init__(self, ocr_service):
        self.ocr_service = ocr_service

    def preprocess_image(self, image_path):
        try:
            with Image.open(image_path) as img:
                grayscale_img = img.convert('L')
                return grayscale_img
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None

    def process_image(self, image_path):
        preprocessed_image = self.preprocess_image(image_path)
        if preprocessed_image is None:
            return None
        try:
            result = self.ocr_service.recognize_text(preprocessed_image)
            return result
        except Exception as e:
            print(f"Error processing OCR: {e}")
            return None
