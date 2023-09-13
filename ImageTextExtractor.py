


class Image:
    def __init__(self, column_num):

        self.column_num = column_num
        self.images = self.pdf2jpg()
