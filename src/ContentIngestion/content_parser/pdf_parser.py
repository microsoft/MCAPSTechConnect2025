import base64
import imghdr
import io
import logging
from typing import Generator, Optional, Tuple
import PyPDF2
from PIL import Image
from askai_core.Utility.prompts import IMAGE_DESCRIPTION_PROMPT, TEXT_DATA_PROMPT

from askai_core.content_parser.base_parser import BaseParser

class PDFParser(BaseParser):
    def extract_text(self, IS_PARSE_BY_DOCINTELLIGENCE: bool = False) -> Generator[Tuple[int, str, bool], None, None]:
        try:
            file_content = self.file_content
            is_image_present = False
            with io.BytesIO(initial_bytes=file_content) as pdf_bytes:
                pdf_reader = PyPDF2.PdfReader(stream=pdf_bytes)
                for index, page in enumerate(pdf_reader.pages):
                    page_number = index + 1
                    logging.info(f"IS_PARSE_BY_DOCINTELLIGENCE: {IS_PARSE_BY_DOCINTELLIGENCE}")
                    page_content = None
                    if not IS_PARSE_BY_DOCINTELLIGENCE:
                        page_content = page.extract_text()
                        logging.info(f"Extracted page content from pypdf: {page_content}")
                    
                    if (page_content is None or page_content.strip() == "") and self.documentAnalysisClient is not None:
                        logging.info(f"documentAnalysisClient is not none")
                        
                        form_recognizer_content = self._extract_form_recognizer_content(page_number)
                        logging.info(f"Extracted page content from form_recognizer_content: {form_recognizer_content}")
                        
                        if form_recognizer_content:
                            page_content = " ".join(line.content for page in form_recognizer_content for line in page.lines if line.content)
                            logging.info(f"Extracted page content from form_recognizer_content page_content: {page_content}")
                            
                    if self.openai_utility is not None and self.storage_manager is not None and self.process_image:
                        image_info = self.get_image_description(page, page_content, page_number)
                        for image in image_info:
                            logging.info(f"Received Image Info for images on pageNumber: {page_number}")
                            page_content += " " 
                            page_content += image
                            is_image_present = True
                    yield page_number, page_content, is_image_present
        except Exception as e:
            logging.error(f"Error extracting text from pdf document with exception: {e}, from PageNumber: {page_number}")

    def _extract_form_recognizer_content(self, page_number: int) :
        document_analysis_client = self.documentAnalysisClient
        poller = document_analysis_client.begin_analyze_document("prebuilt-read", self.file_content, pages=page_number)
        result = poller.result()
        return result.pages if result.content else None
    
    def extract_image(self) -> Generator[Tuple[int, list], None, None]:
        file_content = self.file_content
        with io.BytesIO(initial_bytes=file_content) as pdf_bytes:
            pdf_reader = PyPDF2.PdfReader(stream=pdf_bytes)
            for index, page in enumerate(pdf_reader.pages):
                page_number = index + 1
                page_content = page.extract_text()
                if self.openai_utility is not None and self.storage_manager is not None:
                    image_info = self.get_image_description(page, page_content, page_number)
                    yield page_number, image_info

    def get_image_description(self, current_page, page_content, page_number) :
        image_info = []
        try:
            images = current_page.images
        except Exception as e:
            logging.error(f"Error while extracting images: {str(e)}")
            return image_info
        for image in enumerate(images):
            try:
                image_bytes = Image.open(io.BytesIO(image[1].data))
                image_type = image_bytes.format
                if image_bytes.width >= 100 and image_bytes.height >= 100 and not self.is_image_empty(image_bytes):
                    base64_encoded_data = base64.b64encode(image[1].data).decode('utf-8')
                    image_data = f"data:image/{image_type};base64,{base64_encoded_data}"
                    prompt = IMAGE_DESCRIPTION_PROMPT
                    text_data = TEXT_DATA_PROMPT
                    text_data += page_content
                    description = self.openai_utility.generate_image_description(image_data, text_data, prompt)
                    if description is not None:
                        self.storage_manager.upload_to_blob(image[1].data, file_format=f"{image_type}")
                        blob_name = self.storage_manager.blob_name
                        image_description = " [ImageBlobName = " + str(blob_name) + " ] "
                        image_description += description
                        image_info.append(image_description)
                        logging.info(f"Image description found for image at page number: {page_number} blob name: {blob_name}")
                    else:
                        logging.info(f"Image description is None for image at page number: {page_number}")
            except Exception as e:
                logging.error(f"Error while processing the image at page number: {page_number} error is: {str(e)}")
                continue
        return image_info
    
    def is_image_empty(self, image):
        img_gray = image.convert('L')
        pixels = list(img_gray.getdata())
        is_black = all(pixel <= 5 for pixel in pixels)
        is_white = all(pixel >= 250 for pixel in pixels)
        return is_black or is_white