import errno
from http import client as http_lib
import json
import os
from pathlib import *
import shutil
import socket
from subprocess import *
from tkinter import ttk
from tkinter import *
import time
import sys

system_arguments = sys.argv[1:]


def output(*args):
    splash_screen.text.config(state=NORMAL)
    splash_screen.text.insert(END, " ".join([str(a) for a in args]) + "\n")
    splash_screen.text.see(END)
    splash_screen.text.config(state=DISABLED)


loading_bar_max = 12


class SplashScreen:
    """
        Creates a splash screen with a loading bar, with a percentage loaded.

        The percentage is based off how many 'increment_loading' calls have
        been made.
    """
    def __init__(self, master):
        self.master = master
        master.title("Loading")

        self.label = Label(master,
                           text="Loading", width=30, height=3)
        self.label.pack()

        self.mpb = ttk.Progressbar(master, orient="horizontal", length=300,
                                   mode="determinate")
        self.mpb.pack()
        self.mpb["maximum"] = loading_bar_max
        self.mpb["value"] = 0

        self.percentage_done = Label(master, text="0%", width=30, height=3)
        self.percentage_done.pack()

        self.scroll = Scrollbar(master)
        self.text = Text(master, height=8, width=80)

        self.scroll.pack(side=RIGHT, fill=Y)
        self.text.pack(side=LEFT, fill=Y)
        self.scroll.config(command=self.text.yview)
        self.text.config(yscrollcommand=self.scroll.set)

        self.text.pack()


root = Tk()

w = 550  # width for the Tk root
h = 700  # height for the Tk root

# calculate x and y coordinates for the Tk root window
x = (root.winfo_screenwidth() - w) / 2
y = (root.winfo_screenheight() - h - 200) / 2

# set the dimensions of the screen
# and where it is placed
root.geometry('%dx%d+%d+%d' % (w, h, x, y))

splash_screen = SplashScreen(root)
root.update()
root.update_idletasks()


def increment_loading(text_change: str=None,
                      delay: float = 0,
                      update_to_full: bool=False):
    """
    Increment loading bar by one step (or to completion) to reflect how many
    steps have been taken to load the program.

    :param text_change:
        What text to display on the splash screen, if any, for a specific
        section of code being executed.
    :param update_to_full:
        Whether or not to update to a full progress bar.
    :param delay:
        How much to delay the function by, in seconds.
    """
    splash_screen.mpb["value"] += 1
    if update_to_full:
        splash_screen.mpb["value"] = splash_screen.mpb["maximum"]
    if splash_screen.mpb["value"] > splash_screen.mpb["maximum"]:
        sys.stderr.print("Loading Bar Value Exceeded Maximum")
        exit(1)
    if not (text_change is None):
        splash_screen.label.config(text=text_change)
    splash_screen.percentage_done.config(
        text=str((splash_screen.mpb["value"] * 100) //
                 splash_screen.mpb["maximum"])+"%")

    root.update()
    root.update_idletasks()
    time.sleep(delay)


increment_loading("Updating Properties.")
if not ("properties.json" in os.listdir(".")):
    output("File './properties.json' does not exist:")
    exit(errno.ENOENT)  # No such file or directory

properties_file = open("./properties.json", "r")

_json_variables = dict(json.loads("".join(properties_file.readlines())))

working_directory = os.getcwd()

local_code_repository = (str(_json_variables["local code repository"]))

if local_code_repository.startswith(".."):
    output("File Path Not Formatted Correctly")
    exit(errno.EFTYPE)  # Find write errno code
if not local_code_repository.startswith("."):
    if local_code_repository.startswith("/"):
        local_code_repository = "."+local_code_repository
    else:
        local_code_repository = "./" + local_code_repository

local_code_repository = local_code_repository[1:]

local_code_repository = Path(os.getcwd()+local_code_repository)


def last_commit_id():
    """ Return the last commit ID from the git repository """
    return str(_json_variables.get("last update commit", "No Last Commit"))


def global_code_repository():
    """ Return the url for the online git repository """
    try:
        return str(_json_variables["global code repository"])
    except KeyError:
        output("No global repository specified")
        exit(errno.EINVAL)  # Invalid argument


def main_file():
    """ Return the file path for the main file """
    return str(_json_variables.get("main file", ""))


"""
Detects whether or not there is an internet connection. 

If a HEAD request to google doesn't return a 'getaddrinfo()' error / 
'gaierror', the HEAD request made it to www.google.com and returned.
"""

increment_loading("Checking Internet.")
# create connection
conn = http_lib.HTTPConnection("www.google.com", timeout=5)
try:
    # create a HEAD request
    conn.request("HEAD", "/")
    connected_to_internet = True
except socket.gaierror or socket.timeout:
    connected_to_internet = False
finally:
    conn.close()


update_required = False

# no update if there is no internet
if connected_to_internet:
    output("Connected to internet.")
    # default value, changed when checking output
    out = last_commit_id()

    # if the repository exists
    if local_code_repository.name in os.listdir("."):
        output(local_code_repository, "exists")
        os.chdir(local_code_repository.absolute())

        increment_loading("Updating remotes.")
        # Fetch updates for remotes or remote groups in the
        # repository as defined by remotes.
        Popen(["git", "remote", "update"], stdout=PIPE).wait()

        # git status -uno -> untracked files: mode = no,
        # Show no untracked files.
        out = check_output(["git", "status"]).decode("utf-8")

        # output log history
        output("\n".join(out.split("\n")[:10])+"\t.\n\t.\n\t.\n")

        out = out.split("\n")[1]

        _json_variables["last update commit"] = \
            check_output(["git", "log", "--format=\"%H\"", "-n", "1"])\
            .decode("utf-8").replace("\"", "")

        os.chdir("..")

        update_required = "Your branch is behind" in out

    # if repo doesn't exist, an update is required, there is no code.
    else:
        output(local_code_repository, "does not exist")
        increment_loading()
        update_required = True

    # display if an update is required
    output("Update Available" if update_required else "Update Not Available")

    # If there was, update the property
    if update_required:
        _json_variables["last update commit"] = out.strip()
else:
    output("No Internet Connection")


# If the local code repository is not
if not(local_code_repository.name in os.listdir(".")):
    os.makedirs(local_code_repository.absolute())
os.chdir(local_code_repository.absolute())


increment_loading("Cleaning the local directory.")
output("Cleaning the directory...")
Popen(["git", "clean", "-df"], stdout=PIPE).wait()
output("Done.")


output("Connected: "+str(connected_to_internet))
output("Update: "+str(update_required))

if connected_to_internet and update_required:
    increment_loading("Updating from git.")
    # git pull of all the source
    Popen(["git", "pull"], stdout=PIPE).wait()
    Popen(["git", "checkout", "."], stdout=PIPE).wait()
    output("Git Pull Request to 'origin/master'")

    # check if it downloaded.
    # if it doesn't..
    if len(list(filter(lambda _x: _x[0] != ".", os.listdir(".")))) == 0:
        shutil.rmtree(str(os.getcwd()), ignore_errors=True)
        os.chdir(working_directory)

        increment_loading("Cloning the repository.")
        # clone the whole repository after deleting.
        Popen(["git", "clone", global_code_repository()], stdout=PIPE).wait()

        os.chdir(local_code_repository.absolute())
    else:
        increment_loading()
else:
    increment_loading()


project_languages = []
project_language_extensions = []
try:
    increment_loading("Checking project languages.")
    project_languages = _json_variables.get("project languages", [])

    __project_language_extensions__ = _json_variables.get(
        "language extensions")
    __project_language_extensions__ = dict(__project_language_extensions__)

    project_language_extensions = []

    for language in project_languages:
        project_language_extensions.append(
            list(__project_language_extensions__[language]))

    project_language_extensions = sum(project_language_extensions, [])

    output("Project Languages", project_languages)
    output("Project Extensions", project_language_extensions)
except TypeError:
    output("Error occurred, project languages not configured.")
    pass

# grab properties.json
os.chdir(working_directory)
if "properties.json" in local_code_repository.iterdir():
    increment_loading("Updating properties from git.")
    _json_variables_from_repo = \
        dict(json.loads("\n".join(
            open(local_code_repository / "properties.json", "r").readlines())))
    for k, v in _json_variables_from_repo.items():
        output("Updated Property:", repr(k), ":", repr(v))
        _json_variables[k] = v
else:
    increment_loading()
os.chdir(local_code_repository.absolute())


increment_loading("Compiling code.")
# recompile all the java files in-case
# they are compiled versions of the old code.
for f in os.listdir("."):
    # java file.
    if f.endswith(".java") and f != ".java":
        if main_file() == "":
            f_contents = "".join(open(f).readlines())
            if "public static void main(String[]" in f_contents:
                _json_variables["main file"] = f

        Popen(["javac", f], stdout=PIPE).wait()
    # python file.
    if f.endswith(".py") and f != ".py":
        if main_file() == "":
            f_contents = "".join(open(f).readlines())
            if "if __name__ == '__main__':" in f_contents:
                _json_variables["main file"] = f


# Check if main file found.
if main_file() == "":
    output("Could not find main file.")
    exit(errno.ENOENT)  # No such file or directory
elif main_file() in os.listdir("."):
    output("Found main file:\t" + main_file())

    f_contents = open(main_file(), "r").readlines()

    if len(f_contents) > 15:
        line_end = min(21, len(f_contents))
        line_divide = line_end-3
        while len(f_contents) > line_end:
            f_contents.pop(line_divide)
        f_contents[line_divide] = "\t.\n\t.\n\t.\n"
    f_contents = "".join(f_contents)

    output("\n\n"+f_contents+"\n\n")
else:
    output("Specified main file not in local repository:\t"+main_file()+"?")
    exit(errno.ENOENT)  # No such file or directory

increment_loading("Updating file system.")
output("Updating JSON file.")
json_file = open(working_directory+"/properties.json", "w")
json_file.write(json.dumps(_json_variables, indent=4, sort_keys=True))
json_file.close()

# Run the project if main file found and updates went smoothly.
output("Running project.")
increment_loading("Running the project.", update_to_full=True, delay=0.5)
splash_screen.master.withdraw()
root.update()
root.update_idletasks()

# if project is written in java
if main_file().endswith("java"):
    Popen(["java", main_file().replace(".java", "")], stdout=PIPE).wait()
if main_file().endswith("py"):
    py_ver = "python3"
    if "python2" in [to.lower() for to in project_languages]:
        py_ver = "python2"
    Popen([py_ver, main_file()], stdout=PIPE).wait()

os.chdir(working_directory)
