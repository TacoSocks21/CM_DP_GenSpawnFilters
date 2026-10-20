"""
Rebuilds the 9 spawn filter datapacks from a copy of Cobblemon's own data folder
(common/src/main/resources/data/cobblemon in the Cobblemon repo).

Rules (matching how the Cobblemon 1.7 packs were built):
  - A spawn entry belongs to the generation of its species' national dex number...
  - ...unless it is a regional form/bias, which is moved to that region's generation:
      Alolan -> Gen 7, Galarian/Hisuian -> Gen 8, Paldean (incl. Paldean Tauros) -> Gen 9
  - Each pack gets its generation's entries in data/onlygen<N>/spawn_pool_world (its pack.mcmeta blocks
    Cobblemon's own spawn_pool_world).
  - Herd entries (spawn_pool_world/herds, added in Cobblemon 1.8) belong to the generation of the
    species the file is named after (0169_crobat_alpha.json -> Gen 2), else of the herd's leader(s);
    with only that pack installed, herd members from other generations are left out (no Zubat in a
    Gen 2 Crobat herd). If the leaders span generations (e.g. Eeveelution herds), each generation gets
    its own members.
  - Any species left with no spawns in its own generation (e.g. Smoochum, which only spawns in
    Jynx herds) gets its generation's members of those herds as a herd of their own.

Combining packs (mix-and-match) is handled by a spawn rule that every pack ships an identical copy of:
  - Each pack also ships a biome tag, spawnfilter:gen<N>_enabled, which only exists when that pack is installed.
  - data/spawnfilter/spawn_rules/generation_filter.json uses those tags to:
      * only allow habitat spawns (Cobblemon 1.8 habitat structures) from installed generations. Cobblemon 1.8.2
        only shows a rule the species of a habitat spawn (its ID, "habitat_cobblemon:vulpix"), not its form, so a
        species that habitats spawn in more than one generation's form (Vulpix and Alolan Vulpix) needs all of
        those generations installed. Species that habitats only spawn in one form (Alolan Geodude) are exact.
        Anything else about a habitat spawn reads as 0 to a rule and crashes the game, so the rule must not use it.
      * pick the right version of every herd that mixes generations. All versions of those herds are in
        data/spawnfilter/spawn_pool_world/herds in every pack, and the rule only allows the one matching the
        installed generations (Gen 2 alone: just the Alpha Crobat; Gen 1 + 2: Cobblemon's own Crobat herd).
  - Before anything is written, the rule is checked against every combination of installed generations.

Output is always written with LF line endings; unchanged files are copied as-is.

Usage:
  python generate_spawn_filters.py <cobblemon data dir> <pack folder pattern>
  e.g. python generate_spawn_filters.py ../cobblemon/common/src/main/resources/data/cobblemon "SpawnFilter_Gen{gen}_Cobblemon1.8.2_v2.0"
"""
import itertools
import json
import os
import re
import sys

GENS = range(1, 10)
SHARED = "spawnfilter"  # namespace for the files every pack has an identical copy of

REGION_GEN = {
    "alolan": 7, "region_bias=alola": 7, "alolabias": 7,
    "galarian": 8, "region_bias=galar": 8, "galarbias": 8,
    "hisuian": 8, "region_bias=hisui": 8, "hisuibias": 8,
    "paldean": 9,
}
HABITAT_ID = "habitat_"  # Cobblemon names every habitat spawn "habitat_<namespace>:<species>"
VARIANT_ID = "__sf."  # Mixed-gen herd versions are named "<herd id>__sf.in1.in2.out4." (installed/missing gens)


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
    os.makedirs(os.path.dirname(path), exist_ok=True)
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


def herd_part(spawn, members, gens):
    """The herd entry with only the given generations' members, or None if none of them can spawn."""
    kept = [m for m, g in members if g in gens]
    if not any(m.get("isLeader", False) or m.get("isFollower", True) for m in kept):
        return None
    return {**spawn, "herdablePokemon": kept}


def load_habitat_entries(habitat_dir, species_gens):
    """Every habitat pool entry as (pool name, species, generation of the form it spawns)."""
    entries = []
    for filename in sorted(os.listdir(habitat_dir)):
        if filename.endswith(".json"):
            for spawn in read_json(os.path.join(habitat_dir, filename))[1]["spawns"]:
                species = re.sub(r"[^a-z0-9]", "", spawn["species"].lower().split(":")[-1])
                modifiers = (spawn.get("modifiers") or "").split()
                entries.append((filename[:-len(".json")], species, pokemon_gen(" ".join([species] + modifiers), species_gens)))
    return entries


def habitat_requirements(species_gens, habitat_entries):
    """Which generations must be installed for a habitat to spawn each species: every generation whose form of it
    a habitat spawns (a rule can't tell the forms apart), or its own generation if no habitat spawns it."""
    required = {}
    for _, species, gen in habitat_entries:
        required.setdefault(species, set()).add(gen)
    return {s: required.get(s, {g}) for s, g in species_gens.items()}


def species_in(spawn):
    if "herdablePokemon" in spawn:
        return [m["pokemon"] for m in spawn["herdablePokemon"]]
    return [spawn["pokemon"]]


class Herd:
    """One herd entry from Cobblemon, with the generation(s) it belongs to on its own."""

    def __init__(self, rel_path, spawn, members, owners):
        self.rel_path = rel_path
        self.spawn = spawn
        self.members = members
        self.member_gens = {g for _, g in members}
        self.owners = owners

    @property
    def mixed(self):
        return len(self.member_gens) > 1

    def variants(self):
        """One version per combination of installed generations that includes an owner: (gens, entry)."""
        for size in range(1, len(self.member_gens) + 1):
            for gens in itertools.combinations(sorted(self.member_gens), size):
                gens = set(gens)
                part = herd_part(self.spawn, self.members, gens) if gens & self.owners else None
                if part:
                    suffix = "".join(f"in{g}." for g in sorted(gens)) + "".join(f"out{g}." for g in sorted(self.member_gens - gens))
                    yield gens, {**part, "id": self.spawn["id"] + VARIANT_ID + suffix}


def gen_enabled(gen):
    return f"v.spawnable_position.biome.is_in('#{SHARED}:gen{gen}_enabled')"


def contains(text, search):
    return f"q.is_included({text}, {search})"


def quoted(text):
    return f"'{text}'"


def habitat_allow(requirements):
    # The species as a space-padded word: "habitat_cobblemon:vulpix" -> " vulpix ", so it only matches whole names
    # (porygon isn't found inside porygonz). Another namespace stays "habitat_<mod>:..." and matches nothing.
    species = f"q.replace('# ', '#', q.replace(v.spawn_detail.id, {quoted(HABITAT_ID + 'cobblemon:')}, ' '))"

    def word_list(names):
        return quoted(" " + " ".join(sorted(names)) + " ")  # Space-separated: Cobblemon's own Molang strings use spaces

    known = contains(word_list(requirements), species)  # Unknown species are blocked
    needs = [f"(!({contains(word_list(s for s, gens in requirements.items() if g in gens), species)}) || {gen_enabled(g)})"
             for g in GENS]
    return " && ".join([known] + needs)


def herd_variant_allow():
    spawn_id = "v.spawn_detail.id"
    return " && ".join(
        f"(!({contains(spawn_id, quoted(f'.in{g}.'))}) || {gen_enabled(g)})"
        f" && (!({contains(spawn_id, quoted(f'.out{g}.'))}) || !({gen_enabled(g)}))"
        for g in GENS
    )


def generation_rule(requirements):
    spawn_id = "v.spawn_detail.id"
    return {
        "displayName": "Cobblemon Spawn Filters: only spawn Pokemon from installed generations",
        "enabled": True,
        "components": [
            {"type": "filter", "spawnDetailSelector": contains(spawn_id, quoted(HABITAT_ID)), "allow": habitat_allow(requirements)},
            {"type": "filter", "spawnDetailSelector": contains(spawn_id, quoted(VARIANT_ID)), "allow": herd_variant_allow()},
        ],
    }


def enabled_tag():
    # Every biome, so the tag's existence alone says the pack is installed
    return {"replace": False, "values": [
        "#minecraft:is_overworld", "#minecraft:is_nether", "#minecraft:is_end",
        {"id": "#c:is_overworld", "required": False},
        {"id": "#c:is_nether", "required": False},
        {"id": "#c:is_end", "required": False},
    ]}


def compile_molang(expression):
    """Turns one of the generated Molang expressions into Python, to check the rule without starting Minecraft."""
    assert "!=" not in expression
    # Only use values Cobblemon is known to fill in for every spawn. A missing one reads as the number 0, and a
    # q.* function handed a number instead of text throws, which crashes the game (habitat spawns in 1.8.2 have
    # no v.spawn_detail.pokemon, for one).
    used = set(re.findall(r"\b[qv]\.[a-z_.]+", expression))
    assert used <= {"q.is_included", "q.replace", "v.spawn_detail.id", "v.spawnable_position.biome.is_in"}, used
    python = re.sub(rf"v\.spawnable_position\.biome\.is_in\('#{SHARED}:gen(\d)_enabled'\)", r"enabled(\1)", expression)
    for molang, replacement in [
        ("q.is_included(", "contains("), ("q.replace(", "replace("), ("v.spawn_detail.id", "spawn_id"),
        ("&&", " and "), ("||", " or "), ("!", " not "),
    ]:
        python = python.replace(molang, replacement)
    assert "v." not in python and "q." not in python, python[:200]
    return compile(python, "<rule>", "eval")


def check_rule(rule, requirements, herds, root_ids, habitat_entries):
    """Simulates the rule for every combination of installed generations and raises if anything is off."""
    habitat, variant = rule["components"]
    habitat_selector, habitat_allowed = compile_molang(habitat["spawnDetailSelector"]), compile_molang(habitat["allow"])
    variant_selector, variant_allowed = compile_molang(variant["spawnDetailSelector"]), compile_molang(variant["allow"])

    def run(code, installed, spawn_id):
        return bool(eval(code, {"__builtins__": {}}, {
            "enabled": installed.__contains__, "contains": lambda text, search: search in text,
            "replace": lambda text, search, replacement: text.replace(search, replacement), "spawn_id": spawn_id,
        }))

    # Every species (not only the ones Cobblemon's habitats use) in every form habitats spawn it in
    entries = {(s, g) for s, gens in requirements.items() for g in gens}
    assert {(s, g) for _, s, g in habitat_entries} <= entries
    variants = {h: list(h.variants()) for h in herds if h.mixed}

    # Each component must only pick out its own spawns; regular spawns and single-gen herds are left alone
    for spawn_id in root_ids + [h.spawn["id"] for h in herds if not h.mixed]:
        assert not run(habitat_selector, set(), spawn_id) and not run(variant_selector, set(), spawn_id), spawn_id
    for species, _ in entries:
        spawn_id = f"{HABITAT_ID}cobblemon:{species}"
        assert run(habitat_selector, set(), spawn_id) and not run(variant_selector, set(), spawn_id), spawn_id
    for versions in variants.values():
        for _, v in versions:
            assert run(variant_selector, set(), v["id"]) and not run(habitat_selector, set(), v["id"]), v["id"]
    # Unknown species and other mods' species are blocked even with everything installed
    for spawn_id in (f"{HABITAT_ID}cobblemon:missingno", f"{HABITAT_ID}othermod:vulpix", f"{HABITAT_ID}cobblemon:"):
        assert not run(habitat_allowed, set(GENS), spawn_id), spawn_id

    for size in range(1, 10):
        for installed in map(set, itertools.combinations(GENS, size)):
            for species, gen in entries:
                allowed = run(habitat_allowed, installed, f"{HABITAT_ID}cobblemon:{species}")
                assert allowed == (requirements[species] <= installed), (species, installed)
                assert not allowed or gen in installed, (species, gen, installed)  # Never another generation's form

            for herd, versions in variants.items():
                active = [(gens, v) for gens, v in versions if run(variant_allowed, installed, v["id"])]
                expected = herd_part(herd.spawn, herd.members, herd.member_gens & installed) if herd.owners & installed else None
                if expected is None:
                    assert not active, (herd.spawn["id"], installed)
                else:
                    assert len(active) == 1 and active[0][0] <= installed, (herd.spawn["id"], installed)
                    assert {**active[0][1], "id": herd.spawn["id"]} == expected, (herd.spawn["id"], installed)
                if len(installed) == 9 and herd.owners:
                    assert {**active[0][1], "id": herd.spawn["id"]} == herd.spawn  # Cobblemon's own herd, exactly once
    print(f"Rule checked against all 511 combinations of installed generations "
          f"({len(entries)} habitat species/forms, {sum(map(len, variants.values()))} herd versions)")


def main(data_dir, pack_pattern):
    species_gens = load_species_gens(os.path.join(data_dir, "species"))
    src_dir = os.path.join(data_dir, "spawn_pool_world")
    sources = {}  # relative path -> (source text, data, indent)
    placed = {gen: {} for gen in GENS}  # gen -> relative path -> spawns, for regular spawn files
    herds = []

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
                    owners = {g for g in herd_owner_gens(members, file_species) if herd_part(spawn, members, {g})}
                    herds.append(Herd(rel_path, spawn, members, owners))
            else:
                for gen, spawns in split_root_file(data, species_gens).items():
                    placed[gen][rel_path] = spawns

    # A species that only spawns inside another generation's herds (e.g. Smoochum, which in 1.8 only spawns in
    # Jynx herds) would vanish from its own pack, so give its generation those herds' same-gen members.
    # Regular herds are preferred over alpha herds, so this doesn't create alpha-less "boss" herds.
    covered = {(p.split()[0], gen) for gen, files in placed.items() for spawns in files.values()
               for spawn in spawns for p in species_in(spawn)}
    covered |= {(m["pokemon"].split()[0], g) for h in herds for m, g in h.members if g in h.owners}
    missing = {(m["pokemon"].split()[0], g) for h in herds for m, g in h.members} - covered
    for alpha in (False, True):
        rescued = set()
        for herd in herds:
            if herd.rel_path.endswith("_alpha.json") != alpha:
                continue
            for gen in sorted(herd.member_gens - herd.owners):
                needs = {m["pokemon"].split()[0] for m, g in herd.members if g == gen} & {s for s, g in missing if g == gen}
                if needs and herd_part(herd.spawn, herd.members, {gen}):
                    herd.owners.add(gen)
                    rescued |= {(s, gen) for s in needs}
                    print(f"Gen {gen}: added {sorted(needs)} herd from {herd.rel_path} ({herd.spawn['id']}), since they spawn nowhere else")
        missing -= rescued

    shared_herds = {}  # relative path -> spawns: every version of the herds that mix generations
    for herd in herds:
        if herd.mixed:
            shared_herds.setdefault(herd.rel_path, []).extend(v for _, v in herd.variants())
        elif herd.owners:
            placed[herd.owners.copy().pop()].setdefault(herd.rel_path, []).append(herd.spawn)

    habitat_dir = os.path.join(data_dir, "habitat_pools")
    habitat_entries = load_habitat_entries(habitat_dir, species_gens) if os.path.isdir(habitat_dir) else []
    requirements = habitat_requirements(species_gens, habitat_entries)
    rule = generation_rule(requirements)
    root_ids = [s["id"] for files in placed.values() for spawns in files.values() for s in spawns if "herdablePokemon" not in s]
    check_rule(rule, requirements, herds, root_ids, habitat_entries)

    pools = {}
    for pool, species, _ in habitat_entries:
        pools.setdefault(pool, set()).add(species)
    for species, gens in sorted(requirements.items()):
        if len(gens) > 1:
            print(f"Habitats: {species} needs gens {sorted(gens)} (spawns in more than one generation's form)")
    print("Habitats left empty with one pack: " + ", ".join(
        f"Gen {g}: {sum(not any(requirements[s] <= {g} for s in found) for found in pools.values())}/{len(pools)}"
        for g in GENS))

    def output(rel_path, spawns):
        text, data, indent = sources[rel_path]
        return text if spawns == data["spawns"] else json.dumps({**data, "spawns": spawns}, indent=indent, ensure_ascii=False)

    shared_files = {os.path.join(SHARED, "spawn_pool_world", p): output(p, s) for p, s in shared_herds.items()}
    shared_files[os.path.join(SHARED, "spawn_rules", "generation_filter.json")] = json.dumps(rule, indent=2)

    for gen, files in placed.items():
        pack_data = os.path.join(pack_pattern.format(gen=gen), "data")
        # Clear out the old files but keep the folders themselves (OneDrive can refuse to delete synced folders)
        for folder in (os.path.join(pack_data, f"onlygen{gen}", "spawn_pool_world"), os.path.join(pack_data, SHARED)):
            for root, _, old_files in os.walk(folder):
                for old_file in old_files:
                    if old_file.endswith(".json"):
                        os.remove(os.path.join(root, old_file))
        for rel_path, spawns in files.items():
            write_text(os.path.join(pack_data, f"onlygen{gen}", "spawn_pool_world", rel_path), output(rel_path, spawns))
        for rel_path, text in shared_files.items():
            write_text(os.path.join(pack_data, rel_path), text)
        write_text(os.path.join(pack_data, SHARED, "tags", "worldgen", "biome", f"gen{gen}_enabled.json"),
                   json.dumps(enabled_tag(), indent=2))
        herd_files = sum(1 for p in files if p.startswith("herds"))
        print(f"Gen {gen}: {len(files) - herd_files} spawn files + {herd_files} herd files -> {pack_data}")
    print(f"All packs: {sum(map(len, shared_herds.values()))} versions of {sum(h.mixed for h in herds)} mixed-gen herds "
          f"in {len(shared_herds)} shared herd files, plus the generation_filter spawn rule")


if __name__ == "__main__":
    main(*sys.argv[1:3])
