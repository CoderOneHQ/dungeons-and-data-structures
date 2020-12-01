Dungeons and data structures: Tournamant game

## Installation instructions

"""shell
> python3 -m venv venv
> source venv/bin/activate
> pip install -r requirements.txt
"""

## Running a game
Once all game dependencies properly installed, the game can be launched using command line:
> ./main.py

There a number of command line option support by the game driver. To get a full list of options run:
> ./main.py --help


### Game modes
There are 3 main modes to run the game:
 - Interactive mode - when a human player can particiapate in a match
 This is a 'normal' game mode when a human user can play the game with the keyboard the game to explore it. This mode requires at least one bot.
 - Match - two or more* AI agents play a game without human participant.
 - 'Headless' match - the game is played by bots with no human participant without graphics output.
 This is the mode used to run a tornamanet.

By default, game runs in a tornament mode, without user input, with graphics output. For example, to ran a random match between two AI agent "agent1.py" and "agent2.py", run:
> ./main.py agent1 agent2

**Note** do not include ".py", because the agent code is loaded from a python module. In the example above, `agent1` - is python module name, represented by a single file `agent1.py`.

Agent with multiple files code are also supported. Keep in mind that each proper (python modules)[https://docs.python.org/3/tutorial/modules.html] must include `__init__.py` file.
 

