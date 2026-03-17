"""Built-in RCT2 scenario definitions."""

from enum import StrEnum


class Pack(StrEnum):
    """RollerCoaster Tycoon 2 game packs."""

    BASE = "RollerCoaster Tycoon 2"
    WACKY_WORLDS = "Wacky Worlds"
    TIME_TWISTER = "Time Twister"


class Scenario(StrEnum):
    """Built-in RCT2 scenarios. Values are the .SC6 filenames."""

    # ── Base Game — Beginner ─────────────────────────────────────────
    CRAZY_CASTLE = "Crazy Castle.SC6"
    ELECTRIC_FIELDS = "Electric Fields.SC6"
    FACTORY_CAPERS = "Factory Capers.SC6"

    # ── Base Game — Challenging ──────────────────────────────────────
    AMITY_AIRFIELD = "Amity Airfield.SC6"
    BOTANY_BREAKERS = "Botany Breakers.SC6"
    BUMBLY_BAZAAR = "Bumbly Bazaar.SC6"
    DUSTY_GREENS = "Dusty Greens.SC6"
    FUNGUS_WOODS = "Fungus Woods.SC6"
    GRAVITY_GARDENS = "Gravity Gardens.SC6"
    INFERNAL_VIEWS = "Infernal Views.SC6"

    # ── Base Game — Expert ───────────────────────────────────────────
    ALPINE_ADVENTURES = "Alpine Adventures.SC6"
    EXTREME_HEIGHTS = "Extreme Heights.SC6"
    GHOST_TOWN = "Ghost Town.SC6"
    LUCKY_LAKE = "Lucky Lake.SC6"
    RAINBOW_SUMMIT = "Rainbow Summit.SC6"

    # ── Base Game — Six Flags (Real) ─────────────────────────────────
    SIX_FLAGS_BELGIUM = "Six Flags Belgium.SC6"
    SIX_FLAGS_GREAT_ADVENTURE = "Six Flags Great Adventure.SC6"
    SIX_FLAGS_HOLLAND = "Six Flags Holland.SC6"
    SIX_FLAGS_MAGIC_MOUNTAIN = "Six Flags Magic Mountain.SC6"
    SIX_FLAGS_OVER_TEXAS = "Six Flags over Texas.SC6"

    # ── Base Game — Six Flags (Build Your Own) ───────────────────────
    BYO_SIX_FLAGS_BELGIUM = "Build your own Six Flags Belgium.SC6"
    BYO_SIX_FLAGS_GREAT_ADVENTURE = "Build your own Six Flags Great Adventure.SC6"
    BYO_SIX_FLAGS_HOLLAND = "Build your own Six Flags Holland.SC6"
    BYO_SIX_FLAGS_MAGIC_MOUNTAIN = "Build your own Six Flags Magic Mountain.SC6"
    BYO_SIX_FLAGS_PARK = "Build your own Six Flags Park.SC6"
    BYO_SIX_FLAGS_OVER_TEXAS = "Build your own Six Flags over Texas.SC6"

    # ── Wacky Worlds — Beginner ──────────────────────────────────────
    VICTORIA_FALLS = "Africa - Victoria Falls.SC6"
    GREAT_WALL_OF_CHINA = "Asia - Great Wall of China Tourism Enhancement.SC6"
    GRAND_CANYON = "North America - Grand Canyon.SC6"
    RIO_CARNIVAL = "South America - Rio Carnival.SC6"

    # ── Wacky Worlds — Challenging ───────────────────────────────────
    AFRICAN_DIAMOND_MINE = "Africa - African Diamond Mine.SC6"
    MAHARAJA_PALACE = "Asia - Maharaja Palace.SC6"
    AYERS_ROCK = "Australasia - Ayers Rock.SC6"
    EUROPEAN_CULTURAL_FESTIVAL = "Europe - European Cultural Festival.SC6"
    ROLLERCOASTER_HEAVEN = "North America - Rollercoaster Heaven.SC6"
    INCA_LOST_CITY = "South America - Inca Lost City.SC6"

    # ── Wacky Worlds — Expert ────────────────────────────────────────
    OASIS = "Africa - Oasis.SC6"
    ECOLOGICAL_SALVAGE = "Antarctic - Ecological Salvage.SC6"
    JAPANESE_COASTAL_RECLAIM = "Asia - Japanese Coastal Reclaim.SC6"
    FUN_AT_THE_BEACH = "Australasia - Fun at the Beach.SC6"
    RENOVATION = "Europe - Renovation.SC6"
    EXTREME_HAWAIIAN_ISLAND = "N America - Extreme Hawaiian Island.SC6"
    RAIN_FOREST_PLATEAU = "South America - Rain Forest Plateau.SC6"

    # ── Time Twister — Beginner ──────────────────────────────────────
    ROBIN_HOOD = "Dark Age - Robin Hood.SC6"
    AFTER_THE_ASTEROID = "Prehistoric - After the Asteroid.SC6"
    PRISON_ISLAND = "Roaring Twenties - Prison Island.SC6"
    FLOWER_POWER = "Rock 'n' Roll - Flower Power.SC6"

    # ── Time Twister — Challenging ───────────────────────────────────
    CASTLE = "Dark Age - Castle.SC6"
    FIRST_ENCOUNTERS = "Future - First Encounters.SC6"
    ANIMATRONIC_FILM_SET = "Mythological - Animatronic Film Set.SC6"
    JURASSIC_SAFARI = "Prehistoric - Jurassic Safari.SC6"
    SCHNEIDER_CUP = "Roaring Twenties - Schneider Cup.SC6"

    # ── Time Twister — Expert ────────────────────────────────────────
    FUTURE_WORLD = "Future - Future World.SC6"
    CRADLE_OF_CIVILIZATION = "Mythological - Cradle of Civilization.SC6"
    STONE_AGE = "Prehistoric - Stone Age.SC6"
    SKYSCRAPERS = "Roaring Twenties - Skyscrapers.SC6"
    ROCK_N_ROLL = "Rock 'n' Roll - Rock 'n' Roll.SC6"


SCENARIO_PACK: dict[Scenario, Pack] = {
    # Base Game
    Scenario.CRAZY_CASTLE: Pack.BASE,
    Scenario.ELECTRIC_FIELDS: Pack.BASE,
    Scenario.FACTORY_CAPERS: Pack.BASE,
    Scenario.AMITY_AIRFIELD: Pack.BASE,
    Scenario.BOTANY_BREAKERS: Pack.BASE,
    Scenario.BUMBLY_BAZAAR: Pack.BASE,
    Scenario.DUSTY_GREENS: Pack.BASE,
    Scenario.FUNGUS_WOODS: Pack.BASE,
    Scenario.GRAVITY_GARDENS: Pack.BASE,
    Scenario.INFERNAL_VIEWS: Pack.BASE,
    Scenario.ALPINE_ADVENTURES: Pack.BASE,
    Scenario.EXTREME_HEIGHTS: Pack.BASE,
    Scenario.GHOST_TOWN: Pack.BASE,
    Scenario.LUCKY_LAKE: Pack.BASE,
    Scenario.RAINBOW_SUMMIT: Pack.BASE,
    Scenario.SIX_FLAGS_BELGIUM: Pack.BASE,
    Scenario.SIX_FLAGS_GREAT_ADVENTURE: Pack.BASE,
    Scenario.SIX_FLAGS_HOLLAND: Pack.BASE,
    Scenario.SIX_FLAGS_MAGIC_MOUNTAIN: Pack.BASE,
    Scenario.SIX_FLAGS_OVER_TEXAS: Pack.BASE,
    Scenario.BYO_SIX_FLAGS_BELGIUM: Pack.BASE,
    Scenario.BYO_SIX_FLAGS_GREAT_ADVENTURE: Pack.BASE,
    Scenario.BYO_SIX_FLAGS_HOLLAND: Pack.BASE,
    Scenario.BYO_SIX_FLAGS_MAGIC_MOUNTAIN: Pack.BASE,
    Scenario.BYO_SIX_FLAGS_PARK: Pack.BASE,
    Scenario.BYO_SIX_FLAGS_OVER_TEXAS: Pack.BASE,
    # Wacky Worlds
    Scenario.VICTORIA_FALLS: Pack.WACKY_WORLDS,
    Scenario.GREAT_WALL_OF_CHINA: Pack.WACKY_WORLDS,
    Scenario.GRAND_CANYON: Pack.WACKY_WORLDS,
    Scenario.RIO_CARNIVAL: Pack.WACKY_WORLDS,
    Scenario.AFRICAN_DIAMOND_MINE: Pack.WACKY_WORLDS,
    Scenario.MAHARAJA_PALACE: Pack.WACKY_WORLDS,
    Scenario.AYERS_ROCK: Pack.WACKY_WORLDS,
    Scenario.EUROPEAN_CULTURAL_FESTIVAL: Pack.WACKY_WORLDS,
    Scenario.ROLLERCOASTER_HEAVEN: Pack.WACKY_WORLDS,
    Scenario.INCA_LOST_CITY: Pack.WACKY_WORLDS,
    Scenario.OASIS: Pack.WACKY_WORLDS,
    Scenario.ECOLOGICAL_SALVAGE: Pack.WACKY_WORLDS,
    Scenario.JAPANESE_COASTAL_RECLAIM: Pack.WACKY_WORLDS,
    Scenario.FUN_AT_THE_BEACH: Pack.WACKY_WORLDS,
    Scenario.RENOVATION: Pack.WACKY_WORLDS,
    Scenario.EXTREME_HAWAIIAN_ISLAND: Pack.WACKY_WORLDS,
    Scenario.RAIN_FOREST_PLATEAU: Pack.WACKY_WORLDS,
    # Time Twister
    Scenario.ROBIN_HOOD: Pack.TIME_TWISTER,
    Scenario.AFTER_THE_ASTEROID: Pack.TIME_TWISTER,
    Scenario.PRISON_ISLAND: Pack.TIME_TWISTER,
    Scenario.FLOWER_POWER: Pack.TIME_TWISTER,
    Scenario.CASTLE: Pack.TIME_TWISTER,
    Scenario.FIRST_ENCOUNTERS: Pack.TIME_TWISTER,
    Scenario.ANIMATRONIC_FILM_SET: Pack.TIME_TWISTER,
    Scenario.JURASSIC_SAFARI: Pack.TIME_TWISTER,
    Scenario.SCHNEIDER_CUP: Pack.TIME_TWISTER,
    Scenario.FUTURE_WORLD: Pack.TIME_TWISTER,
    Scenario.CRADLE_OF_CIVILIZATION: Pack.TIME_TWISTER,
    Scenario.STONE_AGE: Pack.TIME_TWISTER,
    Scenario.SKYSCRAPERS: Pack.TIME_TWISTER,
    Scenario.ROCK_N_ROLL: Pack.TIME_TWISTER,
}
