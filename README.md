# NieR:Automata cheat code on keyboard and mouse (PC)

A step-by-step guide, with screenshots, for entering NieR:Automata's final cheat code on PC using a keyboard
and mouse. The cheat unlocks chapter select, the debug room and the trophy shop by skipping straight to the
final ending.

**Read the guide: <https://suemon-kwok.github.io/nier-automata-cheat-code-keyboard/>**

Video walkthrough: <https://www.youtube.com/watch?v=YOUR_VIDEO_ID>

## The short version

The cheat only listens to gamepad buttons, so the game's own keyboard settings cannot enter it. It does work
if Windows believes an Xbox controller is plugged in. The guide builds a virtual Xbox controller and drives it
from your keyboard and mouse, using three free tools:

| Tool | What it does |
| --- | --- |
| [ViGEmBus](https://github.com/nefarius/ViGEmBus/releases) | Creates the virtual Xbox 360 controller |
| [UCR (Universal Control Remapper)](https://github.com/Snoothy/UCR/releases) | Turns key presses into controller buttons |
| [Interception](https://github.com/oblitum/Interception) | Lets UCR read, and block, your keyboard and mouse |

The sequence, in PlayStation and Xbox names, with the keys the guide uses:

| Step | PlayStation | Xbox | Key |
| --- | --- | --- | --- |
| Hold | R2 | RT | Middle mouse button |
| 1 | Up | D-pad up | I |
| 2 | Down | D-pad down | K |
| 3 | Up | D-pad up | I |
| 4 | Right | D-pad right | L |
| 5 | Left | D-pad left | J |
| 6 | Square | X | U |
| 7 | Circle | B | O |
| 8 | Triangle | Y | Y |
| 9 | Cross | A | H |

Where: the prologue, after the Marx boss fight and the short 9S conversation, standing between the two sets of
three barrels.

The part that takes the longest is the right trigger. The obvious mapping lets go of R2 while you are still
holding the key, and the game cancels the code when that happens. The guide shows the plugin that holds it.

## What is in this repository

| Path | Contents |
| --- | --- |
| `index.html` | The whole guide: one page, dark theme by default, with a light theme toggle |
| `images/` | The screenshots used in the guide (WebP) |
| `tools/` | Three read-only Python scripts used to inspect the game's cheat code (see below) |
| `LICENSE` | MIT license |

To read it offline, download the repository and open `index.html` in a browser.

## The scripts in `tools/`

They read the running game's memory to check how the cheat works. They never write to the game.

- `find_cheat_code_v2.py` finds the cheat function by its coordinate constants and writes a disassembly report.
- `watch_cheat_inputs.py` logs the held and pressed button values the cheat reads.
- `watch_cheat_manager.py` finds the cheat object and logs its press counter, timer and "fired" flag.

They need 64-bit Python, and install `pymem` and `capstone` on first run. The addresses inside them are for one
Steam build of the Game of the Year edition (`NieRAutomata.exe` image size `0x18f7000`). The scripts check this
and stop on any other build.

## Tested on

Steam, Game of the Year edition, Windows 11, October 2026. One build and one machine, so results on other
versions may differ.

## Credits

- The cheat code was discovered by Lance McDonald. His video explains how he found it:
  <https://www.youtube.com/watch?v=nj95Gumb-_8>
- ViGEmBus by Nefarius, UCR by Snoothy, and Interception by Francisco Lopes. This repository links to their
  official pages and does not redistribute them. Interception is free for non-commercial use, and its author
  sells commercial licences.

## Licence

The guide text, page code and scripts are released under the [MIT License](LICENSE).

That licence does not cover everything in the repository. The game screenshots belong to Square Enix and
PlatinumGames, the frames taken from Lance McDonald's video belong to him, and the third-party tools have their
own licences.

## Disclaimer

This is an unofficial fan guide. It is not affiliated with Square Enix, PlatinumGames or Lance McDonald. It
installs third-party drivers and uses a cheat that can lead to deleting save data. It is meant for single-player
use. Back up your saves first, and do not use these tools in online games.
