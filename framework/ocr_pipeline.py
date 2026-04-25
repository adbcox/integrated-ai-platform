# framework/ocr_pipeline.py

class OcrPipeline:
    def __init__(self, ocr_service):
        self.ocr_service = ocr_service

    def process_image(self, image_path):
        try:
            result = self.ocr_service.recognize_text(image_path)
            return result
        except Exception as e:
            print(f"Error processing OCR: {e}")
            return None

# Example usage:
# from framework.ocr_pipeline import OcrPipeline
# ocr_service = SomeOcrService()  # Replace with actual OCR service implementation
# pipeline = OcrPipeline(ocr_service)
# result = pipeline.process_image("path/to/image.jpg")
