from loader import config

def openai_chatgpt_models():
    """ ГПТ-модели
    """
    models = config.get('openai', 'models').split(",")

    _ = {}
    for i in models:
        model = i.split(":")
        _[model[0]] = float(model[1])

    return _
