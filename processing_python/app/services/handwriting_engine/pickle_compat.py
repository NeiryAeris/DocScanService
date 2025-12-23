# app/services/handwriting_engine/pickle_compat.py
import io
import pickle as _pickle
import pathlib


class Unpickler(_pickle.Unpickler):
    """Unpickler that remaps pathlib.PosixPath/WindowsPath to Pure* variants (cross-platform)."""
    def find_class(self, module, name):
        if module == "pathlib" and name == "PosixPath":
            return pathlib.PurePosixPath
        if module == "pathlib" and name == "WindowsPath":
            return pathlib.PureWindowsPath
        return super().find_class(module, name)


def load(file, **kwargs):
    return Unpickler(file, **kwargs).load()


def loads(s, **kwargs):
    return Unpickler(io.BytesIO(s), **kwargs).load()


# keep the rest of pickle API for torch
Pickler = _pickle.Pickler
dump = _pickle.dump
dumps = _pickle.dumps
