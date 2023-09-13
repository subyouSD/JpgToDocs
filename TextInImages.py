import LineFormattedData
from pdf2image import convert_from_path
import time

class TextInImages:
    def __init__(self, pdf_url, column_num):
        self.pdf_url = pdf_url
        self.image_list = self.pdf2jpg(pdf_url)
        self.column_num = column_num

        self.image_extracted_data_list = self.create_text_list(self.image_list, self.column_num)

    def pdf2jpg(self, pdf_url):
        images = list()
        if not pdf_url.endswith('.pdf'):
            print("This is not a PDF file")
        else:
            images = convert_from_path(pdf_url)
        return images

    def create_text_list(self, images, column_num):
        image_text_list = []
        for idx, image in enumerate(images):
            # image_numpy = np.array(image)
            text_in_image = LineFormattedData.LineFormattedData(image, column_num)
            line_formatted = text_in_image.line_formatted_data
            image_text_list.append(line_formatted)

        return image_text_list

if __name__ == '__main__':
    start = time.time()

    extractor = TextInImages("./test/Meeting Minute3.pdf", 2)
    print(extractor.pdf_url)
    for i in extractor.image_extracted_data_list:
        for j in i:
            print(j['text'], end="")

    end = time.time()

    print("\nIt took " + str(end - start) + " seconds")

