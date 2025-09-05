import os
import subprocess
import time
from robot import run

# Path to your robot file
ROBOT_FILE = os.path.abspath("test.robot")

def run_robot():
    """Run the Robot Framework test file from Python"""
    result_code = run(ROBOT_FILE)
    print("Robot finished with code:", result_code)

if __name__ == "__main__":
    run_robot()
