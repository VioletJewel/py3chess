# -*- coding: utf-8 -*-

# fixes ALSA buffer underrun issues on archlinux regarding pygame font initialization
import sys
if sys.platform[:5] == "linux":
    import os
    os.environ['SDL_AUDIODRIVER'] = 'dsp'

from chess_box import chess
import enum
import pathlib
import pygame
import time

pygame.init()
pygame.font.init()

# dimensions and padding
SQUARE_SIZE = (60, 60)
PAD = 8
CURSOR_PAD = 5
ID_PAD = 30
# colors
BG_COLOR = (104, 74, 50)
SQUARE_COLORS = [ (240, 217, 181), (181, 136, 99) ]
SELECTED_COLOR = (20, 85, 30)
CURSOR_COLOR = (20, 112, 70)
FONT_COLOR = SQUARE_COLORS[0]
# alphas
SELECTED_ALPHA = 128
GHOST_ALPHA = 102
# delay
REPEAT_DELAY = 0.2
REPEAT_WAIT = 0.05
# pygame keys
UP_KEYS = (pygame.K_UP, pygame.K_k)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_l)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_j)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_h)
# font
FONT = pygame.font.Font(str(pathlib.Path(__file__).with_name("ubuntu_font")/"Ubuntu-R.ttf"), 30)
ID_RANKS = tuple(FONT.render(str(n+1), True, FONT_COLOR) for n in range(7, -1, -1))
ID_FILES = tuple(FONT.render(chr(n), True, FONT_COLOR) for n in range(ord('A'), ord('H')+1))
MSG_FONT = pygame.font.Font(str(pathlib.Path(__file__).with_name("ubuntu_font")/"Ubuntu-R.ttf"), 18)

PIECES = {}
GHOSTS = {}
def _get_pieces(path):
    for pt in chess.PieceType:
        for c in chess.Color:
            piece = chess.Piece(c, pt)
            img_path = path/"{}_{}.png".format(pt, c)
            image = pygame.image.load(str(img_path))
            PIECES[piece] = image
            surf = pygame.Surface(SQUARE_SIZE)
            surf.fill((0, 255, 0))
            surf.set_colorkey((0, 255, 0))
            surf.blit(image, (0, 0))
            surf.set_alpha(GHOST_ALPHA)
            GHOSTS[piece] = surf
_get_pieces(pathlib.Path(__file__).with_name("pieces"))

SQUARES_RECTS = tuple(pygame.Rect((x, y), SQUARE_SIZE)
        for y in range(ID_PAD + PAD, PAD + SQUARE_SIZE[1] * 8, SQUARE_SIZE[1])
        for x in range(ID_PAD + PAD, PAD + SQUARE_SIZE[0] * 8, SQUARE_SIZE[0])
        )

def _get_squares():
    sq_surfs = (
        pygame.Surface(SQUARE_SIZE),
        pygame.Surface(SQUARE_SIZE)
    )
    sq_surfs[int(chess.Color.LIGHT)].fill(SQUARE_COLORS[int(chess.Color.LIGHT)])
    sq_surfs[int(chess.Color.DARK)].fill(SQUARE_COLORS[int(chess.Color.DARK)])
    return sq_surfs
SQUARES = _get_squares()

def _get_cursor():
    vsurf = pygame.Surface((CURSOR_PAD, SQUARE_SIZE[1]))
    vsurf.fill(CURSOR_COLOR)
    hsurf = pygame.Surface((SQUARE_SIZE[0] - 2 * CURSOR_PAD, CURSOR_PAD))
    hsurf.fill(CURSOR_COLOR)
    cursor_surf = pygame.Surface(SQUARE_SIZE)
    cursor_surf.set_colorkey((0, 0, 0))
    cursor_surf.blit(vsurf, (0, 0))
    cursor_surf.blit(vsurf, (SQUARE_SIZE[0] - CURSOR_PAD, 0))
    cursor_surf.blit(hsurf, (CURSOR_PAD, 0))
    cursor_surf.blit(hsurf, (CURSOR_PAD, SQUARE_SIZE[1] - CURSOR_PAD))
    return cursor_surf
CURSOR = _get_cursor()


def _get_selected():
    surf = pygame.Surface(SQUARE_SIZE)
    surf.fill(SELECTED_COLOR)
    surf.set_alpha(SELECTED_ALPHA)
    return surf
SELECTED = _get_selected()


def pos_to_index(x, y):
    lpad = PAD + ID_PAD
    tpad = PAD + ID_PAD
    if (x < lpad or y < tpad or
            x > lpad + 8 * SQUARE_SIZE[0] or y > tpad + 8 * SQUARE_SIZE[1]):
        return None
    xfloor, yfloor = (x - lpad) // SQUARE_SIZE[0], (y - tpad) // SQUARE_SIZE[1]
    return xfloor + 8 * yfloor


class DirMask(enum.IntFlag):
    UP = 1
    RIGHT = 2
    DOWN = 4
    LEFT = 8

class UI():
    def __init__(self):
        self.size = (
                8*SQUARE_SIZE[0] + 2*PAD + 2*ID_PAD,
                8*SQUARE_SIZE[1] + 2*PAD + 2*ID_PAD,
                )
        self.display = pygame.display.set_mode(self.size)
        self.display.fill(BG_COLOR)
        self.dirty = True
        self.clock = pygame.time.Clock()
        self.fps = 120

        self.dirmask = DirMask(0)     # mask for directions (has all directions)
        self.dirtime = None           # direction time (when direction key first pressed)
        self.dirtime_repeat = None    # direction time repeat (when dir key repeated)
        self.cursor = 52              # cursor (E2)
        self.sel_ind = None       # selected square
        self.board = chess.Board()    # chess board
        self.dragpiece = None         # piece currently being dragged with mouse
        self.dragpos = None           # position of piece being dragged
        self.piecemoved = False       # indicates if piece moved at all between mouse DOWN and UP
        self.double_select = False    # occurs if same square single clicked twice
        self.ignore_mouseup = False   # should ignore next mouseup event
        self.draw_cursor = True       # do blit cursor (turn off if only mouse events used)
        self.error_msg = None         # used to display error messages

        # cursor surf
        vsurf = pygame.Surface((CURSOR_PAD, SQUARE_SIZE[1]))
        vsurf.fill(CURSOR_COLOR)
        hsurf = pygame.Surface((SQUARE_SIZE[0] - 2 * CURSOR_PAD, CURSOR_PAD))
        hsurf.fill(CURSOR_COLOR)
        self.cursor_surf = pygame.Surface(SQUARE_SIZE)
        self.cursor_surf.set_colorkey((0, 0, 0))
        self.cursor_surf.blit(vsurf, (0, 0))
        self.cursor_surf.blit(vsurf, (SQUARE_SIZE[0] - CURSOR_PAD, 0))
        self.cursor_surf.blit(hsurf, (CURSOR_PAD, 0))
        self.cursor_surf.blit(hsurf, (CURSOR_PAD, SQUARE_SIZE[1] - CURSOR_PAD))

    def mainloop(self):
        running = True
        while running:
            for event in pygame.event.get():
                running &= self.onevent(event)
            if self.dirty:
                self.onrender()
                self.dirty = False
            self.clock.tick(self.fps)

    def onevent(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            self.keydown(event)
        elif event.type == pygame.KEYUP:
            self.keyup(event)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mousedown(event)
        elif event.type == pygame.MOUSEMOTION:
            self.mousemove(event)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouseup(event)
        return True

    def keydown(self, event):
        self.draw_cursor = True
        key = event.key
        dirty = False
        if key == pygame.K_SPACE:
            # TODO: dirtyRects
            dirty = True
            if self.sel_ind:
                if self.sel_ind != self.cursor:
                    self.trymove(self.sel_ind, self.cursor)
                self.sel_ind = None
            elif self.board[self.cursor] is not None:
                self.sel_ind = self.cursor
        elif key in UP_KEYS:
            self.dirmask |= DirMask.UP
            self.dirmask &= ~DirMask.DOWN
        elif key in RIGHT_KEYS:
            self.dirmask |= DirMask.RIGHT
            self.dirmask &= ~DirMask.LEFT
        elif key in DOWN_KEYS:
            self.dirmask |= DirMask.DOWN
            self.dirmask &= ~DirMask.UP
        elif key in LEFT_KEYS:
            self.dirmask |= DirMask.LEFT
            self.dirmask &= ~DirMask.RIGHT
        dirty |= bool(self.dirmask)
        if not dirty:
            self.dirtime = None
        self.dirty = dirty

    def trymove(self, from_ind, to_ind):
        self.board.make_move(from_ind, to_ind)
        if self.board.error:
            self.error_msg = self.board.error_msg
        else:
            self.error_msg = None


    def keyup(self, event):
        dirty = False
        key = event.key
        if key == pygame.K_SPACE:
            dirty = True
        elif key in UP_KEYS:
            self.dirmask &= ~DirMask.UP
        elif key in RIGHT_KEYS:
            self.dirmask &= ~DirMask.RIGHT
        elif key in DOWN_KEYS:
            self.dirmask &= ~DirMask.DOWN
        elif key in LEFT_KEYS:
            self.dirmask &= ~DirMask.LEFT
        dirty |= bool(self.dirmask)
        if not dirty:
            self.dirtime = None
        self.dirty = dirty

    def mousedown(self, event):
        self.dragging = False
        index = pos_to_index(*event.pos)
        if index is None:
            self.dirty = False
            return
        self.cursor = index
        self.sel_ind = self.cursor
        p = self.board[self.sel_ind]
        if p is not None:
            self.dragpiece = p
            x, y = event.pos
            self.dragpos = (x - SQUARE_SIZE[0] // 2, y - SQUARE_SIZE[1] // 2)
            self.piecemoved = False
            self.dirty = True
            return
        self.dirty = False

    def mousemove(self, event):
        if self.dragpos:
            self.dragging = True
            self.double_select = False
            index = pos_to_index(*event.pos)
            if index is None:
                self.dirty = False
                return
            cursor = index
            x, y = event.pos
            self.dragpos = (x - SQUARE_SIZE[0] // 2, y - SQUARE_SIZE[1] // 2)
            if cursor != self.cursor:
                self.piecemoved = True
            self.dirty = True
            return
        self.dirty = False

    def mouseup(self, event):
        self.dragging = False
        x, y = event.pos
        newpos = (x - SQUARE_SIZE[0] // 2, y - SQUARE_SIZE[1] // 2)
        if event.pos != newpos:
            self.dragpos = event.pos
            self.ignore_mouseup = False
        if self.double_select:
            self.double_select = False
            self.sel_ind = None
            self.piecemoved = False
            self.dragging = False
            self.dragpos = None
            self.dragpiece = None
            self.dirty = True
            return
        if self.ignore_mouseup:
            self.ignore_mouseup = False
        else:
            index = pos_to_index(*event.pos)
            if index is None:
                self.dragpos = None
                self.dragpiece = None
                self.sel_ind = None
                self.dirty = True
                return
            self.cursor = index
            self.dragpiece = None
            self.dragpos = None
            if not self.piecemoved:
                self.sel_ind = self.cursor
                self.double_select = True
            else:
                self.draw_cursor = False
                if self.sel_ind != self.cursor:
                    self.trymove(self.sel_ind, self.cursor)
                self.sel_ind = None
        self.dirty = True

    def onrender(self):
        if self.dirmask:
            move = False
            t = time.time()
            if self.dirtime is None:
                move = True
                self.dirtime = t
                self.dirtime_repeat = self.dirtime
            elif t - self.dirtime > REPEAT_DELAY:
                if t - self.dirtime_repeat > REPEAT_WAIT:
                    self.dirtime_repeat = t
                    move = True
            if move:
                inc = 0
                if DirMask.UP in self.dirmask:
                    if self.cursor // 8 > 0:
                        inc += -8
                if DirMask.RIGHT in self.dirmask:
                    if self.cursor % 8 < 7:
                        inc += 1
                if DirMask.DOWN in self.dirmask:
                    if self.cursor // 8 < 7:
                        inc += 8
                if DirMask.LEFT in self.dirmask:
                    if self.cursor % 8 > 0:
                        inc += -1
                if inc:
                    # TODO: dirtyRects (much lighter rendering)
                    self.cursor = self.cursor + inc
        # draw board
        self.display.fill(BG_COLOR)
        for i, txt in enumerate(ID_RANKS):
            x, y = SQUARES_RECTS[i * 8].topleft
            x -= ID_PAD - 2
            y += 12
            self.display.blit(txt, (x, y))
        for i, txt in enumerate(ID_FILES):
            x, y = SQUARES_RECTS[i + 56].bottomleft
            y += 2
            x += 17
            self.display.blit(txt, (x, y))
        if self.error_msg:
            errmsg = MSG_FONT.render(self.error_msg, True, FONT_COLOR)
            self.display.blit(errmsg, (ID_PAD + 5, 5))
        for i, p in enumerate(self.board):
            sr = SQUARES_RECTS[i]
            square = SQUARES[(i // 8) % 2 != i % 2]
            self.display.blit(square, sr)
            sel_sr = SQUARES_RECTS[self.sel_ind] if i == self.sel_ind else None
            if p is not None:
                if sel_sr:
                    # draw transparent ghost piece
                    self.display.blit(PIECES[p], sr)
                    # draw select background
                    self.display.blit(SELECTED, sr)
                else:
                    # draw normal piece
                    self.display.blit(PIECES[p], sr)
        if self.draw_cursor:
            x, y = self.cursor // 8, self.cursor % 8
            self.display.blit(CURSOR, SQUARES_RECTS[self.cursor])
        # draw drag piece
        if self.dragpos and self.dragging:
            self.display.blit(GHOSTS[self.dragpiece], self.dragpos)
        # if self.dirmask:
        pygame.display.flip()

def main():
    ui = UI()
    ui.mainloop()
    pygame.quit()

if __name__ == "__main__":
    main()
