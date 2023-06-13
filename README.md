Chessy
======

This chess game was written by Violet McClure for final project.

![chessy interface picture](https://github.com/VioletJewel/i/blob/main/chessy.png)

There is no chess engine; this was quite enough work as it is.

It provides move validation and a nice UI.

There are three ways to move a piece:

    1. click and drag a piece
    2. click a square; then click a destination square
    3. use hjkl or arrow keys to move a cursor; use space to select a square
       and a destination square

If you don't use the arrow keys (or hjkl) and space, the cursor will disappear
when you move a piece.

There are numbers from 8 to 1 for the ranks and alphabetic characters from 'A'
to 'H' for the files.

If you make an invalid move, then an error message appears at the top of the
screen.

In order to implement this chess game,
[chessprogramming.org](https://www.chessprogramming.org/Main_Page) was heavily
used.

The move validation was implemented from memory, as I have played chess in my
free time since middle school and have learned from various source and from
playing on chess.com and lichess.

## Running

If you have not already, set up a virtual environment (venv): `python3 -m venv
env`

Each time you open a new shell, you need to start the venv: `source
env/bin/activate` (in bash or zsh)

For Windows, you may need to use `.\env\bin\activate`.

Before you run *Chessy* for the first time, do `pip install .`.

The above command should install everything; if you get an error installing
pygame, run `pip install pygame==2.0.0.dev6` first and then `pip install .`

Now, each time you want to run *Chessy*, just activate the virtual environment
and run `chessy` in the shell.

## Todo

Unfortunately, I didn't get time to make a chess engine. First, I need to
refactor how I do move validation and properly use bitboards. Then, I would be
able to experiment with minimax and other algorithms in conjunctin with
pseudo-valid move generation among other things that are commonly well known.
