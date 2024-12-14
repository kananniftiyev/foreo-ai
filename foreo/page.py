from PyPDF2 import PdfReader

class PageText:
  def __init__(self, reader: PdfReader):
    page_count: int = 0
    pages = {}

    page_count = len(reader.pages)

    for i in reader.pages:
      page_count+= 1
      pages[page_count] = i.extract_text

  def return_page(page_number: int):
    pass

  def all_article():
    pass

