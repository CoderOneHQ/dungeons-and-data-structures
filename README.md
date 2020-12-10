# Dungeons & Data Structures: Coder One AI Game Challenge

### Prerequisites
This is a `python` project and valid Python3 installation is required to run it.
If you don't have have `python` installed on your machine, please go to python the official python [web site pt](https://www.python.org/) and follow installation instructions for your operating system.

## Installation
There are a number of ways to install the project. Easies is to use intallation package. 
Download latest avaialble release from [github release page](https://github.com/gocoderone/dungeons-and-data-structures/releases).

### MacOS/Linux
Assuming `~/workspace` is the directory you want to use to delevop your AI-agent:
Open terminal and run
```shell
# Create a working directory for your project:
> mkdir -p ~/workspace/my-agent

# Change into that directory
> cd ~/workspace/my-agent

# Create a python virtual environment. Lets call it venv
> python3 -m venv venv
# Activate your new python environment
> source venv/bin/activate

# Install CoderOne Dungen module you have previously downloaded:
> pip install ~/Downloads/coderone-challenge-dungeons-0.1.0.tar.gz

```
Once you have working installation you can start working on your AI-agent.
> coderone-dungeon --interactive --watch my_agent

### Windows
Windows installation follows similar steps as other operating system. 
It is possible that you might need to use an alternative way to start the game, instead of realying on the convenice wraper `codeone-dungeon`
```shell
> python -m coderone.dungeon.main
```

## Running a game
Once all game dependencies properly installed, the game can be launched using command line:
> python -m coderone.dungeon.main

There a number of command line option support by the game driver. To get a full list of options run:
> python -m coderone.dungeon.main --help

### Commandline options summory
Game runner recognises a number of command line options.
use  `python -m coderone.dungeon.main --help` to get a list of supported options.

* `--headless` - run the game without graphics. Tournament matches will be run in this mode.
* `--interactive` - game is created with extra player for the interactive user. This player can be controlled using keyboard.
* `--watch` - automatically reload user agent if source code files changes. This allows for interactive development as code can be edited while the game is running.
* `--record <FILE>` - record game action into a specified file for later review.


### Interactive mode keys:
* `Enter` - to pause / un-pause the game
* `r` - to restart the game with new random map
* `↑` / `↓` / `←` / `→` - arrows to move the player
* `<SPACE>` - to place the bomb


### Game modes
There are 3 main modes to run the game:
 - Interactive mode - when a human player can particiapate in a match
 This is a 'normal' game mode when a human user can play the game with the keyboard the game to explore it. This mode requires at least one bot.
 - Match - two or more* AI agents play a game without human participant.
 - 'Headless' match - the game is played by bots with no human participant without graphics output.
 This is the mode used to run a tornamanet.

By default, game runs in a tornament mode, without user input, with graphics output. For example, to ran a random match between two AI agent "agent1.py" and "agent2.py", run:
> coderone-dungeon agent1.py agent2.py

Agent with multiple files code are also supported. Keep in mind that a proper [python modules](https://docs.python.org/3/tutorial/modules.html) must include `__init__.py` file.

## Config options
On the first run the game will generate default config file `config.json` and store in the OS-specific configuation directory.

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
In your local developemnt environemnt you have access to all config options, such as nubmer of iteration the game runs (`max_iterations`) or game update time step (`tick_step`). However, this options are fixed in the tournamtent and can not be modified so please don't rely on this values.


## Known issues
Python library used for graphics has some known issues.
If you experience a game crash with error like:
```
munmap_chunk(): invalid pointer
Aborted (core dumped)
```
Add the following option to your `config.json`
> "no_text": false,

This options disables all texts in the game which resolves library crashes.

On ARM you python Arcade fails to install without FFI. Install it via:
```shell
> sudo apt install libffi-dev libtiff5-dev libjpeg8-dev libopenjp2-7-dev zlib1g-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python3-tk \
    libharfbuzz-dev libfribidi-dev libxcb1-dev
```

## Development

Clone this git repository:
> git clone https://github.com/gocoderone/dungeons-and-data-structures

Open termnial and run following commands

```shell
> cd <git check-out>
> python3 -m venv venv
> source venv/bin/activate
> pip install -r coderone/dungeon/requirements.txt
 
```

## Contributions
As we strive to build AI sport games we welcome all contributions to improve the experience for all participants.

Feel free to [raise](https://github.com/gocoderone/dungeons-and-data-structures/issues/new/choose) an issue in the github repository if you experiece any issue or would like to send a suggestion.

## Authors
HUMANS at [Coder One](https://www.gocoder.one/):
* Ivan aka [@abbyssoul](https://github.com/abbyssoul)

