import os

cobblemonVersion = "1.8.2"
datapackVersion = "2.0"
genNum = "1"
dir1 = f".\SpawnFilter_Gen{genNum}_Cobblemon{cobblemonVersion}_v{datapackVersion}\data\onlygen{genNum}\spawn_pool_world"
dir2 = ".\COBBLEVERSE-DP-v28\data\cobblemon\spawn_pool_world"

mismatches = []

for filename in os.listdir(dir1):
    if filename.endswith(".json"):
        file1_path = os.path.join(dir1, filename)
        file2_path = os.path.join(dir2, filename)

        if not os.path.exists(file2_path):
            print("Shot and a miss...")
            continue

        with open(file1_path, "r") as f1, open(file2_path, "r") as f2:
            if f1.read() != f2.read():
                mismatches.append(filename)

print(f"Mismatched files for gen {genNum}:", mismatches)
