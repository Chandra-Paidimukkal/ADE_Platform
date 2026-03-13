import fitz


def extract_blocks(pdf_path):

    doc = fitz.open(pdf_path)

    blocks = []

    for page_num, page in enumerate(doc):

        for block in page.get_text("blocks"):

            x0, y0, x1, y1, text, *_ = block

            blocks.append({
                "text": text.strip(),
                "bbox": [x0, y0, x1, y1],
                "page": page_num
            })

    return blocks