import os


# TODO return human readable in mb
def size(file_path):
    try:
        file_size = os.path.getsize(file_path)
    except FileNotFoundError:
        file_size = 0
    finally:
        return file_size
