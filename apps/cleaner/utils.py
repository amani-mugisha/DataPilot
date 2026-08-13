import os


def get_uploaded_filename(uploaded_file):
    return os.path.basename(uploaded_file.name)


def is_csv(filename):
    return filename.lower().endswith(".csv")