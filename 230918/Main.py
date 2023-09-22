import TextInImages
import time

if __name__ == '__main__':
    start = time.time()

    extractor = TextInImages.TextInImages("../test/P02.pdf", [2,2])

    extractor.insert_text_to_word(extractor.image_extracted_data_list, extractor.pdf_url[:-4] + ".docx")

    end = time.time()

    print("\nIt took " + str(end - start) + " seconds")
