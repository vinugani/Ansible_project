# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""An implementation of RFC4013 SASLprep.
This code is mostly (apart from utils methods) a copy of
https://github.com/mongodb/mongo-python-driver/blob/master/pymongo/saslprep.py

Contributors: Andrey Tuzhilin <andrei.tuzhilin@gmail.com>
"""

import sys
from ansible.module_utils.six import text_type
from ansible.module_utils._text import to_text


class NoStringPrepError(Exception):
    """Local python installation does not have a stringprep module"""
    pass


try:
    import stringprep
except ImportError:
    HAVE_STRINGPREP = False

    def saslprep(data):
        """SASLprep dummy"""
        data = to_text(data)
        if isinstance(data, text_type):
            raise NoStringPrepError("The stringprep module is not available.")
        return data
else:
    HAVE_STRINGPREP = True
    import unicodedata
    # RFC4013 section 2.3 prohibited output.
    _PROHIBITED = (
        # A strict reading of RFC 4013 requires table c12 here, but
        # characters from it are mapped to SPACE in the Map step. Can
        # normalization reintroduce them somehow?
        stringprep.in_table_c12,
        stringprep.in_table_c21_c22,
        stringprep.in_table_c3,
        stringprep.in_table_c4,
        stringprep.in_table_c5,
        stringprep.in_table_c6,
        stringprep.in_table_c7,
        stringprep.in_table_c8,
        stringprep.in_table_c9)

    def saslprep(data, prohibit_unassigned_code_points=True):
        """An implementation of RFC4013 SASLprep.
        :Parameters:
          - `data`: The string to SASLprep. Unicode strings
            (python 2.x unicode, 3.x str) are supported. Byte strings
            (python 2.x str, 3.x bytes) are ignored.
          - `prohibit_unassigned_code_points`: True / False. RFC 3454
            and RFCs for various SASL mechanisms distinguish between
            `queries` (unassigned code points allowed) and
            `stored strings` (unassigned code points prohibited). Defaults
            to ``True`` (unassigned code points are prohibited).
        :Returns:
        The SASLprep'ed version of `data`.
        """
        data = to_text(data)
        if not isinstance(data, text_type):
            return data

        if prohibit_unassigned_code_points:
            prohibited = _PROHIBITED + (stringprep.in_table_a1,)
        else:
            prohibited = _PROHIBITED

        # RFC3454 section 2, step 1 - Map
        # RFC4013 section 2.1 mappings
        # Map Non-ASCII space characters to SPACE (U+0020). Map
        # commonly mapped to nothing characters to, well, nothing.
        in_table_c12 = stringprep.in_table_c12
        in_table_b1 = stringprep.in_table_b1
        data = u"".join(
            [u"\u0020" if in_table_c12(elt) else elt
             for elt in data if not in_table_b1(elt)])

        # RFC3454 section 2, step 2 - Normalize
        # RFC4013 section 2.2 normalization
        data = unicodedata.ucd_3_2_0.normalize('NFKC', data)

        in_table_d1 = stringprep.in_table_d1
        if in_table_d1(data[0]):
            if not in_table_d1(data[-1]):
                # RFC3454, Section 6, #3. If a string contains any
                # RandALCat character, the first and last characters
                # MUST be RandALCat characters.
                raise ValueError("SASLprep: failed bidirectional check")
            # RFC3454, Section 6, #2. If a string contains any RandALCat
            # character, it MUST NOT contain any LCat character.
            prohibited = prohibited + (stringprep.in_table_d2,)
        else:
            # RFC3454, Section 6, #3. Following the logic of #3, if
            # the first character is not a RandALCat, no other character
            # can be either.
            prohibited = prohibited + (in_table_d1,)

        # RFC3454 section 2, step 3 and 4 - Prohibit and check bidi
        for char in data:
            if any(in_table(char) for in_table in prohibited):
                raise ValueError("SASLprep: failed prohibited character check")

        return data
