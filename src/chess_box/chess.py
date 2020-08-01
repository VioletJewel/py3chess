#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum, IntFlag

class Bitboard():
    """
          +-----------------------+
        8 |00 01 02 03 04 05 06 07|
          |                       |
        7 |08 09 10 11 12 13 14 15|
          |                       |
        6 |16 17 18 19 20 21 22 23|
          |                       |
        5 |24 25 26 27 28 29 30 31|
          |                       |
        4 |32 33 34 35 36 37 38 39|
          |                       |
        3 |40 41 42 43 44 45 46 47|
          |                       |
        2 |48 49 50 51 52 53 54 55|
          |                       |
        1 |56 57 58 59 60 61 62 63|
          +-----------------------+
           A  B  C  D  E  F  G  H
    """
    def __init__(self, mask):
        self.mask = mask

    def copy(self):
        return self.__class__(self.mask)

    @classmethod
    def from_ranks(cls, ranks):
        mask = 0
        bitmask = 1
        for rank in range(8):
            # top rank (8) -> bottom rank (1)
            if ranks & bitmask:
                mask |= 0b11111111 << (rank * 8)
            bitmask <<= 1
        return cls(mask)

    @classmethod
    def from_quadrant(cls, quad_bit):
        """ mirror quadrant bit to all four quadrants

               quad_bit     =>  mask
                 row
               0  1  2  3
              +-----------+    +-----------+   +-----------+   +-----------+   +-----------+
            0 |00 01 02 03|    |00 01 02 03|   |07 06 05 04|   |56 57 58 59|   |63 62 61 60|
          c   |           |    |           |   |           |   |           |   |           |
          o 1 |04 05 06 07|    |08 09 10 11|   |15 14 13 12|   |48 49 50 51|   |55 54 53 52|
          l   |           | => |           | + |           | + |           | + |           |
            2 |08 09 10 11|    |16 17 18 19|   |23 22 21 20|   |40 41 42 43|   |47 46 45 44|
              |           |    |           |   |           |   |           |   |           |
            3 |12 13 14 15|    |24 25 26 27|   |31 30 29 28|   |32 33 34 35|   |39 38 37 36|
              +-----------+    +-----------+   +-----------+   +-----------+   +-----------+
        """
        r  = quad_bit // 4 # quadrant row
        c  = quad_bit % 4  # quadrant column
        mask  = 1 << (r       * 8 +     c     )
        mask |= 1 << (r       * 8 + 3 - c + 4 )
        mask |= 1 << ((3 - r) * 8 +     c + 32)
        mask |= 1 << ((3 - r) * 8 + 3 - c + 36)
        return cls(mask)

    @classmethod
    def from_indices(cls, *bits):
        mask = 0
        for bit in bits:
            mask |= 1 << bit
        return cls(mask)

    def pretty(self):
        lines = []
        for r in range(8):
            line = []
            for c in range(8):
                i = r * 8 + c
                line.append(" " + ("*" if self.mask & (1 << i) else "_"))
            lines.append("".join(line))
        return "\n".join(lines)

    def __str__(self):
        return self.pretty()

    def __format__(self, fmt):
        return str.__format__(self.__str__(), fmt)

    def __repr__(self):
        return self.pretty()

    def __bool__(self):
        return bool(self.mask)

    def __or__(self, bb):
        return self.__class__(self.mask | bb.mask)

    def __and__(self, bb):
        return self.__class__(self.mask & bb.mask)

    def __xor__(self, bb):
        return self.__class__(self.mask ^ bb.mask)

    def __invert__(self):
        return self.__class__((~self.mask) & 0xffffffffffffffff)

    def __contains__(self, mask):
        return self.mask & mask

    def __getitem__(self, bit):
        return (self.mask >> bit) & 1

    def __setitem__(self, bit, on):
        if on:
            self.mask |= 1 << bit
        else:
            self.mask &= ~(1 << bit)

    def has_bit(bit):
        return self.mask & (1 << bit)

class Color(Enum):
    """ Color: light, dark """
    LIGHT = False
    DARK  = True

    def __invert__(self):
        return Color(abs(self._value_-1)) # avoid branches; uses __new__() (perf untested)

    def __bool__(self):
        return self._value_

    def __int__(self):
        return int(self._value_)

    def __str__(self):
        return "Dark" if self._value_ else "Light"

    def __format__(self, fmt):
        return str.__format__(self.__str__(), fmt)


class PieceType(Enum):
    """ Piece Type: king, queen, rook, bishop, knight, pawn """
    KING   = 'k'
    QUEEN  = 'q'
    ROOK   = 'r'
    BISHOP = 'b'
    KNIGHT = 'n'
    PAWN   = 'p'

    def __str__(self):
        name = self._name_
        return name[0] + name[1:].lower()

    def __int__(self):
        return self._member_names_.index(self._name_) + 2

    def __hash__(self):
        return int(self)

class Piece():
    def __init__(self, color, piecetype):
        self.color = color
        self.piecetype = piecetype

    def get_char(self):
        return self.piecetype.value if self.color else self.piecetype.value.upper()

    def __str__(self):
        return "{} {}".format(self.color, self.piecetype)

    def __format__(self, fmt):
        return str.__format__(self.__str__(), fmt)

    def __format__(self, fmt):
        return str.__format__(self.__str__(), fmt)

    def __repr__(self):
        return "Piece({}, {})".format(self.color, self.piecetype)

    def __hash__(self):
        return (int(self.color) + 2) * (int(self.piecetype) - 2) + 8

    def __eq__(self, o):
        return o.__class__ == self.__class__ and self.color == o.color and self.piecetype == o.piecetype

    @classmethod
    def from_str(cls, char):
        return cls(Color(char.islower()), PieceType(char.lower()))

class MoveStatus(IntFlag):
    INVALID   = 0
    VALID     = 1
    ENPASSANT = 2
    CAPTURE   = 4
    CASTLE    = 8

class Board():
    def __init__(self, **kwargs):
        self.turn = kwargs.get("turn", Color.LIGHT)
        self.halfmove_clock = kwargs.get("halfmove_clock", 0)
        self.ep_bit = kwargs.get("ep_bit", None)
        self.castle = kwargs.get("castle", dict((c, 0b11) for c in Color))
        self.states = []
        self.movestatus = MoveStatus(0)
        self.error_msg = None
        self.error  = False
        self.bbs = {
                "all"            : kwargs.get("bb_all"     , Bitboard.from_ranks(0b11000011)),
                Color.LIGHT      : kwargs.get("bb_lights"  , Bitboard.from_ranks(0b11000000)),
                Color.DARK       : kwargs.get("bb_darks"   , Bitboard.from_ranks(0b00000011)),
                PieceType.KING   : kwargs.get("bb_kings"   , Bitboard.from_indices(4, 60)),
                PieceType.QUEEN  : kwargs.get("bb_queens"  , Bitboard.from_indices(3, 59)),
                PieceType.ROOK   : kwargs.get("bb_rooks"   , Bitboard.from_quadrant(0)),
                PieceType.KNIGHT : kwargs.get("bb_knights" , Bitboard.from_quadrant(1)),
                PieceType.BISHOP : kwargs.get("bb_bishops" , Bitboard.from_quadrant(2)),
                PieceType.PAWN   : kwargs.get("bb_pawns"   , Bitboard.from_ranks(0b01000010)),
                }

    def valid_move(self, from_bit, to_bit):
        self.movestatus = MoveStatus.INVALID
        self.error = False
        self.error_msg = None
        if from_bit < 0 or from_bit > 63:
            self.error = True
            self.error_msg = "from square must be between 0 and 63"
            return False
        if to_bit < 0 or to_bit > 63:
            self.error = True
            self.error_msg = "target square must be between 0 and 63"
            return False
        if to_bit == from_bit:
            self.error = True
            self.error_msg = "from and target square are the same"
        fp = self[from_bit]
        if fp is None:
            self.error = True
            self.error_msg = "selected piece empty"
            return False
        if fp.color != self.turn:
            self.error = True
            self.error_msg = "not {}'s turn".format(~self.turn)
            return False
        tp = self[to_bit]
        if tp and fp.color == tp.color:
            self.error = True
            self.error_msg = "cannot capture own color"
            return False
        dif = to_bit - from_bit
        xdif = (to_bit % 8) - (from_bit % 8)
        ydif = (to_bit // 8) - (from_bit // 8)
        # ---------
        # pawn move
        # ---------
        if fp.piecetype == PieceType.PAWN:
            front, start = (8,8) if fp.color else (-8,48)
            # moved once forward
            if dif == front:
                if tp is not None:
                    self.error = True
                    self.error_msg = "{} cannot capture on square in front".format(fp)
                else:
                    self.movestatus = MoveStatus.VALID
            # moved twice forward
            elif dif == 2 * front:
                if from_bit < start or from_bit > start + 7:
                    self.error = True
                    self.error_msg = "{} can only move two squares on the first move".format(fp)
                elif self[from_bit + front] is not None:
                    self.error = True
                    self.error_msg = "{} cannot move through another piece".format(fp)
                elif tp is not None:
                    self.error = True
                    self.error_msg = "{} cannot capture two squares in front".format(fp)
                else:
                    self.movestatus = MoveStatus.VALID | MoveStatus.ENPASSANT
            # diagonal capture
            elif (dif == front - 1 or dif == front + 1) and abs(xdif) == 1:
                if self.ep_bit == to_bit:
                    self.movestatus = MoveStatus.VALID | MoveStatus.CAPTURE | MoveStatus.ENPASSANT
                elif tp is None:
                    self.error = True
                    self.error_msg = "{} must capture on diagonal square".format(fp)
                else:
                    self.movestatus = MoveStatus.VALID | MoveStatus.CAPTURE
            # invalid target square
            else:
                self.error = True
                self.error_msg = "invalid target square for {}".format(fp)
        # -----------
        # knight move
        # -----------
        elif fp.piecetype == PieceType.KNIGHT:
            if abs(dif) in {6, 10, 15, 17} and abs(xdif) < 3:
                self.movestatus = MoveStatus.VALID
            else:
                self.error = True
                self.error_msg = "invalid target square for {}".format(fp)
        # -----------
        # bishop move
        # -----------
        elif fp.piecetype == PieceType.BISHOP:
            if abs(xdif) != abs(ydif):
                self.error = True
                self.error_msg = "invalid target square for {}".format(fp)
            else:
                inc = ydif // abs(ydif) * (9 if xdif == ydif else 7)
                for x in range(from_bit + inc, to_bit, inc):
                    if self[x]:
                        self.error = True
                        self.error_msg = "{} cannot move through another piece".format(fp)
                        break
                else:
                    self.movestatus = MoveStatus.VALID
        # ---------
        # rook move
        # ---------
        elif fp.piecetype == PieceType.ROOK:
            if xdif * ydif != 0:
                self.error = True
                self.error_msg = "invalid target square for {}".format(fp)
            else:
                inc = (xdif + ydif) // abs(xdif + ydif) * (1 if xdif else 8)
                for x in range(from_bit + inc, to_bit, inc):
                    if self[x]:
                        self.error = True
                        self.error_msg = "{} cannot move through another piece".format(fp)
                        break
                else:
                    self.movestatus = MoveStatus.VALID
        # ----------
        # queen move
        # ----------
        elif fp.piecetype == PieceType.QUEEN:
            # diagonals (like bishop)
            if abs(xdif) == abs(ydif):
                inc = ydif // abs(ydif) * (9 if xdif == ydif else 7)
                for x in range(from_bit + inc, to_bit, inc):
                    if self[x]:
                        self.error = True
                        self.error_msg = "{} cannot move through another piece".format(fp)
                        break
                else:
                    self.movestatus = MoveStatus.VALID
            # ranks/files (like rook)
            elif xdif * ydif == 0:
                inc = (xdif + ydif) // abs(xdif + ydif) * (1 if xdif else 8)
                for x in range(from_bit + inc, to_bit, inc):
                    if self[x]:
                        self.error = True
                        self.error_msg = "{} cannot move through another piece".format(fp)
                        break
                else:
                    self.movestatus = MoveStatus.VALID
            # invalid
            else:
                self.error = True
                self.error_msg = "invalid target square for {}".format(fp)
        elif fp.piecetype == PieceType.KING:
            # NOTE: castling doesn't handle all chess960 variants
            # queen-side castle
            if xdif == -2:
                if not self.castle[self.turn] & 0b10:
                    self.error = True
                    self.error_msg = "{} does not have privileges to castle queen-side".format(fp)
                elif self[from_bit-1]:
                    self.error = True
                    self.error_msg = "{} cannot castle through another piece".format(fp)
                elif self[from_bit-2]:
                    self.error = True
                    self.error_msg = "{} cannot castle and capture".format(fp)
                else:
                    self.movestatus = MoveStatus.VALID | MoveStatus.CASTLE
            # king-side castle
            elif xdif == 2:
                if not self.castle[self.turn] & 0b01:
                    self.error = True
                    self.error_msg = "{} does not have privileges to castle king-side".format(fp)
                elif self[from_bit+1]:
                    self.error = True
                    self.error_msg = "{} cannot castle through another piece".format(fp)
                elif self[from_bit+2]:
                    self.error = True
                    self.error_msg = "{} cannot castle and capture".format(fp)
                else:
                    self.movestatus = MoveStatus.VALID | MoveStatus.CASTLE
            # can move one square only
            elif not {abs(xdif), abs(ydif)}.issubset({0,1}):
                self.error = True
                self.error_msg = "invalid target square for {}".format(fp)
            else:
                self.movestatus = MoveStatus.VALID
        else:
            self.error = True
            self.error_msg = "unknown piece type"
        # -----------------------------------------------------------------------------------------
        # invalid move; return early
        if not self.movestatus:
            return False
        if self.future_check(from_bit, to_bit):
            self.error = True
            self.error_msg = "moving {} here will put the king in check".format(fp)
            self.movestatus = MoveStatus.INVALID
            return False
        # add capture flag if applicable
        if tp:
            self.movestatus |= MoveStatus.CAPTURE
        return True

    def in_check(self, from_bit, to_bit):
        cking = Piece(self.turn, PieceType.KING)
        for bit, p in enumerate(self):
            if p == cking:
                cking = bit
                break
        cx, cy = bit % 8, bit // 8
        knights = ( (-1, -2), (1, -2), (-2, -1), (2, -1), (-1, 2), (1, 2), (-2, 1), (2, 1) )
        kings = ( (-1, -1), (-1, 0), (-1, 1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1) )
        K,Q,R,B,N,P = tuple(Piece(~self.turn, pt) for pt in PieceType)
        for rx,ry in knights:
            x = cx + rx
            y = cy + ry
            if x < 0 or x > 8 or y < 0 or y < 8:
                continue
            b = y * 8 + x
            if self[b] == N:
                return True
        rels = (
                (-1, -1, {B,Q}, (lambda x,y: x >= 0 and y >= 0)),
                ( 1, -1, {B,Q}, (lambda x,y: x <= 8 and y >= 0)),
                (-1,  1, {B,Q}, (lambda x,y: x >= 0 and y <= 8)),
                ( 1,  1, {B,Q}, (lambda x,y: x <= 8 and y <= 8)),
                ( 1,  0, {R,Q}, (lambda x,y: x <= 8)),
                ( 0,  1, {R,Q}, (lambda x,y: y <= 8)),
                (-1,  0, {R,Q}, (lambda x,y: x >= 0)),
                ( 0, -1, {R,Q}, (lambda x,y: y >= 0)),
                )
        for rel in rels:
            rx, ry, s, test = rel
            x = cx + rx
            y = cy + ry
            while test(x, y):
                b = y * 8 + x
                p = self[b]
                if p in s:
                    return True
                x += rx
                y += ry
        for rx,ry in kings:
            x = cx + rx
            y = cy + ry
            if x < 0 or x > 8 or y < 0 or y < 8:
                continue
            b = y * 8 + x
            if self[b] == K:
                return True
        return False

    def future_check(self, from_bit, to_bit):
        bbs_backup = dict((k,bb.copy()) for k,bb in self.bbs.items())
        self[to_bit] = self[from_bit]
        self[from_bit] = None
        in_check = self.in_check(from_bit, to_bit)
        self.bbs = bbs_backup
        return in_check

    def make_move(self, from_bit, to_bit):
        if not self.valid_move(from_bit, to_bit):
            return
        if MoveStatus.ENPASSANT in self.movestatus:
            inc = 8 * (to_bit // 32 * 2 - 1)
            if MoveStatus.CAPTURE in self.movestatus:
                self[self.ep_bit - inc] = None
                self.ep_bit = None
            else:
                self.ep_bit = to_bit + inc
        else:
            self.ep_bit = None
        if MoveStatus.CASTLE in self.movestatus:
            self.castle[self.turn] = 0b00
            f_bit, t_bit = (-2, 1) if to_bit % 8 == 2 else (1, -1)
            f_bit += to_bit
            t_bit += to_bit
            self[t_bit] = self[f_bit]
            self[f_bit] = None
        elif to_bit == 0 or from_bit == 0:
            self.castle[Color.DARK] &= 0b01
        elif to_bit == 7 or from_bit == 7:
            self.castle[Color.DARK] &= 0b10
        elif to_bit == 56 or from_bit == 56:
            self.castle[Color.LIGHT] &= 0b01
        elif to_bit == 63 or from_bit == 63:
            self.castle[Color.LIGHT] &= 0b10
        c = self[to_bit]
        self[to_bit] = self[from_bit]
        self[from_bit] = None
        self.turn = ~self.turn

    def __iter__(self):
        for bit in range(64):
            yield self[bit]

    def __getitem__(self, bit):
        mask = 1 << bit
        if mask in self.bbs[Color.LIGHT]:
            color = Color.LIGHT
        elif mask in self.bbs[Color.DARK]:
            color = Color.DARK
        else:
            return None
        for pt in PieceType:
            if mask in self.bbs[pt]:
                return Piece(color, pt)

    def __setitem__(self, bit, piece):
        for pt in PieceType:
            self.bbs[pt][bit] = 0
        if piece is None:
            self.bbs[Color.LIGHT][bit] = 0
            self.bbs[Color.DARK][bit]  = 0
        else:
            self.bbs[piece.color][bit]  = 1
            self.bbs[~piece.color][bit] = 0
            self.bbs[piece.piecetype][bit] = 1

    def __str__(self):
        lines = []
        for r in range(8):
            line = []
            for c in range(8):
                p = self[r * 8 + c]
                line.append(p.get_char() if p else "_")
            lines.append(" ".join(line))
        return "\n".join(lines)


