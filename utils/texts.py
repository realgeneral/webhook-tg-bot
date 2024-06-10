"""
    Source: https://github.com/cymon4380/numdeclination
"""
class Nominative(object):
    name = "именительный"
    singular = True

class Genitive(object):
    name = "родительный"
    singular = True

class Dative(object):
    name = "дательный"
    singular = True

class Accusative(object):
    name = "винительный"
    singular = True

class Instrumental(object):
    name = "творительный"
    singular = True

class Prepositional(object):
    name = "предложный"
    singular = True


class ConvertedNumber(object):
    number = 0
    case = None
    word = ''

class Pluralize:
    """ Числительные
    """
    @staticmethod
    def declinate(number, words: list, type: int = 1):
        if 0 >= type or type > 6:
            raise ValueError("Тип должен быть от 1 до 5.")

        if not isinstance(number, (int, float)) or isinstance(number, bool):
            raise ValueError('Указанное вами число не является int или float.')

        string = str(int(number))
        last_digits = string[-2:]

        cases_dict = {
            1: [Nominative, Genitive, Genitive],
            2: [Genitive, Genitive, Genitive],
            3: [Dative, Dative, Dative],
            4: [Instrumental, Instrumental, Instrumental],
            5: [Prepositional, Prepositional, Prepositional],
        }

        cases = cases_dict[type]
        case = ConvertedNumber()
        case.number = number
        if last_digits[0] == '1' and len(last_digits) == 2:
            case.word = words[2]
            case.case = cases_dict[type][2]
            case.case.singular = False
        else:
            if len(last_digits) == 1:
                ld = last_digits[0]
            else:
                ld = last_digits[1]
            if int(ld) == 1:
                case.word = words[0]
                case.case = cases_dict[type][0]
            elif int(ld) in [2, 3, 4]:
                case.word = words[1]
                case.case = cases_dict[type][1]
            else:
                case.word = words[2]
                case.case = cases_dict[type][2]
                case.case.singular = False

        return case

async def split_text(text, max_chars):
    """
    Разбивает текст на блоки и добавляет их в список.
    Каждый блок представляет собой кусок текста или
    полный блок markdown разметки.

    Parameters:
        text (str): Исходный текст.
        max_chars (int): Максимальное количество символов в блоке.

    Returns:
        list: Список блоков.
    """
    # Создаем пустой список для хранения блоков
    blocks = []

    # Разбиваем текст по каждому отдельному элементу markdown разметки
    # text_blocks = re.split(r'(\n\n|\n#{1,6}\s.*|^\*\s{1}.*|^\d+[\.\)]\s.*|`{3}.*`{3}|_{2}.*_{2}|\*{2}.*\*{2}|`{1}.*`{1}|\!\[.*\]\(.*\)|\[.*\]\(.*\))\n?', str(text))
    text_blocks = re.split(r'(\n\n|\n#{1,6}\s.*|^\*\s{1}.*|^\d+[\.\)]\s.*|`{3}.*`{3}|_{2}.*_{2}|\*{2}.*\*{2}|`{1}.*`{1}|\!\[.*\]\(.*\)|\[.*\]\(.*\))\n?', str(text))


    # Обрабатываем каждый блок
    for block in text_blocks:
        # Пропускаем пустые блоки
        if block == '':
            continue

        # Если блок содержит markdown с кодом, обрабатываем его
        if re.search(r'^`{3}.*`{3}', block):
            # Разбиваем блок с кодом на строки
            code_lines = block.splitlines()

            # Обрабатываем каждую строку
            for line in code_lines:
                # Добавляем строку, обернутую в кавычки, в список блоков
                blocks.append(f"{line}")
            continue

        # Если блок содержит markdown, проверяем его длину с учетом разметки
        if re.search(r'(\*\*|__|`)', block):
            while len(block) > max_chars:
                # Ищем ближайший символ разметки перед максимальным лимитом
                cutoff = re.search(r'\*\*|__|`|^\* |^\d+[\.\)] |^#{1,6}\s', block[:max_chars+1])
                if cutoff:
                    # Добавляем блок до разметки в список и обрезаем текущий блок
                    blocks.append(f"{block[:cutoff.start()]}{block[cutoff.start():cutoff.end()]}")
                    block = block[cutoff.end():]
                else:
                    # Если разметки в блоке не найдено, обрезаем по максимальной длине
                    blocks.append(block[:max_chars])
                    block = block[max_chars:]

            # Добавляем оставшуюся часть блока в список
            blocks.append(block)

        # Если блок не содержит markdown, просто разбиваем его по максимальной длине
        else:
            for i in range(0, len(block), max_chars):
                blocks.append(block[i:i+max_chars])

    return text_blocks
