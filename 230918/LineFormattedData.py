# LineFormattedData
# with PagesInFile.py:

import pytesseract

# 받는 값 image list 와 column num
# parameters = image list
# column num


class LineFormattedData:
    def __init__(self, image, column_num):
        self.image = image
        self.column_num = column_num
        self.line_formatted_data = self.process_pdf(
            self.image)

    def process_pdf(self, image):

        extracted_data = self.extract_data_from_image(image, 10)

        self.width, self.height = image.size

        if self.column_num == 1:
            line_formatted = self.data_to_text_json_1(extracted_data, self.height)
        elif self.column_num == 2:
            line_formatted = self.data_to_text_json_2(extracted_data, self.width, self.height)
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

    def data_to_text_json_1(self, words, height):
        spacing, max_height = self.calculate_spacing_height(words)

        formatted_text = ""

        self.left_x = min([word['x'] for word in words])
        self.right_x = max([(word['x'] + word['width']) for word in words])

        self.top_y = min([word['y'] for word in words])
        self.bottom_y = self.height - self.top_y

        # 한 줄씩 나누기 위한 parameters
        line_formatted = []
        first_x = words[0]['x']
        first_y = words[0]['y']

        for idx, word in enumerate(words[:-1]):
            if (word['text'] != '-') & (word['text'][-1] == '-'):
                word['text'] = word['text'][:-1]
            next_word = words[idx + 1]
            formatted_text += word['text'] + ' '

            # 블락이 다를 때 또는 같은데 paragraph 가 다를 경우 개행
            if (word['block_num'] != next_word['block_num']) \
                    | ((word['block_num'] == next_word['block_num']) & (word['par_num'] != next_word['par_num'])):
                pass

            # 블락이 같고 paragraph 도 같은데, 라인이 다르면 뒤에 다음 단어 width 이상 남으면 개행
            elif (word['block_num'] == next_word['block_num']) & (word['par_num'] == next_word['par_num']) \
                    & (word['line_num'] != next_word['line_num']) & \
                    (self.right_x - word['x'] - word['width'] > next_word['width']):
                pass

            # 라인이 다른데 다음 줄이 알파벳 으로 시작 하지 않으면 개행
            elif (word['line_num'] != next_word['line_num']) & (not next_word['text'][0].isalpha()):
                pass
            else:
                continue

            gap = next_word['y'] - word['y'] - spacing

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

        middle_line_x = width / 2

        self.first_column_left_x = min([word['x'] for word in words])
        self.first_column_right_x = max(
            [(word['x'] + word['width']) for word in words if (word['x'] + word['width']) < middle_line_x])

        self.second_column_left_x = min(
            [(word['x'] + word['width']) for word in words if (word['x'] + word['width']) > middle_line_x])
        self.second_column_right_x = max([(word['x'] + word['width']) for word in words])

        self.top_y = min([word['y'] for word in words])
        self.bottom_y = max([word['y'] for word in words]) + spacing

        # 한 줄씩 나누기 위한 parameters
        line_formatted = []
        first_word_x = words[0]['x']
        first_word_y = words[0]['y']
        line_formatted.append({'text': '\n' * int((first_word_y-self.top_y)//spacing),
                        'x': 0,
                        'y': 0,})
        first_right_word = True
        for idx, word in enumerate(words[:-1]):
            if (word['text'] != '-') & (word['text'][-1] == '-'):
                word['text'] = word['text'][:-1]
            next_word = words[idx + 1]
            formatted_text += word['text'] + ' '

            if word['x'] < middle_line_x:
                criteria = self.first_column_right_x
            else:
                criteria = self.second_column_right_x
                if first_right_word == True:
                    first_right_word = False
                    next_line_num = '\n' * int((word['y']-self.top_y) // spacing)
                    formatted_text = next_line_num + formatted_text

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

            gap = next_word['y'] - word['y'] - spacing
            if word['y'] > next_word['y'] | ((word['x'] < middle_line_x) & (next_word['x'] > middle_line_x)):
                gap = self.bottom_y - word['y'] + next_word['y'] - self.top_y - spacing

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



