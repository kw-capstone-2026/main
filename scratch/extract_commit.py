import subprocess

commits = {
    "LOG1": "3cb3fc8dfc1cc154f4bc85ae325f83adba98a32e",
    "LOG2": "f9c917683254b74896e6ca96258f24fe70d1e322",
    "LOG3": "12ad5d09564898c4e296472196f3d3570c183f3b",
    "LOG4": "fb92549e0443bdf3dfd1e70661294eccdb2cf1bc",
    "LOG5": "a349c4bf018c55804b794ba67522713b67346e5f"
}

for name, commit in commits.items():
    try:
        content = subprocess.check_output(f"git show {commit}:src/feature_merger.py", shell=True)
        filename = f"scratch/feature_merger_{name}.py"
        with open(filename, "wb") as f:
            f.write(content)
        print(f"Extracted {name} to {filename}")
    except Exception as e:
        print(f"Error for {name}: {e}")
