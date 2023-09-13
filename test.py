from pdf2image import convert_from_path

# from PIL import Image
import pytesseract
# import spacy
import cv2
import time


def pdf2jpg(image_url):
    pages = list()
    if not image_url.endswith('.pdf'):
        print("this is not a pdf file")
    else:
        pages = convert_from_path(image_url)
        # for i, page in enumerate(pages):
        #     print(image_url[:-4] + "" + str(i + 1) + ".jpg")
        #     print(page)
        #     page.save(image_url[:-4]+""+str(i+1)+".jpg","JPEG")
    return pages


def extract_data_from_image(image, confidence=-1):  # 텍스트 및 좌표 추출
    # image = cv2.imread(image_path)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    extracted_data = []
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if data['conf'][i] > confidence:
            extracted_data.append({
                "text": text,
                "x": data['left'][i],
                "y": data['top'][i],
                "width": data['width'][i],
                "height": data['height'][i],
                "line_num": data['line_num'][i],
                "block_num": data['block_num'][i],
                "par_num": data['par_num'][i]
            })
    return extracted_data


def calculate_spacing_height(extracted_data):  # line spacing & word height 구하기

    max_height = max([word['height'] for word in extracted_data])

    total_gap = 0.0
    count = 0

    for i, data in enumerate(extracted_data[:-1]):  # block_num 이 같지 않으면, 개행 됐을 수 있음
        if (data['block_num'] == extracted_data[i + 1]['block_num']) & (
                data['line_num'] != extracted_data[i + 1]['line_num']) \
                & (data['par_num'] == extracted_data[i + 1]['par_num']):

            total_gap += extracted_data[i + 1]['y'] - data['y']
            count += 1

    if count == 0:
        avg_gap = 1.25 * max_height
    else:
        avg_gap = round(total_gap / count, 2)

    return avg_gap, max_height


def data_to_text_json_1(words, width, height):  # 개행 및 형식화
    spacing, avg_height = calculate_spacing_height(words)

    formatted_text = ""
    column_max_x = max([(word['x'] + word['width']) for word in words])

    min_y = min([word['y'] for word in words])
    bottom_max = height - min_y

    # 한 줄씩 나누기 위한 parameters
    line_formatted = []
    first_word_x = words[0]['x']
    first_word_y = words[0]['y']

    for idx, word in enumerate(words[:-1]):
        next_word = words[idx + 1]
        formatted_text += word['text'] + ' '  # 띄움이 확인 불가, spacing 1개로 가정

        # block_num 이 다르다는 것은 무조건 개행, block_num 이 같은데 par_num 이 다른 건 블락 안에서 paragraph 로 나뉨 -> 개행
        # 블락이 다를 때 또는 같은데 paragraph 가 다를 경우 개행
        # if (word['block_num'] != next_word['block_num']) \
        #         | ((word['block_num'] == next_word['block_num']) & (word['par_num'] != next_word['par_num'])):
        #     pass
        #
        # # 블락이 같고 paragraph 도 같은데, 라인이 다르면 뒤에 500px 이상 남으면 개행
        # elif (word['block_num'] == next_word['block_num']) & (word['par_num'] == next_word['par_num']) \
        #         & (word['line_num'] != next_word['line_num']) & \
        #         (column_max_x - word['x'] - word['width'] > next_word['width']):
        #     pass
        #
        # # 라인이 다른데 다음 줄이 알파벳 으로 시작 하지 않으면 개행
        # elif (word['line_num'] != next_word['line_num']) & (not next_word['text'][0].isalpha()):
        #     pass
        # else:
        #     continue

        if (word['y'] < (next_word['y']-avg_height)) & (word['text'][-1] != '.'):
            continue
        else:
            pass

        gap = next_word['y'] - word['y']
        if word['y'] > next_word['y']:
            gap = bottom_max - word['y']

        while gap > avg_height:
            formatted_text += '\n'
            gap -= spacing
            if gap <= avg_height:
                line_formatted.append({
                    'text': formatted_text,
                    'x': first_word_x,
                    'y': first_word_y,
                })
                first_word_x = next_word['x']
                first_word_y = next_word['y']
                # formatted_text = ''

    formatted_text += words[-1]['text']
    line_formatted.append({
        'text': formatted_text,
        'x': first_word_x,
        'y': first_word_y,
    })

    return formatted_text


def data_to_text_json_2(words, width, height):  # 개행 및 형식화
    spacing, avg_height = calculate_spacing_height(words)

    formatted_text = ""

    middle_line_x = width / 2
    first_column_max_x = max([(word['x']+word['width']) for word in words if (word['x']+word['width']) < middle_line_x])
    second_column_max_x = max([(word['x']+word['width']) for word in words if (word['x']+word['width']) > middle_line_x])

    min_y = min([word['y'] for word in words])
    bottom_max = height - min_y

    # 한 줄씩 나누기 위한 parameters
    line_formatted = []
    first_word_x = words[0]['x']
    first_word_y = words[0]['y']

    for idx, word in enumerate(words[:-1]):
        next_word = words[idx + 1]
        formatted_text += word['text'] + ' '  # 띄움이 확인 불가, spacing 1개로 가정

        # 페이지 중간의 값 보다 작으면 2단 페이지 에서 왼편, 크면 오른 편의 맥스 기준을 지정
        if word['x'] < middle_line_x:
            criteria = first_column_max_x
        else:
            criteria = second_column_max_x

        # block_num 이 다르다는 것은 무조건 개행, block_num 이 같은데 par_num 이 다른 건 블락 안에서 paragraph 로 나뉨 -> 개행
        # 블락이 다를 때 또는 같은데 paragraph 가 다를 경우 개행
        if (word['block_num'] != next_word['block_num']) \
                | ((word['block_num'] == next_word['block_num']) & (word['par_num'] != next_word['par_num'])):
            pass

        # 블락이 같고 paragraph 도 같은데, 라인이 다르면 뒤에 500px 이상 남으면 개행
        elif (word['block_num'] == next_word['block_num']) & (word['par_num'] == next_word['par_num']) \
                & (word['line_num'] != next_word['line_num']) \
                & (criteria - (word['x'] + word['width']) > next_word['width'] + 10):
            pass

        # 라인이 다른데 다음 줄이 알파벳 으로 시작 하지 않으면 개행
        elif (word['line_num'] != next_word['line_num']) & (not next_word['text'][0].isalpha()) \
                & ((word['par_num'] != next_word['par_num']) | (word['block_num'] != next_word['block_num'])):
            pass
        else:
            continue

        gap = next_word['y'] - word['y']
        if word['y'] > next_word['y'] | ((word['x'] < middle_line_x) & (next_word['x'] > middle_line_x)):
            gap = bottom_max - word['y'] + next_word['y'] - min_y

        while gap > avg_height:
            formatted_text += '\n'
            gap -= spacing
            #
            if gap <= avg_height:
                line_formatted.append({
                    'text': formatted_text,
                    'x': first_word_x,
                    'y': first_word_y,
                })
                first_word_x = next_word['x']
                first_word_y = next_word['y']
                # formatted_text = ''

    formatted_text += words[-1]['text']
    line_formatted.append({
        'text': formatted_text,
        'x': first_word_x,
        'y': first_word_y,
    })

    return formatted_text


def test(url, column_num):
    start = time.time()

    # images = pdf2jpg(url)
    image = cv2.imread(url)

    # column 1 일때와, 2일때, 돌리는 function 정해주기
    column_functions = {
        1: data_to_text_json_1,
        2: data_to_text_json_2,
    }

    if column_num in column_functions:
        selected_function = column_functions[column_num]
        # for i, image in enumerate(images):
        width, height, channels = image.shape
        # print(width, height)
        extracted_data = extract_data_from_image(image)
        # for x in range(len(extracted_data) // 4):
        #     print(extracted_data[x * 4])
        #     print(extracted_data[x * 4 + 1])
        #     print(extracted_data[x * 4 + 2])
        #     print(extracted_data[x * 4 + 3])
        line_formatted = selected_function(extracted_data, width, height)
        print(line_formatted)
    else:
        print("Invalid column_num")

    end = time.time()

    print("\nit took " + str(end - start) + " seconds")


test("./test/ESSAYSamples.jpg", 1)
