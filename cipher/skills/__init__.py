import importlib
import pkgutil

TOOLS = {}


def skill(name, description, properties=None, required=None):
    def wrap(func):
        TOOLS[name] = {
            "func": func,
            "schema": {
                "name": name,
                "description": description,
                "input_schema": {
                    "type": "object",
                    "properties": properties or {},
                    "required": required or [],
                },
            },
        }
        return func
    return wrap


def load_all():
    for m in pkgutil.iter_modules(__path__):
        importlib.import_module(f"{__name__}.{m.name}")
