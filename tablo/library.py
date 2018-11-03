import os
import pickle

library_filename = 'tablo_library.p'

tablo_dir = os.path.join(os.path.expanduser('~'), '.tablo')
library_file_path = os.path.join(tablo_dir, library_filename)

def update_library(recordings):
    if not os.path.exists(tablo_dir):
        os.makedirs(tablo_dir)
    with open(library_file_path, 'wb') as library_file:
        pickle.dump(recordings, library_file)

def load_library(recordings):
    if os.path.exists(library_file_path):
        with open(library_file_path, 'rb') as library_file:
            recordings.update(pickle.load(library_file))
    else:
        print("Initializing tablo recordings library...")
