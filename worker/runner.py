import subprocess


def run_test():

    process = subprocess.Popen(
        [
            "pytest",
            "tests/test_demo.py",
            "-v",
            "-s"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout:
        print(line, end="")

    process.wait()

    return process.returncode
