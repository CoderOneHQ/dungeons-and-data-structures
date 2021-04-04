> ⚠️ **Are you here for the 2021 AI Sports Challenge?** \
This repo contains the game and documentation for the 2020 version of Dungeons and Data Structures. You can play around with it as practise, but a new game and documentation will be released at the start of the challenge on 22 April 5 PM (AEST). Stay up to date on challenge announcements by joining our [Discord](https://discord.gg/NkfgvRN) and checking your email (after registering [here](https://gocoder.one/aisports?utm_source=github)).

# Dungeons & Data Structures

**The AI Sports Challenge 2020 season has officially ended!**
We had some amazing submissions from around the world. Congratulations to all our teams! 🎉
If you created a bot, we'd love for you to share it with us by raising a pull request against this repo and adding the link to your bot for others to play against below. 👇

### Agent Directory
- TEAM NAME
- Baby Yoda
- terserah
- pBot Compilers
- [Level 1 NPC](https://github.com/Jy4ng/coderone2020)
- bruh
- [ARX II-13](https://github.com/yukuefume/arx_ii-13)
- M Zheng
- KnAIght
- A Tan
- BombPyrates
- Chaotic NULLtral
- [Jigglybluff](https://github.com/garyleecf/jigglybluff_ozzymozzy)
- RizDog
- [PGB](https://github.com/GillesVandewiele/aisports-bomberman)
- Rengoku
- Monty Python 3.9.1
- Reed-Solo-man Error Collector
- [Bots by Robots](https://github.com/tannishpage/Coder_one_bot)
- [Gambit](https://github.com/Jfbarr/Gambit-dijkstra-bot)
- jab.AI
- FleeBot2077
- [Floth](https://github.com/suwat513/coderone-floth)
- DLCT2
- FSO
- Oke
- Mosin
- Thailandnumberone
- Bomber Clan
- ZeroNet
- thegeeky
- AeroBot
- Yeet Yate Yote
- Donkie
- [K Chan](https://github.com/kaleongchan/k-chan-agent)
- [Team Solo Bot](https://github.com/christopherhb/faiker)
- [Artificial Incompetence](https://github.com/gimait/DaDSbot)
- SY
- [Wizards](https://github.com/chrisrabe/ai-sports)
- UC Engineering Society
- Rootbeer
- Datawizards

# Setup and Installation
> ⚠️ **New here?** \
We **HIGHLY** recommend checking out the full documentation [here](https://bit.ly/aisportschallenge), which includes installation instructions, getting started tutorials, FAQ's, and tips and tricks.

You're also welcome to join us on [Discord](https://discord.gg/NkfgvRN) to contribute to the discussion or ask any questions from the community.

## Prerequisites
This is a `python` project and a valid Python3 installation is required to run it.
If you don't have `python` installed on your machine, please go to the official Python web site [here](https://www.python.org/) and follow installation instructions for your operating system.

## Installation
There are several ways to install the project. The simplest way is to use intallation package.
Download the latest available release from the [github release page](https://github.com/gocoderone/dungeons-and-data-structures/releases).

### MacOS/Linux
Assuming `~/workspace` is the directory you want to use to develop your Agent, open your terminal and run:
```shell
# Create a working directory for your project:
> mkdir -p ~/workspace/my-agent

# Change into that directory
> cd ~/workspace/my-agent

# Create a python virtual environment. Let's call it venv
> python3 -m venv venv
# Activate your new python environment
> source venv/bin/activate

# Install Coder One Dungeon module you have previously downloaded:
> pip install ~/Downloads/coderone-challenge-dungeons-0.1.0.tar.gz

```
Once you have a working installation you can start working on your Agent:
```
coderone-dungeon --interactive --watch my_agent
```

### Windows
Windows installation follows similar steps as other operating system. For a step-by-step, check the full documentation [here](https://bit.ly/aisportschallenge).
It is possible that you might need to use an alternative way to start the game, instead of relying on the convenience wrapper `codeone-dungeon`.
```shell
> python -m coderone.dungeon.main
```

## Running a game
Once all game dependencies have been properly installed, the game can be launched using command line:
```
python -m coderone.dungeon.main
```

There are a number of command line options supported by the game driver. To get a full list of options run:
```
python -m coderone.dungeon.main --help
```

### Command line options summory
The game runner recognises a number of command line options.
Use  `python -m coderone.dungeon.main --help` to get a list of supported options.

* `--headless` - run the game without graphics. Tournament matches will be run in this mode.
* `--interactive` - game is created with an extra player for the interactive user. This player can be controlled using your keyboard.
* `--watch` - automatically reload user's Agent if source code files changes. This allows for interactive development as code can be edited while the game is running.
* `--record <FILE>` - record game action into a specified file for later review.

### Interactive mode keys:
* `Enter` - pause / un-pause the game
* `r` - restart the game with a new random map
* `↑` / `↓` / `←` / `→` - move
* `<SPACE>` - place a bomb

### Game modes
There are 3 main modes to run the game:
 - Interactive mode - when a human player can participate in a match
 This is a 'normal' game mode when a human user can play the game with the keyboard the game to explore it. This mode requires at least one bot to be specified.
 - Match - two or more* Agents play a game without a human participant.
 - 'Headless' match - the game is played by bots with no human participant and without graphics output.
This is the mode used to run a tournament.

By default, game runs in a tournament mode, without user input, with graphics output. For example, to run a random match between two Agents "agent1.py" and "agent2.py", run:
```
coderone-dungeon agent1.py agent2.py
```

Agents with multi-file code are also supported. Keep in mind that a proper [python module](https://docs.python.org/3/tutorial/modules.html) must include `__init__.py` file.

## Config options
On the first run the game will generate a default config file `config.json` and store it in the OS-specific configuation directory.

Default config looks like this:
```
{
	"headless": false,
	"interactive": false,
	"start_paused": true,
	"wait_end": 5,
	"max_iterations": 3000,
	"tick_step": 0.10
}
```
### Config notes
In your local development environment you have access to all config options, such as number of iterations the game runs (`max_iterations`) or game update time step (`tick_step`). However, these options are fixed in the tournament and cannot be modified so please don't rely on these values.


## Known issues
The Python library used for graphics has some known issues.
If you experience a game crash with an error like:
```
munmap_chunk(): invalid pointer
Aborted (core dumped)
```
Add the following option to your `config.json`
```
...
 "no_text": true,
...
```

This options disables all text in the game which resolves library crashes.

On ARM, python Arcade fails to install without FFI. Install it via:
```shell
> sudo apt install libffi-dev libtiff5-dev libjpeg8-dev libopenjp2-7-dev zlib1g-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python3-tk \
    libharfbuzz-dev libfribidi-dev libxcb1-dev
```

## Development

Clone this git repository:
```
git clone https://github.com/gocoderone/dungeons-and-data-structures
```

Open terminal and run the following commands:

```shell
> cd <git check-out>
> python3 -m venv venv
> source venv/bin/activate
> pip install -r coderone/dungeon/requirements.txt

```

## Contributions
As we work towards building the home for AI Sports, we welcome all feedback and contributions to help us improve the experience for participants.

Feel free to [raise](https://github.com/gocoderone/dungeons-and-data-structures/issues/new/choose) an issue against this Repo if you experience any issues or would like to send a suggestion.

## Authors
HUMANS at [Coder One](https://www.gocoder.one/):
* Ivan aka [@abbyssoul](https://github.com/abbyssoul)

