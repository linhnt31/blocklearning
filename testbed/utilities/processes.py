import subprocess

def run_and_output(command):
  p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
  # Interact with process: Send data to stdin. Read data from stdout and stderr
  (stdout, stderr) = p.communicate()
  p_status = p.wait()

  if p_status != 0:
    print(stderr)
    exit(p_status)

  return stdout.decode()
