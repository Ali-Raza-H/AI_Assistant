import subprocess

try:
    subprocess.check_output("firefox")
except Exception as e:
    print(f"Error: {e}")