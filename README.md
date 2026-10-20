# What it is...
Want to play with _only_ Pokémon from your favorite generation/s? You've come to the right place!

This datapack manipulates the spawning mechanics for Cobblemon by replacing the spawn files with only Pokémon from this generation.

**NOTE**: All regional-form spawns have been moved to their respective generations:
- Alolan = Gen 7
- Galarian = Gen 8
- Hisuian = Gen 8
- Paldean = Gen 9

## Requirements
| Minecraft | Cobblemon | Datapack |
|-----------|-----------|----------|
| 1.21.1    | 1.8.2     | v2.x     |
| 1.21.1    | 1.7.1     | v1.x     |

Older datapack versions are on the Versions tab of each Modrinth page.

## Mix and match!

Want to include multiple generations? Just add any number of my spawn-filtering datapacks to include them in the spawn pool. It's that easy!

For example, if you want a special playthrough of generations 1-4 (my favorite ones, by the way), just add all four datapacks to your world and you're all set.

Herds that mix generations combine automatically, too. With only Gen 2 installed, an Alpha Crobat shows up on its own, but install Gen 1 as well and it leads its usual herd of Zubat and Golbat.

- [Gen 1: Kanto](https://modrinth.com/datapack/cobblemon-spawn-filter-gen-1-kanto)
- [Gen 2: Johto](https://modrinth.com/datapack/cobblemon-spawn-filter-gen-2-johto)
- [Gen 3: Hoenn](https://modrinth.com/datapack/cobblemon-spawn-filter-gen-3-hoenn)
- [Gen 4: Sinnoh](https://modrinth.com/datapack/cobblemon-spawn-filter-gen-4-sinnoh)
- [Gen 5: Unova](https://modrinth.com/datapack/cobblemon-spawn-filter-gen-5-unova)
- [Gen 6: Kalos](https://modrinth.com/datapack/cobblemon-spawn-filter-gen-6-kalos)
- [Gen 7: Alola](https://modrinth.com/datapack/cobblemon-spawn-filter-gen-7-alola)
- [Gen 8: Galar](https://modrinth.com/datapack/cobblemon-spawn-filter-gen-8-galar)
- [Gen 9: Paldea](https://modrinth.com/datapack/cobblemon-spawn-filter-gen-9-paldea)

# How it works...
## What this datapack **DOES** affect:
- All natural spawns (...when they just _pop_ into existence)
- Fishing spawns (via Cobblemon fishing mechanics)
- Alpha Pokémon and herd spawns (new in Cobblemon 1.8)
- Habitat structures (new in Cobblemon 1.8)
    - NOTE: Habitats replace normal spawning right around them, so a habitat with none of your generations' Pokémon won't spawn anything nearby.
    - NOTE: Some Pokémon spawn in habitats in both their regular and a regional form (example: Vulpix in Wildfire Scars, Alolan Vulpix in Snowy Grottos). Cobblemon doesn't let datapacks tell those apart in habitats, so habitats only spawn them when both generations are installed (Gen 1 + Gen 7 for Vulpix). They still spawn normally outside habitats.

## What this datapack **DOES NOT** affect:
- Cobblemon structures (example: Gimmighouls spawning from the chests in Gimmighoul towers)
- Structure loot tables (example: fossil loot tables from sus sand/gravel in fossil archaeology structures)
- Cross-gen evolutions (example: Pichu > Pikachu, Magneton > Magnezone)

# Setup
Setup for these spawn filters will depend on whether you are playing with just the base mod or using a popular modpack, such as Cobbleverse. See the applicable directions below:

## Cobblemon (base mod only)
1. Add datapack/s to your Modrinth profile or modpack
1. Copy/move the datapack/s to your world's datapack folder
    - NOTE: Datapacks in `./datapacks` (base folder) don't apply globally to all your worlds, this is why you must include it in the world-specific datapack folder (`./saves/<your_world_name>/datapacks`) for this to work. More info on the [Minecraft Wiki](https://minecraft.wiki/w/Data_pack#Usage).
1. Join your world and enjoy the filtered spawns!

## Cobbleverse (popular modpack)
I found a way for my datapacks to be compatible with the Cobbleverse modpack, but my workaround is a little technical, so I plan to create a tutorial video soon: [TODO: Add YouTube tutorial link here...]. But for now, directions listed below:

1. Add datapack/s to your Modrinth profile (appear in the `./datapacks` directory by default)
1. Move/Cut & paste datapack/s to the `./datapacks/extra` sub-directory (not the world-specific datapack folder)
    - *IMPORTANT*: Make sure to not leave any copies in the `./datapacks` directory, they must *ONLY* be in the `./datapacks/extra` sub-directory. It seems that the Cobbleverse modpack uses this directory to determine which datapacks are optional, which is important for the next steps.
1. Create new world/open existing world
1. Type the given command: `/datapack enable SpawnFilter_Gen#_Cobblemon1.8.2_v2.0.zip after COBBLEVERSE-DP-v28.zip` (replace `#` with the generation number, `1` through `9`)
    - *NOTE*: Specifying the datapack loads `after` the Cobbleverse datapack is necessary for this work, otherwise the Cobbleverse datapack will override my spawn rules. That's why this command is needed and we can't just add the file to the folder.
    - *NOTE*: The version numbers (i.e. `v1.0`, or `v28`) may be different than the ones provided in the command above, but if you start typing, then autocomplete should help you find the correct name you need.
    - *NOTE*: Your player needs operator (OP) status to execute commands. If they are disabled in you're single player world, then just Pause the game > Open to LAN > Set "Allow Commands" = ON > Start LAN World > Now execute the command
1. For multiple generations, repeat the previous step until each datapack is enabled.

## Disclaimer
Currently, the spawning rules are based off of the base Cobblemon mod. If a modpack, such as Cobbleverse, has their own tweaked spawning rules, then enabling my datapacks will revert to the base Cobblemon spawning rules.

Also, because the spawn rules are based off of the base Cobblemon mod, any spawning conditions for unimplemented Pokémon that modpacks add, will be missing until they are in the base mod. For example, this notably affects mythical and legendary Pokémon that spawn naturally from the Cobbleverse modpack.

# Contact
Issues or questions?

Reach out to me on the official Cobblemon discord (@TacoSocks) or email me at <tacosocks.gaming@gmail.com>.

# TL;DR
Filters Cobblemon’s natural Pokémon spawns by generation, including Alphas, herds and habitats. Stack multiple datapacks to combine generations. :)