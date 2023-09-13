# LineFormattedData
# with TextInImages.py:

from pdf2image import convert_from_path
import pytesseract
import time
import TextInImages
import numpy as np

# 받는 값 image list 와 column num
# parameters = image list
# column num


class LineFormattedData:
    def __init__(self, image, column_num):
        self.image = image
        self.column_num = column_num
        self.line_formatted_data = self.process_pdf(
            self.image, self.column_num)

    def process_pdf(self, image, column_num):

        extracted_data = self.extract_data_from_image(image, 10)
        width, height = image.size

        if self.column_num == 1:
            line_formatted = self.data_to_text_json_1(extracted_data, height)
        elif self.column_num == 2:
            line_formatted = self.data_to_text_json_2(extracted_data, width, height)
        else:
            print("Invalid column_num")

        return line_formatted

    def extract_data_from_image(self, image, confidence=-1):
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

    def calculate_spacing_height(self, extracted_data):
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

    def data_to_text_json_1(self, words, width, height):
        spacing, max_height = self.calculate_spacing_height(words)

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
                    formatted_text = ''

        formatted_text += words[-1]['text']
        line_formatted.append({
            'text': formatted_text,
            'x': first_x,
            'y': first_y,
        })

        return line_formatted

    def data_to_text_json_2(self, words, width, height):
        spacing, avg_height = self.calculate_spacing_height(words)

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
                    formatted_text = ''

        # 마지막 단어 추가
        formatted_text += words[-1]['text']
        line_formatted.append({
            'text': formatted_text,
            'x': first_word_x,
            'y': first_word_y,
        })

        return line_formatted


