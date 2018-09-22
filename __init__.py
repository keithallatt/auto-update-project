import subprocess
from subprocess import check_output
import os
import shutil
import json
import errno

# import sys
# system_arguments = sys.argv[1:]

_json_variables = dict(json.loads("\n".join(open("./properties.json", "r").readlines())))

current_working_directory = os.getcwd()


def last_commit_id():
    return str(_json_variables["last update commit"])


def local_code_repository():
    return str(_json_variables["local code repository"])


def global_code_repository():
    return str(_json_variables["global code repository"])


def main_file():
    return str(_json_variables.get("main file", ""))


OUTPUT = print

"""
Detects whether or not there is an internet connection. 

If a HEAD request to google doesn't return a 'getaddrinfo()' error / 'gaierror', the HEAD request made it to 
www.google.com and returned.
"""


def __have_internet__():
    import socket
    import http.client as http_lib

    # create connection
    conn = http_lib.HTTPConnection("www.google.com", timeout=5)
    try:
        # create a HEAD request
        conn.request("HEAD", "/")
        conn.close()
        return True
    except socket.gaierror:
        conn.close()
        return False


connected_to_internet = __have_internet__()

########################################################################################################################

"""
Find the last-update file, to know when the last update was.
"""
update_required = False

# no update if there is no internet
if connected_to_internet:
    # default value, changed when checking output
    out = last_commit_id()

    # if repo exists
    if local_code_repository().split("/")[-1] in os.listdir("."):
        OUTPUT(local_code_repository()+" exists")
        os.chdir(local_code_repository())

        # check if there was an update.
        subprocess.Popen(["git", "remote", "update"], stdout=subprocess.PIPE)

        out = check_output(["git", "status", "-uno"]).decode("utf-8")

        # OUTPUT log history
        OUTPUT("\n".join(out.split("\n")[0:2]))

        out = out.split("\n")[1]

        _json_variables["last update commit"] = \
            check_output(["git", "log", "--format=\"%H\"", "-n", "1"]).decode("utf-8").replace("\"", "")

        os.chdir("..")

        update_required = "Your branch is behind" in out

    # if repo doesn't exist, an update is required, there is no code.
    else:
        OUTPUT(local_code_repository()+" does not exist")

        update_required = True

    # display if an update is required
    OUTPUT("Update Available" if update_required else "Update Not Available")

    # If there was, update the property
    if update_required:
        _json_variables["last update commit"] = out


########################################################################################################################

#
if not(local_code_repository().split("/")[-1] in os.listdir(".")):
    os.makedirs(local_code_repository())
os.chdir(local_code_repository())


########################################################################################################################

OUTPUT("Cleaning the directory...")
subprocess.Popen(["git", "clean", "-df"], stdout=subprocess.PIPE).wait()
OUTPUT("Done.")

########################################################################################################################

if connected_to_internet and update_required:
    # git pull of all the source
    process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE)
    process.wait()
    process = subprocess.Popen(["git", "checkout", "."], stdout=subprocess.PIPE)
    process.wait()
    output = process.communicate()[0]

    # check if it downloaded.
    # if it doesn't..
    if len(list(filter(lambda x: x[0] != ".", os.listdir(".")))) == 0:
        shutil.rmtree(str(os.getcwd()), ignore_errors=True)
        os.chdir(current_working_directory)

        # clone the whole repository after deleting.
        subprocess.Popen(["git", "clone", global_code_repository()], stdout=subprocess.PIPE).wait()

        os.chdir(local_code_repository())

# grab properties.json
os.chdir(current_working_directory)
if "properties.json" in os.listdir(local_code_repository()):
    _json_variables_from_repo = \
        dict(json.loads("\n".join(open(local_code_repository()+"/properties.json", "r").readlines())))
    for k, v in _json_variables_from_repo.items():
        print("Updated Property:", repr(k), ":", repr(v))
        _json_variables[k] = v
os.chdir(local_code_repository())

# recompile all the java files in-case they are compiled versions of the old code.
for f in os.listdir("."):
    # ends with .java but is not a file named '.java'
    if f.endswith(".java") and f != ".java":
        if main_file() == "":
            f_contents = "\n".join(open(f).readlines())
            if "public static void main(String[]" in f_contents:
                MAIN_FILE = f

        subprocess.Popen(["javac", f], stdout=subprocess.PIPE).wait()


########################################################################################################################

# Check if main file found.
if main_file() == "":
    OUTPUT("Could not find main file.")
    exit(errno.ENOENT)  # No such file or directory
elif main_file() in os.listdir("."):
    OUTPUT("Found main file:\t" + main_file())
else:
    OUTPUT("Specified main file not in repo:\t"+main_file()+"?")
    exit(errno.ENOENT)  # No such file or directory

OUTPUT("Updating JSON file.")
json_file = open(current_working_directory+"/properties.json", "w")
json_file.write(json.dumps(_json_variables, indent=4, sort_keys=True))
json_file.close()

# Run the project if main file found and updates went smoothly.
OUTPUT("Running project.")
subprocess.Popen(["java", main_file().replace(".java", "")], stdout=subprocess.PIPE)
os.chdir(current_working_directory)
