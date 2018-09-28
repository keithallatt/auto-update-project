# AutoUpdateProject

This project is aimed at creating an interface, consisting of a python script and JSON file, that creates a local copy of an online repository, to then act as a class loader to run Java projects. The script may be ammended to work for C/C++ or Python projects.

This project relies on the functionality of git through the command line. In my example, the unix command `git clone https://github.com/keithallatt/repo` clones the repository into a local git repository on the users system, and `git pull` is used to gather any updates and apply them in the local git repository.

## Getting Started

This project is designed to be used anywhere where updates are frequent or for testing purposes. The python script makes no edits to the code downloaded from the git repository online, but simply downloads and runs the code.

### Prerequisites

* `git` must be installed.
* `python 3.*` must be installed.
* For any projects using Java, the appropriate JVM (Java Virtual Machine) must be properly installed.
* For any other languages used, appropriate compilers or interpreters must be installed.

**This information must be conveyed to the end users as well. Python and git are required by the system to function.**

*Note: Windows users may be able to use this project if unix commands are useable through the command line. Say, through the use of cygwin. Support is not guaranteed.*

### Installing

To implement into a working project, deploy the project as the `__init__.py` script with the appropriately completed `properties.json` file ([Wiki](https://github.com/keithallatt/AutoUpdateProject/wiki/JSON)). At the git repository specified in `properties.json`, the entire project, and only the project with any added documentation should be uploaded. Any new **stable** releases should be updated. 

### Support

For additional support, consider checking the project's wiki, or by creating an issue on this project. Be specific or fixes may not be able to be completed.

## Usage

### Standalone

This interface can be used as a standalone application, bundled into a .app or .exe file or ran as a python script, with an appropriately filled out JSON file and online git repository. This is recommended for projects with graphical user interfaces or headless programs that require no input or can rely on command line arguments.

  ```ditaa {cmd=true args=["-E"]}
  +--------+   +-------+    +-------+
  |        | --+ ditaa +--> |       |
  |  Text  |   +-------+    |diagram|
  |Document|   |!magic!|    |       |
  |     {d}|   |       |    |       |
  +---+----+   +-------+    +-------+
      :                         ^
      |       Lots of work      |
      +-------------------------+
  ```

### From the command line

For any project that relies heavily on command line input and output, or runs in the background, or for a project that just needs an update manager, this route works better. Using the command line, command line arguments can control how the program is used, for example, running headless and/or without running the program after the update is complete.


