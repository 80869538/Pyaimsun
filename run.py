import subprocess
import config
import platform
import os.path as osp
import os
import sys

# path to the Aimsun_Next binary
if platform.system() == 'Darwin':  # OS X
    binary_name = 'Aimsun Next'
elif config.CONSOLE_MODE:
    binary_name = "aconsole.exe"
else:
    binary_name = 'Aimsun Next.exe'

aimsun_path = osp.join(osp.expanduser(config.AIMSUN_NEXT_PATH),
                        binary_name)

script_path = osp.join(config.PROJECT_PATH, "core", "load.py")


# start the aimsun process
aimsun_call = [aimsun_path, "-script", script_path, str(config.PORT), config.PROJECT_PATH]
aimsun_proc = subprocess.run(aimsun_call, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

