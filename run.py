import subprocess
import config
import platform
import os.path as osp


# path to the Aimsun_Next binary
if platform.system() == 'Darwin':  # OS X
    binary_name = 'Aimsun Next'
else:
    binary_name = 'Aimsun Next.exe'

aimsun_path = osp.join(osp.expanduser(config.AIMSUN_NEXT_PATH),
                        binary_name)

script_path = osp.join(config.PROJECT_PATH, "core", "load.py")


# start the aimsun process
aimsun_call = [aimsun_path, "-script", script_path, str(config.PORT), config.PROJECT_PATH]

aimsun_proc = subprocess.run(aimsun_call, check=True, capture_output=True).stdout