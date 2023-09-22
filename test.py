from pdf2docx import Converter

pdf_file = './test/test_2.pdf'
docx_file = './test/abcdefg.docx'

# convert pdf to docx
cv = Converter(pdf_file)
cv.convert(docx_file)      # all pages by default
cv.close()

