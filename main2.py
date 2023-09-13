from pdf2image import convert_from_path

# from PIL import Image
import pytesseract
# import spacy
# import cv2
import time


def pdf2jpg(image_url):
    pages = list()
    if not image_url.endswith('.pdf'):
        print("this is not a pdf file")
    else:
        pages = convert_from_path(image_url)

    return pages


def extract_data_from_image(image, confidence=-1):
    # text 정리하고, empty 데이터와 정확성 낮은 데이터 filtering 후 필요한 데이터 만 추출하기

    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    extracted_data = []
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if (data['conf'][i] > confidence) & (text != ''):
            extracted_data.append({
                "text": text,
                "x": data['left'][i],
                "y": data['top'][i],
                "width": data['width'][i],
                "height": data['height'][i],
                "line_num": data['line_num'][i],
                "block_num": data['block_num'][i],
                "par_num": data['par_num'][i],
            })
    return extracted_data


def calculate_spacing_height(extracted_data):  # spacing & word height 구하기

    max_height = max([word['height'] for word in extracted_data])

    total_gap = 0.0
    count = 0
    avg_gap = 1.25 * max_height

    for i, data in enumerate(extracted_data[:-1]):  # block_num 이 같지 않으면, 개행 됐을 수 있음
        if (data['block_num'] == extracted_data[i + 1]['block_num']) & \
                (data['par_num'] == extracted_data[i + 1]['par_num']) & \
                (data['line_num'] != extracted_data[i + 1]['line_num']):
            total_gap += extracted_data[i + 1]['y'] - data['y']
            count += 1

    if count != 0:
        avg_gap = round(total_gap / count, 2)

    return avg_gap, max_height


def data_to_text_json_1(words, width, height):  # 한 문단 기준 데이터 텍스트 형식화
    spacing, max_height = calculate_spacing_height(words)

    formatted_text = ""

    # set the left and right margin
    right_x = max([(word['x'] + word['width']) for word in words])
    left_x = min([word['x'] for word in words])

    # set the top and the top /bottom margin with the minimum y value
    top_y = min([word['y'] for word in words])
    bottom_y = height - top_y

    # 한 줄씩 나누기 위한 parameters
    line_formatted = []
    first_x = words[0]['x']
    first_y = words[0]['y']

    for idx, word in enumerate(words[:-1]):
        next_word = words[idx + 1]
        formatted_text += word['text'] + ' '  # 띄움이 확인 불가, spacing 1개로 가정

        # 블락이 다를 때 또는 같은데 paragraph 가 다를 경우 개행
        if (word['block_num'] != next_word['block_num']) \
                | ((word['block_num'] == next_word['block_num']) & (word['par_num'] != next_word['par_num'])):
            pass

        # 블락이 같고 paragraph 도 같은데, 라인이 다르면 뒤에 다음 단어 width 이상 남으면 개행
        elif (word['block_num'] == next_word['block_num']) & (word['par_num'] == next_word['par_num']) \
                & (word['line_num'] != next_word['line_num']) & \
                (right_x - word['x'] - word['width'] > next_word['width']):
            pass

        # 라인이 다른데 다음 줄이 알파벳 으로 시작 하지 않으면 개행
        elif (word['line_num'] != next_word['line_num']) & (not next_word['text'][0].isalpha()):
            pass
        else:
            continue

        gap = next_word['y'] - word['y']

        while gap > max_height:
            formatted_text += '\n'
            gap -= spacing
            if gap <= max_height:
                line_formatted.append({
                    'text': formatted_text,
                    'x': first_x,
                    'y': first_y,
                })
                first_word_x = next_word['x']
                first_word_y = next_word['y']
                # formatted_text = ''

    formatted_text += words[-1]['text']
    line_formatted.append({
        'text': formatted_text,
        'x': first_x,
        'y': first_y,
    })

    return formatted_text


def data_to_text_json_2(words, width, height):  # 개행 및 형식화
    spacing, avg_height = calculate_spacing_height(words)

    formatted_text = ""

    # 가상의 중간 선 보다 작은 것 중 max 는 1단의 right, 중간 선 보다 큰 것 중 max는 2단의 right
    middle_line_x = width / 2

    first_column_left_x = min([word['x'] for word in words])
    first_column_right_x = max(
        [(word['x'] + word['width']) for word in words if (word['x'] + word['width']) < middle_line_x])

    second_column_right_x = min(
        [(word['x'] + word['width']) for word in words if (word['x'] + word['width']) > middle_line_x])
    second_column_right_x = max([(word['x'] + word['width']) for word in words])

    top_y = min([word['y'] for word in words])
    bottom_y = height - top_y

    # 한 줄씩 나누기 위한 parameters
    line_formatted = []
    first_word_x = words[0]['x']
    first_word_y = words[0]['y']

    for idx, word in enumerate(words[:-1]):
        next_word = words[idx + 1]
        formatted_text += word['text'] + ' '  # 띄움이 확인 불가, spacing 1개로 가정

        # 페이지 중간의 값 보다 작으면 2단 페이지 에서 왼편, 크면 오른 편의 맥스 기준을 지정
        if word['x'] < middle_line_x:
            criteria = first_column_right_x
        else:
            criteria = second_column_right_x

        # 블락이 다를 때 또는 같은데 paragraph 가 다를 경우 개행
        if (word['block_num'] != next_word['block_num']) \
                | ((word['block_num'] == next_word['block_num']) & (word['par_num'] != next_word['par_num'])):
            pass

        # 블락이 같고 paragraph 도 같은데, 라인이 다르면 뒤에 다음 단어 이상 남으면 개행
        elif (word['block_num'] == next_word['block_num']) & (word['par_num'] == next_word['par_num']) \
                & (word['line_num'] != next_word['line_num']) \
                & (criteria - (word['x'] + word['width']) > next_word['width']):
            pass

        # 라인이 다른데 다음 줄이 알파벳 으로 시작 하지 않으면 개행
        elif (word['line_num'] != next_word['line_num']) & (not next_word['text'][0].isalpha()) \
                & ((word['par_num'] != next_word['par_num']) | (word['block_num'] != next_word['block_num'])):
            pass
        else:
            continue

        # the gap between the current word and the next word but if the current word is the last word on the
        # first column, the gap will be from the word to the bottom + top to the next word
        gap = next_word['y'] - word['y']
        if word['y'] > next_word['y'] | ((word['x'] < middle_line_x) & (next_word['x'] > middle_line_x)):
            gap = bottom_y - word['y'] + next_word['y'] - top_y

        # add \n until the gap gets less than average height of words
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

    # 마지막 단어 추가
    formatted_text += words[-1]['text']
    line_formatted.append({
        'text': formatted_text,
        'x': first_word_x,
        'y': first_word_y,
    })

    return formatted_text


def test(url, column_num):
    start = time.time()

    images = pdf2jpg(url)

    # column 1 일때와, 2일때, 돌리는 function 정해주기
    column_functions = {
        1: data_to_text_json_1,
        2: data_to_text_json_2,
    }

    # 일단 1,2 column 만 그 외는 Invalid
    if column_num in column_functions:
        selected_function = column_functions[column_num]
        for i, image in enumerate(images):
            width, height = image.size
            extracted_data = extract_data_from_image(image, 25)
            line_formatted = selected_function(extracted_data, width, height)

            # 여기서 워드로 변환하는 코드가 필요하다
            print(line_formatted)
    else:
        print("Invalid column_num")

    end = time.time()

    print("\nit took " + str(end - start) + " seconds")


test("./test/Meeting Minute3.pdf", 2)
