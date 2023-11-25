import importlib
import os


def import_all_modules():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    for filename in os.listdir(current_dir):
        if filename.endswith('.py') and filename != '__main__.py':
            module_name = filename[:-3]  # Remove the ".py" extension
            importlib.import_module(module_name)


if __name__ == '__main__':
    import_all_modules()
