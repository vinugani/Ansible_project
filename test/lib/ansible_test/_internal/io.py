"""Functions for disk IO."""
from __future__ import annotations

import errno
import io
import json
import os
import typing as t

from .encoding import (
    ENCODING,
    to_bytes,
    to_text,
)


def read_json_file(path):  # type: (t.AnyStr) -> t.Any
    """Parse and return the json content from the specified path."""
    return json.loads(read_text_file(path))


def read_text_file(path):  # type: (t.AnyStr) -> t.Text
    """Return the contents of the specified path as text."""
    return to_text(read_binary_file(path))


def read_binary_file(path):  # type: (t.AnyStr) -> bytes
    """Return the contents of the specified path as bytes."""
    with open_binary_file(path) as file_obj:
        return file_obj.read()


def make_dirs(path):  # type: (str) -> None
    """Create a directory at path, including any necessary parent directories."""
    try:
        os.makedirs(to_bytes(path))
    except OSError as ex:
        if ex.errno != errno.EEXIST:
            raise


def write_json_file(path,  # type: str
                    content,  # type: t.Any
                    create_directories=False,  # type: bool
                    formatted=True,  # type: bool
                    encoder=None,  # type: t.Optional[t.Callable[[t.Any], t.Any]]
                    ):  # type: (...) -> str
    """Write the given json content to the specified path, optionally creating missing directories."""
    text_content = json.dumps(content,
                              sort_keys=formatted,
                              indent=4 if formatted else None,
                              separators=(', ', ': ') if formatted else (',', ':'),
                              cls=encoder,
                              ) + '\n'

    write_text_file(path, text_content, create_directories=create_directories)

    return text_content


def write_text_file(path, content, create_directories=False):  # type: (str, str, bool) -> None
    """Write the given text content to the specified path, optionally creating missing directories."""
    if create_directories:
        make_dirs(os.path.dirname(path))

    with open_binary_file(path, 'wb') as file_obj:
        file_obj.write(to_bytes(content))


def open_text_file(path, mode='r'):  # type: (str, str) -> t.TextIO
    """Open the given path for text access."""
    if 'b' in mode:
        raise Exception('mode cannot include "b" for text files: %s' % mode)

    # noinspection PyTypeChecker
    return io.open(to_bytes(path), mode, encoding=ENCODING)  # pylint: disable=consider-using-with


def open_binary_file(path, mode='rb'):  # type: (str, str) -> t.BinaryIO
    """Open the given path for binary access."""
    if 'b' not in mode:
        raise Exception('mode must include "b" for binary files: %s' % mode)

    # noinspection PyTypeChecker
    return io.open(to_bytes(path), mode)  # pylint: disable=consider-using-with


class SortedSetEncoder(json.JSONEncoder):
    """Encode sets as sorted lists."""
    def default(self, o):
        """Return a serialized version of the `o` object."""
        if isinstance(o, set):
            return sorted(o)

        return json.JSONEncoder.default(self, o)
