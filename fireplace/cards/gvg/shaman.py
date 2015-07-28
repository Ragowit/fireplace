from ..utils import *


##
# Minions

# Vitality Totem
class GVG_039:
	events = OWN_TURN_END.on(Heal(FRIENDLY_HERO, 4))


# Siltfin Spiritwalker
class GVG_040:
	events = Death(FRIENDLY + MURLOC).on(Draw(CONTROLLER))


# Neptulon
class GVG_042:
	play = Give(CONTROLLER, RandomMinion(race=Race.MURLOC)) * 4


##
# Spells

# Ancestor's Call
class GVG_029:
	play = (
		Summon(CONTROLLER, RANDOM(CONTROLLER_HAND + MINION)),
		Summon(OPPONENT, RANDOM(OPPONENT_HAND + MINION)),
	)


# Crackle
class GVG_038:
	play = Hit(TARGET, RandomNumber(3, 4, 5, 6))


##
# Weapons

# Powermace
class GVG_036:
	deathrattle = Buff(RANDOM(FRIENDLY_MINIONS + MECH), "GVG_036e")
