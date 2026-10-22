import fitz

def extract_text(pdf_path):
    print("Opening PDF:", pdf_path)

    doc = fitz.open(pdf_path)

    print("Total Pages:", len(doc))

    text = ""

    for i, page in enumerate(doc):
        page_text = page.get_text()
        print(f"Page {i+1}: {len(page_text)} characters")
        text += page_text

    doc.close()

    return text