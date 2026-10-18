"""
Rebuilds each generation's spawn_pool_world folder from a copy of Cobblemon's own
spawn_pool_world folder (common/src/main/resources/data/cobblemon/spawn_pool_world).

Rules (matching how the Cobblemon 1.7 packs were built):
  - A spawn entry belongs to the generation of its species' national dex number...
  - ...unless it is a regional form/bias, which is moved to that region's generation:
      Alolan -> Gen 7, Galarian/Hisuian -> Gen 8, Paldean (incl. Paldean Tauros) -> Gen 9
  - Herd entries (spawn_pool_world/herds, added in Cobblemon 1.8) belong to the generation of the
    species the file is named after (0169_crobat_alpha.json -> Gen 2), else of the herd's leader(s);
    herd members from other generations are removed from that herd (no Zubat in a Gen 2 Crobat herd).
    If the leaders span generations (e.g. Eeveelution herds), each generation gets its own members.
  - Any species left with no spawns in its own generation (e.g. Smoochum, which only spawns in
    Jynx herds) gets its generation's members of those herds as a herd of their own.

Output is always written with LF line endings; unchanged files are copied as-is.

Usage:
  python generate_spawn_filters.py <cobblemon spawn_pool_world dir> <cobblemon species dir> <pack folder pattern>
  e.g. python generate_spawn_filters.py ../cobblemon/.../spawn_pool_world ../cobblemon/.../species "SpawnFilter_Gen{gen}_Cobblemon1.8.2_v2.0"
"""
import json
import os
import re
import sys

REGION_GEN = {
    "alolan": 7, "region_bias=alola": 7, "alolabias": 7,
    "galarian": 8, "region_bias=galar": 8, "galarbias": 8,
    "hisuian": 8, "region_bias=hisui": 8, "hisuibias": 8,
    "paldean": 9,
}


def load_species_gens(species_dir):
    gens = {}
    for folder in os.listdir(species_dir):
        gen = int(re.match(r"generation(\d)", folder).group(1))
        for filename in os.listdir(os.path.join(species_dir, folder)):
            gens[filename[:-len(".json")]] = gen
    return gens


def pokemon_gen(pokemon, species_gens):
    species, *aspects = pokemon.split()
    for aspect in aspects:
        if aspect in REGION_GEN:
            return REGION_GEN[aspect]
        if aspect.startswith("bull_breed="):
            return 9
    return species_gens[species]


def read_json(path):
    with open(path, encoding="utf-8-sig") as f:
        text = f.read()  # universal newlines: CRLF from a Windows git checkout becomes LF
    indent = len(re.search(r"\n([ \t]*)\"", text).group(1))
    return text, json.loads(text), indent


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def split_root_file(data, species_gens):
    by_gen = {}
    for spawn in data["spawns"]:
        if spawn["type"] != "pokemon":
            continue
        by_gen.setdefault(pokemon_gen(spawn["pokemon"], species_gens), []).append(spawn)
    return by_gen


def herd_owner_gens(members, file_species):
    """Which generation(s) a herd belongs to: the species the file is named after, else its leader(s), else everyone."""
    named = {g for m, g in members if m["pokemon"].split()[0] in file_species}
    if len(named) == 1:
        return named
    leaders = {g for m, g in members if m.get("isLeader", False)}
    if len(leaders) == 1:
        return leaders
    return {g for _, g in members}


def herd_part(spawn, members, gen):
    """The herd entry with only the given generation's members, or None if none of them can spawn."""
    kept = [m for m, g in members if g == gen]
    if not any(m.get("isLeader", False) or m.get("isFollower", True) for m in kept):
        return None
    return {**spawn, "herdablePokemon": kept}


def species_in(spawn):
    if "herdablePokemon" in spawn:
        return [m["pokemon"] for m in spawn["herdablePokemon"]]
    return [spawn["pokemon"]]


def main(src_dir, species_dir, pack_pattern):
    species_gens = load_species_gens(species_dir)
    sources = {}  # relative path -> (source text, data, indent)
    placed = {gen: {} for gen in range(1, 10)}  # gen -> relative path -> spawns
    herd_entries = []  # (relative path, spawn, members) for the rescue pass below

    for root, _, files in os.walk(src_dir):
        rel_dir = os.path.relpath(root, src_dir)
        for filename in sorted(files):
            if not filename.endswith(".json"):
                continue
            text, data, indent = read_json(os.path.join(root, filename))
            if data.get("enabled", True) is False:
                continue
            rel_path = filename if rel_dir == "." else os.path.join(rel_dir, filename)
            sources[rel_path] = (text, data, indent)
            if rel_dir == "herds":
                file_species = set(re.findall(r"[a-z]+", filename[:-len(".json")])) & species_gens.keys()
                for spawn in data["spawns"]:
                    members = [(m, pokemon_gen(m["pokemon"], species_gens)) for m in spawn["herdablePokemon"]]
                    herd_entries.append((rel_path, spawn, members))
                    for gen in herd_owner_gens(members, file_species):
                        part = herd_part(spawn, members, gen)
                        if part:
                            placed[gen].setdefault(rel_path, []).append(part)
            else:
                for gen, spawns in split_root_file(data, species_gens).items():
                    placed[gen][rel_path] = spawns

    # A species that only spawns inside another generation's herds (e.g. Smoochum, which in 1.8 only spawns in
    # Jynx herds) would vanish from its own pack, so give its generation those herds' same-gen members.
    # Regular herds are preferred over alpha herds, so this doesn't create alpha-less "boss" herds.
    covered = {(p.split()[0], gen) for gen, files in placed.items()
               for spawns in files.values() for spawn in spawns for p in species_in(spawn)}
    missing = {(m["pokemon"].split()[0], g) for _, _, members in herd_entries for m, g in members} - covered
    for alpha in (False, True):
        rescued = set()
        for rel_path, spawn, members in herd_entries:
            if rel_path.endswith("_alpha.json") != alpha:
                continue
            for gen in sorted({g for _, g in members}):
                needs = {m["pokemon"].split()[0] for m, g in members if g == gen} & {s for s, g in missing if g == gen}
                part = herd_part(spawn, members, gen) if needs else None
                if part and part not in placed[gen].get(rel_path, []):
                    placed[gen].setdefault(rel_path, []).append(part)
                    rescued |= {(s, gen) for s in needs}
                    print(f"Gen {gen}: added {sorted(needs)} herd from {rel_path} ({spawn['id']}), since they spawn nowhere else")
        missing -= rescued

    outputs = {gen: {} for gen in range(1, 10)}  # gen -> relative path -> (source text, data, indent, changed)
    for gen, files in placed.items():
        for rel_path, spawns in files.items():
            text, data, indent = sources[rel_path]
            outputs[gen][rel_path] = (text, {**data, "spawns": spawns}, indent, spawns != data["spawns"])

    for gen, files in outputs.items():
        pack = pack_pattern.format(gen=gen)
        out_dir = os.path.join(pack, "data", f"onlygen{gen}", "spawn_pool_world")
        # Clear out the old files but keep the folder itself (OneDrive can refuse to delete synced folders)
        for root, _, old_files in os.walk(out_dir):
            for old_file in old_files:
                if old_file.endswith(".json"):
                    os.remove(os.path.join(root, old_file))
        for rel_path, (text, data, indent, changed) in files.items():
            path = os.path.join(out_dir, rel_path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            write_text(path, json.dumps(data, indent=indent, ensure_ascii=False) if changed else text)
        herds = sum(1 for p in files if p.startswith("herds"))
        print(f"Gen {gen}: {len(files) - herds} spawn files + {herds} herd files -> {out_dir}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
