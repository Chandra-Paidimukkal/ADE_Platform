import pytesseract
from PIL import Image
import fitz


def extract_text_from_images(pdf_path):

    text = ""

    doc = fitz.open(pdf_path)

    for page in doc:

        images = page.get_images()

        for img in images:

            xref = img[0]
            pix = fitz.Pixmap(doc, xref)

            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            text += pytesseract.image_to_string(image)

    return text