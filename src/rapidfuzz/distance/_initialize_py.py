# SPDX-License-Identifier: MIT
# Copyright (C) 2022 Max Bachmann

from __future__ import annotations


def _list_to_editops(ops, src_len: int, dest_len: int):
    if not ops:
        return []

    if len(ops[0]) == 5:
        return Opcodes(ops, src_len, dest_len).as_editops()._editops

    blocks = []
    for op in ops:
        edit_type, src_pos, dest_pos = op

        if src_pos > src_len or dest_pos > dest_len:
            raise ValueError("List of edit operations invalid")

        if src_pos == src_len and edit_type != "insert":
            raise ValueError("List of edit operations invalid")
        elif dest_pos == dest_len and edit_type != "delete":
            raise ValueError("List of edit operations invalid")

        # keep operations are not relevant in editops
        if edit_type == "equal":
            continue

        blocks.append(Editop(edit_type, src_pos, dest_pos))

    # validate order of editops
    for i in range(0, len(blocks) - 1):
        if (
            blocks[i + 1].src_pos < blocks[i].src_pos
            or blocks[i + 1].dest_pos < blocks[i].dest_pos
        ):
            raise ValueError("List of edit operations out of order")
        if (
            blocks[i + 1].src_pos == blocks[i].src_pos
            and blocks[i + 1].dest_pos == blocks[i].dest_pos
        ):
            raise ValueError("Duplicated edit operation")

    return blocks


def _list_to_opcodes(ops, src_len: int, dest_len: int):
    if not ops or len(ops[0]) == 3:
        return Editops(ops, src_len, dest_len).as_opcodes()._opcodes

    blocks = []
    for op in ops:
        edit_type, src_start, src_end, dest_start, dest_end = op

        if src_end > src_len or dest_end > dest_len:
            raise ValueError("List of edit operations invalid")
        elif src_end < src_start or dest_end < dest_start:
            raise ValueError("List of edit operations invalid")

        if edit_type == "equal" or edit_type == "replace":
            if src_end - src_start != dest_end - dest_start or src_start == src_end:
                raise ValueError("List of edit operations invalid")
        if edit_type == "insert":
            if src_start != src_end or dest_start == dest_end:
                raise ValueError("List of edit operations invalid")
        elif edit_type == "delete":
            if src_start == src_end or dest_start != dest_end:
                raise ValueError("List of edit operations invalid")

        # merge similar adjacent blocks
        if blocks:
            if (
                blocks[-1].tag == edit_type
                and blocks[-1].src_end == src_start
                and blocks[-1].dest_end == dest_start
            ):
                blocks[-1].src_end = src_end
                blocks[-1].dest_end = dest_end
                continue

        blocks.append(Opcode(edit_type, src_start, src_end, dest_start, dest_end))

    # check if edit operations span the complete string
    if blocks[0].src_start != 0 or blocks[0].dest_start != 0:
        raise ValueError("List of edit operations does not start at position 0")
    if blocks[-1].src_end != src_len or blocks[-1].dest_end != dest_len:
        raise ValueError("List of edit operations does not end at the string ends")
    for i in range(0, len(blocks) - 1):
        if (
            blocks[i + 1].src_start != blocks[i].src_end
            or blocks[i + 1].dest_start != blocks[i].dest_end
        ):
            raise ValueError("List of edit operations is not continuous")

    return blocks


class MatchingBlock:
    def __init__(self, a, b, size):
        self.a = a
        self.b = b
        self.size = size

    def __len__(self):
        return 3

    def __eq__(self, other):
        if len(other) != 3:
            return False

        return other[0] == self.a and other[1] == self.b and other[2] == self.size

    def __getitem__(self, i):
        if i == 0 or i == -3:
            return self.a
        if i == 1 or i == -2:
            return self.b
        if i == 2 or i == -1:
            return self.size

        raise IndexError("MatchingBlock index out of range")

    def __repr__(self):
        return f"MatchingBlock(a={self.a}, b={self.b}, size={self.size})"


class Editop:
    """
    Tuple like object describing an edit operation.
    It is in the form (tag, src_pos, dest_pos)

    The tags are strings, with these meanings:

    +-----------+---------------------------------------------------+
    | tag       | explanation                                       |
    +===========+===================================================+
    | 'replace' | src[src_pos] should be replaced by dest[dest_pos] |
    +-----------+---------------------------------------------------+
    | 'delete'  | src[src_pos] should be deleted                    |
    +-----------+---------------------------------------------------+
    | 'insert'  | dest[dest_pos] should be inserted at src[src_pos] |
    +-----------+---------------------------------------------------+
    """

    def __init__(self, tag, src_pos, dest_pos):
        self.tag = tag
        self.src_pos = src_pos
        self.dest_pos = dest_pos

    def __len__(self):
        return 3

    def __eq__(self, other):
        if len(other) != 3:
            return False

        return (
            other[0] == self.tag
            and other[1] == self.src_pos
            and other[2] == self.dest_pos
        )

    def __getitem__(self, i):
        if i == 0 or i == -3:
            return self.tag
        if i == 1 or i == -2:
            return self.src_pos
        if i == 2 or i == -1:
            return self.dest_pos

        raise IndexError("Editop index out of range")

    def __repr__(self):
        return (
            f"Editop(tag={self.tag}, src_pos={self.src_pos}, dest_pos={self.dest_pos})"
        )


class Editops:
    """
    List like object of Editos describing how to turn s1 into s2.
    """

    def __init__(self, editops=None, src_len: int = 0, dest_len: int = 0):
        self._src_len: int = src_len
        self._dest_len: int = dest_len
        self._editops = _list_to_editops(editops, src_len, dest_len)

    @classmethod
    def from_opcodes(cls, opcodes: Opcodes) -> Editops:
        """
        Create Editops from Opcodes

        Parameters
        ----------
        opcodes : Opcodes
            opcodes to convert to editops

        Returns
        -------
        editops : Editops
            Opcodes converted to Editops
        """
        return opcodes.as_editops()

    def as_opcodes(self) -> Opcodes:
        """
        Convert to Opcodes

        Returns
        -------
        opcodes : Opcodes
            Editops converted to Opcodes
        """
        x = Opcodes.__new__(Opcodes)
        x._src_len = self._src_len
        x._dest_len = self._dest_len
        blocks = []
        src_pos = 0
        dest_pos = 0
        i = 0
        while i < len(self._editops):
            if (
                src_pos < self._editops[i].src_pos
                or dest_pos < self._editops[i].dest_pos
            ):
                blocks.append(
                    Opcode(
                        "equal",
                        src_pos,
                        self._editops[i].src_pos,
                        dest_pos,
                        self._editops[i].dest_pos,
                    )
                )
                src_pos = self._editops[i].src_pos
                dest_pos = self._editops[i].dest_pos

            src_begin = src_pos
            dest_begin = dest_pos
            type = self._editops[i].tag
            while (
                i < len(self._editops)
                and self._editops[i].tag == type
                and src_pos == self._editops[i].src_pos
                and dest_pos == self._editops[i].dest_pos
            ):
                if type == "replace":
                    src_pos += 1
                    dest_pos += 1
                elif type == "insert":
                    dest_pos += 1
                elif type == "delete":
                    src_pos += 1

                i += 1

            blocks.append(Opcode(type, src_begin, src_pos, dest_begin, dest_pos))

        if src_pos < self.src_len or dest_pos < self.dest_len:
            blocks.append(
                Opcode("equal", src_pos, self.src_len, dest_pos, self.dest_len)
            )

        x._opcodes = blocks
        return x

    def as_matching_blocks(self) -> list[MatchingBlock]:
        blocks = []
        src_pos = 0
        dest_pos = 0
        for op in self:
            if src_pos < op.src_pos or dest_pos < op.dest_pos:
                length = min(op.src_pos - src_pos, op.dest_pos - dest_pos)
                if length > 0:
                    blocks.append(MatchingBlock(src_pos, dest_pos, length))
                src_pos = op.src_pos
                dest_pos = op.dest_pos

            if op.tag == "replace":
                src_pos += 1
                dest_pos += 1
            elif op.tag == "delete":
                src_pos += 1
            elif op.tag == "insert":
                dest_pos += 1

        if src_pos < self.src_len or dest_pos < self.dest_len:
            length = min(self.src_len - src_pos, self.dest_len - dest_pos)
            if length > 0:
                blocks.append(MatchingBlock(src_pos, dest_pos, length))

        blocks.append(MatchingBlock(self.src_len, self.dest_len, 0))
        return blocks

    def as_list(self) -> list[Editop]:
        """
        Convert Editops to a list of tuples.

        This is the equivalent of ``[x for x in editops]``
        """
        return self._editops

    def copy(self) -> Editops:
        """
        performs copy of Editops
        """
        x = Editops.__new__(Editops)
        x._src_len = self._src_len
        x._dest_len = self._dest_len
        x._editops = self._editops[::]
        return x

    def inverse(self):
        """
        Invert Editops, so it describes how to transform the destination string to
        the source string.

        Returns
        -------
        editops : Editops
            inverted Editops

        Examples
        --------
        >>> from rapidfuzz.distance import Levenshtein
        >>> Levenshtein.editops('spam', 'park')
        [Editop(tag=delete, src_pos=0, dest_pos=0),
         Editop(tag=replace, src_pos=3, dest_pos=2),
         Editop(tag=insert, src_pos=4, dest_pos=3)]

        >>> Levenshtein.editops('spam', 'park').inverse()
        [Editop(tag=insert, src_pos=0, dest_pos=0),
         Editop(tag=replace, src_pos=2, dest_pos=3),
         Editop(tag=delete, src_pos=3, dest_pos=4)]
        """
        blocks = []
        for tag, src_pos, dest_pos in self:
            if tag == "delete":
                tag = "insert"
            elif tag == "insert":
                tag = "delete"

            blocks.append(Editop(tag, dest_pos, src_pos))

        x = Editops.__new__(Editops)
        x._src_len = self.dest_len
        x._dest_len = self.src_len
        x._editops = blocks
        return x

    def remove_subsequence(self, subsequence: Editops):
        raise NotImplementedError

    def apply(self, source_string, destination_string):
        raise NotImplementedError

    @property
    def src_len(self) -> int:
        return self._src_len

    @src_len.setter
    def src_len(self, value: int):
        self._src_len = value

    @property
    def dest_len(self) -> int:
        return self._dest_len

    @dest_len.setter
    def dest_len(self, value: int):
        self._dest_len = value

    def __eq__(self, other: Editops) -> bool:
        if not isinstance(other, Editops):
            return False

        return (
            self.dest_len == other.dest_len
            and self.src_len == other.src_len
            and self._editops == other._editops
        )

    def __len__(self):
        return len(self._editops)

    def __delitem__(self, key) -> None:
        del self._editops[key]

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._editops[key]

        start, stop, step = key.indices(len(self._editops))
        if step < 0:
            raise ValueError("step sizes below 0 lead to an invalid order of editops")

        x = Editops.__new__(Editops)
        x._src_len = self._src_len
        x._dest_len = self._dest_len
        x._editops = self._editops[start:stop:step]
        return x

    def __repr__(self):
        return (
            "Editops(["
            + ", ".join(repr(op) for op in self)
            + f"], src_len={self.src_len}, dest_len={self.dest_len})"
        )


class Opcode:
    """
    Tuple like object describing an edit operation.
    It is in the form (tag, src_start, src_end, dest_start, dest_end)

    The tags are strings, with these meanings:

    +-----------+-----------------------------------------------------+
    | tag       | explanation                                         |
    +===========+=====================================================+
    | 'replace' | src[src_start:src_end] should be                    |
    |           | replaced by dest[dest_start:dest_end]               |
    +-----------+-----------------------------------------------------+
    | 'delete'  | src[src_start:src_end] should be deleted.           |
    |           | Note that dest_start==dest_end in this case.        |
    +-----------+-----------------------------------------------------+
    | 'insert'  | dest[dest_start:dest_end] should be inserted        |
    |           | at src[src_start:src_start].                        |
    |           | Note that src_start==src_end in this case.          |
    +-----------+-----------------------------------------------------+
    | 'equal'   | src[src_start:src_end] == dest[dest_start:dest_end] |
    +-----------+-----------------------------------------------------+

    Note
    ----
    Opcode is compatible with the tuples returned by difflib's SequenceMatcher to make them
    interoperable
    """

    def __init__(
        self, tag: str, src_start: int, src_end: int, dest_start: int, dest_end: int
    ):
        self.tag: str = tag
        self.src_start: int = src_start
        self.src_end: int = src_end
        self.dest_start: int = dest_start
        self.dest_end: int = dest_end

    def __len__(self) -> int:
        return 5

    def __eq__(self, other) -> bool:
        if len(other) != 5:
            return False

        return (
            other[0] == self.tag
            and other[1] == self.src_start
            and other[2] == self.src_end
            and other[3] == self.dest_start
            and other[4] == self.dest_end
        )

    def __getitem__(self, i):
        if i == 0 or i == -5:
            return self.tag
        if i == 1 or i == -4:
            return self.src_start
        if i == 2 or i == -3:
            return self.src_end
        if i == 3 or i == -2:
            return self.dest_start
        if i == 4 or i == -1:
            return self.dest_end

        raise IndexError("Opcode index out of range")

    def __repr__(self) -> str:
        return f"Opcode(tag={self.tag}, src_start={self.src_start}, src_end={self.src_end}, dest_start={self.dest_start}, dest_end={self.dest_end})"


class Opcodes:
    """
    List like object of Opcodes describing how to turn s1 into s2.
    The first Opcode has src_start == dest_start == 0, and remaining tuples
    have src_start == the src_end from the tuple preceding it,
    and likewise for dest_start == the previous dest_end.
    """

    def __init__(self, opcodes=None, src_len=0, dest_len=0):
        self._src_len: int = src_len
        self._dest_len: int = dest_len
        self._opcodes = _list_to_opcodes(opcodes, src_len, dest_len)

    @classmethod
    def from_editops(cls, editops: Editops) -> Opcodes:
        """
        Create Opcodes from Editops

        Parameters
        ----------
        editops : Editops
            editops to convert to opcodes

        Returns
        -------
        opcodes : Opcodes
            Editops converted to Opcodes
        """
        return editops.as_opcodes()

    def as_editops(self) -> Editops:
        """
        Convert Opcodes to Editops

        Returns
        -------
        editops : Editops
            Opcodes converted to Editops
        """
        x = Editops.__new__(Editops)
        x._src_len = self._src_len
        x._dest_len = self._dest_len
        blocks = []
        for op in self:
            if op.tag == "replace":
                for j in range(op.src_end - op.src_start):
                    blocks.append(
                        Editop("replace", op.src_start + j, op.dest_start + j)
                    )
            elif op.tag == "insert":
                for j in range(op.dest_end - op.dest_start):
                    blocks.append(Editop("insert", op.src_start, op.dest_start + j))
            elif op.tag == "delete":
                for j in range(op.src_end - op.src_start):
                    blocks.append(Editop("delete", op.src_start + j, op.dest_start))

        x._editops = blocks
        return x

    def as_matching_blocks(self) -> list[MatchingBlock]:
        blocks = []
        for op in self:
            if op.tag == "equal":
                length = min(op.src_end - op.src_start, op.dest_end - op.dest_start)
                if length > 0:
                    blocks.append(MatchingBlock(op.src_start, op.dest_start, length))

        blocks.append(MatchingBlock(self.src_len, self.dest_len, 0))
        return blocks

    def as_list(self) -> list[Opcode]:
        """
        Convert Opcodes to a list of tuples, which is compatible
        with the opcodes of difflibs SequenceMatcher.

        This is the equivalent of ``[x for x in opcodes]``
        """
        return self._opcodes[::]

    def copy(self) -> Opcodes:
        """
        performs copy of Opcodes
        """
        x = Opcodes.__new__(Opcodes)
        x._src_len = self._src_len
        x._dest_len = self._dest_len
        x._opcodes = self._opcodes[::]
        return x

    def inverse(self):
        """
        Invert Opcodes, so it describes how to transform the destination string to
        the source string.

        Returns
        -------
        opcodes : Opcodes
            inverted Opcodes

        Examples
        --------
        >>> from rapidfuzz.distance import Levenshtein
        >>> Levenshtein.opcodes('spam', 'park')
        [Opcode(tag=delete, src_start=0, src_end=1, dest_start=0, dest_end=0),
         Opcode(tag=equal, src_start=1, src_end=3, dest_start=0, dest_end=2),
         Opcode(tag=replace, src_start=3, src_end=4, dest_start=2, dest_end=3),
         Opcode(tag=insert, src_start=4, src_end=4, dest_start=3, dest_end=4)]

        >>> Levenshtein.opcodes('spam', 'park').inverse()
        [Opcode(tag=insert, src_start=0, src_end=0, dest_start=0, dest_end=1),
         Opcode(tag=equal, src_start=0, src_end=2, dest_start=1, dest_end=3),
         Opcode(tag=replace, src_start=2, src_end=3, dest_start=3, dest_end=4),
         Opcode(tag=delete, src_start=3, src_end=4, dest_start=4, dest_end=4)]
        """
        blocks = []
        for tag, src_start, src_end, dest_start, dest_end in self:
            if tag == "delete":
                tag = "insert"
            elif tag == "insert":
                tag = "delete"

            blocks.append(Opcode(tag, dest_start, dest_end, src_start, src_end))

        x = Opcodes.__new__(Opcodes)
        x._src_len = self.dest_len
        x._dest_len = self.src_len
        x._opcodes = blocks
        return x

    def apply(self, source_string, destination_string):
        raise NotImplementedError

    @property
    def src_len(self) -> int:
        return self._src_len

    @src_len.setter
    def src_len(self, value: int):
        self._src_len = value

    @property
    def dest_len(self) -> int:
        return self._dest_len

    @dest_len.setter
    def dest_len(self, value: int):
        self._dest_len = value

    def __eq__(self, other: Opcodes) -> bool:
        if not isinstance(other, Opcodes):
            return False

        return (
            self.dest_len == other.dest_len
            and self.src_len == other.src_len
            and self._opcodes == other._opcodes
        )

    def __len__(self):
        return len(self._opcodes)

    def __getitem__(self, key: int) -> Opcode:
        if isinstance(key, int):
            return self._opcodes[key]
        else:
            raise TypeError("Expected index")

    def __repr__(self):
        return (
            "Opcodes(["
            + ", ".join(repr(op) for op in self)
            + f"], src_len={self.src_len}, dest_len={self.dest_len})"
        )


class ScoreAlignment:
    """
    Tuple like object describing the position of the compared strings in
    src and dest.

    It indicates that the score has been calculated between
    src[src_start:src_end] and dest[dest_start:dest_end]
    """

    def __init__(self, score, src_start, src_end, dest_start, dest_end):
        self.score = score
        self.src_start = src_start
        self.src_end = src_end
        self.dest_start = dest_start
        self.dest_end = dest_end

    def __len__(self):
        return 5

    def __eq__(self, other):
        if len(other) != 5:
            return False

        return (
            other[0] == self.score
            and other[1] == self.src_start
            and other[2] == self.src_end
            and other[3] == self.dest_start
            and other[4] == self.dest_end
        )

    def __getitem__(self, i):
        if i == 0 or i == -5:
            return self.score
        if i == 1 or i == -4:
            return self.src_start
        if i == 2 or i == -3:
            return self.src_end
        if i == 3 or i == -2:
            return self.dest_start
        if i == 4 or i == -1:
            return self.dest_end

        raise IndexError("Opcode index out of range")

    def __repr__(self):
        return f"ScoreAlignment(score={self.score}, src_start={self.src_start}, src_end={self.src_end}, dest_start={self.dest_start}, dest_end={self.dest_end})"
