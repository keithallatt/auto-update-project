import errno
from http import client as http_lib
import json
import os
import shutil
import socket
from subprocess import *
import sys

system_arguments = sys.argv[1:]

output = print


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

local_code_repository = os.getcwd()+local_code_repository


def last_commit_id():
    return str(_json_variables.get("last update commit", "No Last Commit"))


def global_code_repository():
    return str(_json_variables["global code repository"])


def main_file():
    return str(_json_variables.get("main file", ""))


project_languages = []
project_language_extensions = []
try:
    project_languages = _json_variables.get("project languages", [])

    __project_language_extensions__ = _json_variables.get("language extensions")
    __project_language_extensions__ = dict(__project_language_extensions__)

    project_language_extensions = []

    for language in project_languages:
        project_language_extensions.append(
            list(__project_language_extensions__[language]))

    output("Project Languages", project_languages)
    output("Project Extensions", project_language_extensions)
except TypeError:
    output("Error occured, project languages not configured.")
    pass


"""
Detects whether or not there is an internet connection. 

If a HEAD request to google doesn't return a 'getaddrinfo()' error / 
'gaierror', the HEAD request made it to www.google.com and returned.
"""

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
    if local_code_repository.split("/")[-1] in os.listdir("."):
        output(local_code_repository+" exists")
        os.chdir(local_code_repository)

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
        output(local_code_repository+" does not exist")

        update_required = True

    # display if an update is required
    output("Update Available" if update_required else "Update Not Available")

    # If there was, update the property
    if update_required:
        _json_variables["last update commit"] = out.strip()
else:
    output("No Internet Connection")


# If the local code repository is not
if not(local_code_repository.split("/")[-1] in os.listdir(".")):
    os.makedirs(local_code_repository)
os.chdir(local_code_repository)


###############################################################################

output("Cleaning the directory...")
Popen(["git", "clean", "-df"], stdout=PIPE).wait()
output("Done.")

###############################################################################

output("Connected: "+str(connected_to_internet))
output("Update: "+str(update_required))

if connected_to_internet and update_required:
    # git pull of all the source
    Popen(["git", "pull"], stdout=PIPE).wait()
    Popen(["git", "checkout", "."], stdout=PIPE).wait()
    output("Git Pull Request to 'origin/master'")

    # check if it downloaded.
    # if it doesn't..
    if len(list(filter(lambda x: x[0] != ".", os.listdir(".")))) == 0:
        shutil.rmtree(str(os.getcwd()), ignore_errors=True)
        os.chdir(working_directory)

        # clone the whole repository after deleting.
        Popen(["git", "clone", global_code_repository()], stdout=PIPE).wait()

        os.chdir(local_code_repository)

# grab properties.json
os.chdir(working_directory)
if "properties.json" in os.listdir(local_code_repository):
    _json_variables_from_repo = \
        dict(json.loads("\n".join(
            open(local_code_repository+"/properties.json", "r").readlines())))
    for k, v in _json_variables_from_repo.items():
        output("Updated Property:", repr(k), ":", repr(v))
        _json_variables[k] = v
os.chdir(local_code_repository)

# recompile all the java files in-case
# they are compiled versions of the old code.
for f in os.listdir("."):
    # ends with .java but is not a file named '.java'
    if f.endswith(".java") and f != ".java":
        if main_file() == "":
            f_contents = "".join(open(f).readlines())
            if "public static void main(String[]" in f_contents:
                _json_variables["main file"] = f

        Popen(["javac", f], stdout=PIPE).wait()


###############################################################################

# Check if main file found.
if main_file() == "":
    output("Could not find main file.")
    exit(errno.ENOENT)  # No such file or directory
elif main_file() in os.listdir("."):
    output("Found main file:\t" + main_file())

    f_contents = open(main_file(), "r").readlines()

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

output("Updating JSON file.")
json_file = open(working_directory+"/properties.json", "w")
json_file.write(json.dumps(_json_variables, indent=4, sort_keys=True))
json_file.close()

# Run the project if main file found and updates went smoothly.
output("Running project.")

# if project is written in java
if main_file().endswith("java"):
    Popen(["java", main_file().replace(".java", "")], stdout=PIPE).wait()
if main_file().endswith("py"):
    py_ver = "python3"
    if "python2" in [to.lower() for to in project_languages]:
        py_ver = "python2"
    Popen(["python3", main_file()], stdout=PIPE).wait()

os.chdir(working_directory)
