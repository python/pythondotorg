registry = []


def register_function(func):
    registry.append(func)
    return func
