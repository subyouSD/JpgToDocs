import TextInImages
import time

if __name__ == '__main__':
    start = time.time()

    extractor = TextInImages.TextInImages("../test/font/Meeting Minute2.pdf", [1])

    extractor.insert_text_to_word(extractor.image_extracted_data_list, extractor.pdf_url[:-4] + ".docx")

    end = time.time()

    print("\nIt took " + str(end - start) + " seconds")
