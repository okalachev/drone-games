# drone-games

Task:

* https://github.com/acsl-mipt/drone-games/blob/main/.resources/TASK_5.md
* https://github.com/acsl-mipt/drone-games/blob/main/.resources/TASK_5_2.md

## Installation

Create catkin workspace for Clover packages:

```bash
mkdir -p ~/clover_ws/src
cd ~/clover_ws/
catkin_make
```

Clone Clover repo:

```bash
cd clover_ws/src
git clone https://github.com/CopterExpress/clover.git
```

Build `simple_offboard` target:

```bash
cd ~/clover_ws
catkin_make simple_offboard
catkin_make clover_generate_messages
```

## Running

Run services:

```bash
roslaunch main.launch
```

## Misc

Run simple_offboard:

```bash
roslaunch offboard.launch num:=X
```

Run 3 simple_offboard's:

```bash
roslaunch main.launch
```
