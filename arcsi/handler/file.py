import os


from mutagen.id3 import ID3, ID3NoHeaderError, APIC, TIT2, TPE1
from mutagen.mp3 import MP3
from PIL import Image
from slugify import slugify
from werkzeug.utils import safe_join


CONNECTER = "-"
DELIMITER = "-"
DOT = "."


def normalise(namestring):
    slugged = slugify(namestring)
    norms = slugged.replace(DELIMITER, CONNECTER)
    return norms


def slug(namestring):
    slugs = slugify(namestring)
    return slugs


def get_extension(base_name):
    return base_name.rsplit(DOT, 1)[1].lower()


def local_save(file, path):
    file.save(path)
    return path


# TODO return human readable in mb
# Only works after succ upload and file found present in local storage
def size(file_path):
    try:
        file_size = os.path.getsize(file_path)
    except FileNotFoundError:
        file_size = 0
    finally:
        return file_size


def tidy_name(ext, group_name, element_name):
    norms_group = normalise(group_name)
    norms_elem = normalise(element_name)
    norms_names = [norms_group, norms_elem]
    return "{}{}{}".format(DELIMITER.join(norms_names), DOT, ext)


def path(group_name, number, element_name):
    try:
        os.makedirs(
            "{}/{}/{}".format(
                os.path.relpath("arcsi/static/upload/"), group_name, number
            )
        )
    #        os.makedirs("{}/{}/{}".format(app.config["UPLOAD_FOLDER"], group_name, number))
    except FileExistsError as err:
        pass
    file_path = safe_join(
        os.path.relpath("arcsi/static/upload/"), group_name, number, element_name
    )
    return file_path


def get_audio_length(file_path):
    item_audio_obj = MP3(file_path)
    # return item_audio_obj.filename
    item_length = item_audio_obj.info.length
    return str(item_length)


def get_image_dimension(file_path):
    img = Image.open(file_path)

    return "{}x{}".format(img.size[0], img.size[1])


def is_image(ext):
    return True if ext in ["jpg", "jpeg", "png", "gif"] else False


def is_audio(ext):
    return True if ext in ["mp3"] else False


class StoredFile:
    def __init__(self):
        pass
