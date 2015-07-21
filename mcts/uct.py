# This is a very simple implementation of the UCT Monte Carlo Tree Search algorithm in Python 2.7.
# The function UCT(rootstate, itermax, verbose = False) is towards the bottom of the code.
# It aims to have the clearest and simplest possible code, and for the sake of clarity, the code
# is orders of magnitude less efficient than it could be made, particularly by using a 
# state.GetRandomMove() or state.DoRandomRollout() function.
# 
# Example GameState classes for Nim, OXO and Othello are included to give some idea of how you
# can write your own GameState use UCT in your 2-player game. Change the game to be played in 
# the UCTPlayGame() function at the bottom of the code.
# 
# Written by Peter Cowling, Ed Powley, Daniel Whitehouse (University of York, UK) September 2012.
# 
# Licence is granted to freely use and distribute for any sensible/legal purpose so long as this comment
# remains in any distributed code.
# 
# For more information about Monte Carlo Tree Search check out our web site at www.mcts.ai

from math import *
import copy
#import logging
import random
import time
import sys, traceback
from enum import Enum
from fireplace import cards
from fireplace.cards.heroes import *
from fireplace.deck import Deck
from fireplace.enums import CardType, Rarity, PlayState
from fireplace.game import Game
from fireplace.player import Player

#logging.getLogger().setLevel(logging.DEBUG)


class MOVE(Enum):
    PRE_GAME = 1
    PICK_CLASS = 2
    PICK_CARD = 3
    END_TURN = 4
    HERO_POWER = 5
    MINION_ATTACK = 6
    HERO_ATTACK = 7
    PLAY_CARD = 8

class HearthState:
    """ A state of the game, i.e. the game board.
    """
    def __init__(self):
        self.playerJustMoved = 2 # At the root pretend the player just moved is p2 - p1 has the first move
        random.seed(1857)

        adjacent_cards = ["Dire Wolf Alpha", "Ancient Mage", "Defender of Argus", "Sunfury Protector",
                          "Flametongue Totem", "Explosive Shot", "Cone of Cold", "Betrayal", "Void Terror",
                          "Unstable Portal", "Wee Spellstopper", "Piloted Shredder", "Piloted Sky Golem",
                          "Recombobulator", "Foe Reaper 4000", "Nefarian"]
        self.adjacent_cards = adjacent_cards

        self.player1 = None
        self.hero1 = MAGE
        self.deck1 = []
        
        self.player2 = None
        self.hero2 = None
        self.deck2 = []

        self.game = None

        # Simple Arcane Missiles lethal test
        #self.player1 = Player(name="one")
        #self.player2 = Player(name="two")
        #self.hero1 = MAGE 
        #self.deck1 = ["EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277",
        #              "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277",
        #              "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277",
        #              "EX1_277", "EX1_277", "EX1_277"]
        #self.player1.prepare_deck(self.deck1, self.hero1)
        #self.hero2 = MAGE
        #self.deck2 = ["EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277",
        #              "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277",
        #              "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277", "EX1_277",
        #              "EX1_277", "EX1_277", "EX1_277"]
        #self.player2.prepare_deck(self.deck2, self.hero2)
        #self.game = Game(players=(self.player1, self.player2))
        #self.game.start()
        #self.game.players[0].hero.hit(self.game.players[0].hero, 24)
        #self.game.players[1].hero.hit(self.game.players[1].hero, 24)


    def Clone(self):
        """ Create a deep clone of this game state.
        """
        st = HearthState()
        st.playerJustMoved = self.playerJustMoved
        st.player1 = self.player1
        st.hero1 = self.hero1
        st.deck1 = copy.copy(self.deck1)
        st.player2 = self.player2
        st.hero2 = self.hero2
        st.deck2 = copy.copy(self.deck2)
        #st.game = copy.copy(self.game)
        st.game = copy.deepcopy(self.game)
        
        return st

    def DoMove(self, move):
        """ Update a state by carrying out the given move.
        """
        if self.game is not None:
            assert self.game.current_player.playstate == PlayState.PLAYING
            
            if self.game.current_player is not None:        
                if self.game.current_player.name == "one":        
                    self.playerJustMoved = 1        
                else:        
                    self.playerJustMoved = 2

        try:
            if move[0] == MOVE.PRE_GAME:
                self.player1 = Player(name="one")
                self.player2 = Player(name="two")
                self.player1.prepare_deck(self.deck1, self.hero1)
                self.player2.prepare_deck(self.deck2, self.hero2)
                self.game = Game(players=(self.player1, self.player2))
                self.game.start()
            elif move[0] == MOVE.PICK_CLASS:
                self.hero2 = move[1]
            elif move[0] == MOVE.PICK_CARD:
                if len(self.deck1) < 30:
                    self.deck1.append(move[1].id)
                else:
                    self.deck2.append(move[1].id)
            elif move[0] == MOVE.END_TURN:
                self.game.end_turn()
            elif move[0] == MOVE.HERO_POWER:
                heropower = self.game.current_player.hero.power
                if move[3] is None:
                    heropower.use()
                else:
                    heropower.use(target=heropower.targets[move[3]])
            elif move[0] == MOVE.PLAY_CARD:
                card = self.game.current_player.hand[move[2]]
                if move[3] is None:
                    card.play()
                else:
                    card.play(target=card.targets[move[3]])
            elif move[0] == MOVE.MINION_ATTACK:
                minion = self.game.current_player.field[move[2]]
                minion.attack(minion.targets[move[3]])
            elif move[0] == MOVE.HERO_ATTACK:
                hero = self.game.current_player.hero
                hero.attack(hero.targets[move[3]])
            else:
                raise NameError("DoMove ran into unclassified card", move)
        except:
            return            

    def GetMoves(self):
        """ Get all possible moves from this state.
        """
        if self.game is not None:
            if self.game.current_player.playstate != PlayState.PLAYING:
                return []
        valid_moves = []  # Move format is [enum, card, index of card in hand, target index]

        if self.game is None and len(self.deck1) == 30 and len(self.deck2) == 30:
            valid_moves.append([MOVE.PRE_GAME])
        elif self.game is None and len(self.deck1) == 30 and self.hero2 is None:
            valid_moves.append([MOVE.PICK_CLASS, DRUID])
            valid_moves.append([MOVE.PICK_CLASS, HUNTER])
            valid_moves.append([MOVE.PICK_CLASS, MAGE])
            valid_moves.append([MOVE.PICK_CLASS, PALADIN])
            valid_moves.append([MOVE.PICK_CLASS, PRIEST])
            valid_moves.append([MOVE.PICK_CLASS, ROGUE])
            valid_moves.append([MOVE.PICK_CLASS, SHAMAN])
            valid_moves.append([MOVE.PICK_CLASS, WARLOCK])
            valid_moves.append([MOVE.PICK_CLASS, WARRIOR])
        elif self.game is None and len(self.deck1) < 30 or len(self.deck2) < 30:
            collection = []

            if len(self.deck1) < 30:
                owned_cards = []
                ### BASIC ###
                # Druid
                owned_cards.extend(["EX1_169", "CS2_008", "CS2_005", "CS2_009", "CS2_013", "CS2_007", "CS2_011",
                                    "CS2_012", "EX1_173", "CS2_232"])
                # Hunter
                owned_cards.extend(["CS2_084", "DS1_185", "DS1_184", "DS1_175", "NEW1_031", "EX1_539", "DS1_183",
                                    "DS1_070", "CS2_237", "DS1_178"])
                # Mage
                owned_cards.extend(["EX1_277", "CS2_027", "CS2_025", "CS2_024", "CS2_023", "CS2_026", "CS2_029",
                                    "CS2_022", "CS2_033", "CS2_032"])
                # Paladin
                owned_cards.extend(["CS2_091", "CS2_087", "EX1_371", "EX1_360", "CS2_089", "CS2_097", "CS2_092",
                                    "CS2_093", "CS2_094", "CS2_088"])
                # Priest
                owned_cards.extend(["CS1_130", "CS2_003", "CS2_004", "CS2_235", "CS2_236", "DS1_233", "CS2_234",
                                    "EX1_622", "CS1_112", "CS1_113"])
                # Rogue
                owned_cards.extend(["CS2_072", "CS2_074", "CS2_075", "EX1_581", "EX1_278", "EX1_129", "CS2_080",
                                    "CS2_076", "NEW1_004", "CS2_077"])
                # Shaman
                owned_cards.extend(["CS2_041", "EX1_244", "CS2_037", "CS2_045", "CS2_039", "EX1_565", "EX1_246",
                                    "EX1_587", "CS2_046", "CS2_042"])
                # Warlock
                owned_cards.extend(["NEW1_003", "CS2_063", "EX1_302", "EX1_308", "CS2_065", "EX1_306", "CS2_061",
                                    "CS2_057", "CS2_062", "CS2_064"])
                # Warrior
                owned_cards.extend(["CS2_108", "EX1_400", "CS2_106", "CS2_114", "CS2_105", "CS2_103", "EX1_606",
                                    "EX1_084", "NEW1_011", "CS2_112"])
                # Neutral
                owned_cards.extend(["CS2_189", "CS1_042", "EX1_508", "CS2_168", "CS2_171", "EX1_011", "EX1_066",
                                    "CS2_172", "CS2_173", "CS2_121", "CS2_142", "EX1_506", "EX1_015", "CS2_120",
                                    "EX1_582", "CS2_141", "CS2_125", "CS2_118", "CS2_122", "CS2_196", "EX1_019",
                                    "CS2_127", "CS2_124", "CS2_182", "EX1_025", "CS2_147", "CS2_119", "CS2_197",
                                    "CS2_179", "CS2_131", "CS2_187", "DS1_055", "CS2_226", "EX1_399", "EX1_593",
                                    "CS2_150", "CS2_155", "CS2_200", "CS2_162", "CS2_213", "CS2_201", "CS2_222",
                                    "CS2_186"])
        
                ### CLASSIC ###
                # Druid
                owned_cards.extend(["EX1_160", "EX1_154", "EX1_155", "EX1_166", "NEW1_007", "EX1_165"])
                # Hunter
                owned_cards.extend(["EX1_609", "EX1_531", "EX1_617", "EX1_538"])
                # Mage
                owned_cards.extend(["CS2_031", "NEW1_012", "EX1_608", "EX1_289", "EX1_274", "CS2_028", "EX1_559"])
                # Paladin
                owned_cards.extend(["EX1_132", "EX1_130", "EX1_379", "EX1_362"])
                # Priest
                owned_cards.extend(["EX1_621", "EX1_332", "CS1_129", "EX1_339", "EX1_626", "EX1_624"])
                # Rogue
                owned_cards.extend(["CS2_073", "EX1_128", "EX1_126", "EX1_124"])
                # Shaman
                owned_cards.extend(["EX1_251", "CS2_038"])
                # Warlock
                owned_cards.extend(["EX1_316", "EX1_319", "EX1_596", "EX1_317", "EX1_315", "EX1_310"])
                # Warrior
                owned_cards.extend(["EX1_607", "CS2_104", "EX1_391", "EX1_402", "EX1_603", "EX1_408", "EX1_407"])
                # Neutral
                owned_cards.extend(["CS2_231", "EX1_008", "CS2_146", "EX1_004", "EX1_393", "NEW1_018", "EX1_162",
                                    "NEW1_023", "CS2_203", "NEW1_019", "EX1_096", "EX1_082", "NEW1_037", "EX1_102",
                                    "EX1_556", "EX1_597", "EX1_017", "EX1_044", "EX1_020", "EX1_390", "EX1_083",
                                    "EX1_595", "EX1_093", "EX1_023", "EX1_284", "CS1_069", "CS2_151", "CS2_221",
                                    "EX1_028", "EX1_283"])
        
                ### PROMO ###
                owned_cards.extend(["EX1_112"])
        
                ### NAXXRAMAS ###
                # Druid
                owned_cards.extend(["FP1_019"])
                # Hunter
                owned_cards.extend(["FP1_011"])
                # Mage
                owned_cards.extend(["FP1_018"])
                # Paladin
                owned_cards.extend(["FP1_020"])
                # Priest
                owned_cards.extend(["FP1_023"])
                # Rogue
                owned_cards.extend(["FP1_026"])
                # Shaman
                owned_cards.extend(["FP1_025"])
                # Warlock
                owned_cards.extend(["FP1_022"])
                # Warrior
                owned_cards.extend(["FP1_021"])
                # Neutral
                owned_cards.extend(["FP1_028", "FP1_001", "FP1_003", "FP1_002", "FP1_004", "FP1_017", "FP1_007",
                                    "FP1_024", "FP1_029", "FP1_009", "FP1_005", "FP1_027", "FP1_031", "FP1_016",
                                    "FP1_015", "FP1_030", "FP1_012", "FP1_008", "FP1_014", "FP1_010", "FP1_013"])
        
                ### GOBLINS VS GNOMES ##
                # Druid
                owned_cards.extend(["GVG_030"])
                # Hunter
                owned_cards.extend(["GVG_043", "GVG_046"])
                # Mage
                owned_cards.extend(["GVG_001", "GVG_002"])
                # Paladin
                owned_cards.extend(["GVG_057", "GVG_101", "GVG_062"])
                # Priest
                owned_cards.extend(["GVG_011"])
                # Rogue
                owned_cards.extend(["GVG_023", "GVG_025", "GVG_022", "GVG_088"])
                # Shaman
                owned_cards.extend(["GVG_038", "GVG_039", "GVG_037", "GVG_040"])
                # Warlock
                owned_cards.extend(["GVG_045"])
                # Warrior
                owned_cards.extend(["GVG_051", "GVG_054", "GVG_053"])
                # Neutral
                owned_cards.extend(["GVG_082", "GVG_013", "GVG_085", "GVG_076", "GVG_081", "GVG_006", "GVG_103",
                                    "GVG_064", "GVG_075", "GVG_067", "GVG_084", "GVG_065", "GVG_044", "GVG_102",
                                    "GVG_071", "GVG_078", "GVG_096", "GVG_069", "GVG_079"])
                
                ### BLACKROCK MOUNTAIN ###
                # Druid
                owned_cards.extend(["BRM_010", "BRM_009"])
                # Hunter
                owned_cards.extend(["BRM_013", "BRM_014"])
                # Mage
                owned_cards.extend(["BRM_002", "BRM_003"])
                # Paladin
                owned_cards.extend(["BRM_001", "BRM_018"])
                # Priest
                owned_cards.extend(["BRM_004", "BRM_017"])
                # Rogue
                owned_cards.extend(["BRM_007", "BRM_008"])
                # Shaman
                owned_cards.extend(["BRM_011", "BRM_012"])
                # Warlock
                owned_cards.extend(["BRM_005", "BRM_006"])
                # Warrior
                owned_cards.extend(["BRM_015", "BRM_016"])
                # Neutral
                owned_cards.extend(["BRM_022", "BRM_033", "BRM_020", "BRM_026", "BRM_034", "BRM_019", "BRM_024",
                                    "BRM_028", "BRM_025", "BRM_029", "BRM_031", "BRM_027", "BRM_030"])

                hero = getattr(cards, self.hero1)

                for card in owned_cards:
                    cls = getattr(cards, card)
                    if not cls.collectible:
                        continue
                    if cls.type == CardType.HERO:
                        # Heroes are collectible...
                        continue
                    if cls.card_class and cls.card_class != hero.card_class:
                        continue
                    collection.append(cls)

                for card in collection:
                    if card.rarity == Rarity.LEGENDARY and card.id in self.deck1:
                        continue
                    elif self.deck1.count(card.id) < Deck.MAX_UNIQUE_CARDS:
                        valid_moves.append([MOVE.PICK_CARD, card])
            else:
                hero = getattr(cards, self.hero2)

                for card in cards.cardlist:
                    cls = getattr(cards, card)
                    if not cls.collectible:
                        continue
                    if cls.type == CardType.HERO:
                        # Heroes are collectible...
                        continue
                    if cls.card_class and cls.card_class != hero.card_class:
                        continue
                    collection.append(cls)

                for card in collection:
                    if card.rarity == Rarity.LEGENDARY and card.id in self.deck2:
                        continue
                    elif self.deck2.count(card.id) < Deck.MAX_UNIQUE_CARDS:
                        valid_moves.append([MOVE.PICK_CARD, card])
        else:
            # Play card
            for card in self.game.current_player.hand:
                dupe = False
                for i in range(len(valid_moves)):
                    if valid_moves[i][1].id == card.id:
                        dupe = True
                        break
                if not dupe:
                    if card.is_playable():
                        if card.has_target():
                            for t in range(len(card.targets)):
                                valid_moves.append([MOVE.PLAY_CARD, card, self.game.current_player.hand.index(card), t])
                        else:
                            valid_moves.append([MOVE.PLAY_CARD, card, self.game.current_player.hand.index(card), None])

            # Hero Power
            heropower = self.game.current_player.hero.power
            if heropower.is_usable():
                if heropower.has_target():
                    for t in range(len(heropower.targets)):
                        valid_moves.append([MOVE.HERO_POWER, None, None, t])
                else:
                    valid_moves.append([MOVE.HERO_POWER, None, None, None])

            # Minion Attack
            for minion in self.game.current_player.field:
                if minion.can_attack():
                    for t in range(len(minion.targets)):
                        valid_moves.append([MOVE.MINION_ATTACK, minion, self.game.current_player.field.index(minion), t])

            # Hero Attack
            hero = self.game.current_player.hero
            if hero.can_attack():
                for t in range(len(hero.targets)):
                    valid_moves.append([MOVE.HERO_ATTACK, hero, None, t])

            valid_moves.append([MOVE.END_TURN])

        return valid_moves

    def GetResult(self, playerjm):
        """ Get the game result from the viewpoint of playerjm.
        """
        if self.game.players[0].hero.health <= 0 and self.game.players[1].hero.health <= 0:
            return 0.5
        elif self.game.players[playerjm - 1].hero.health <= 0:
            return (self.game.turn - 100) / 2
        elif self.game.players[2 - playerjm].hero.health <= 0:
            return 100 - self.game.turn
        else:  # Should not be possible to get here unless we terminate the game early.
            return 0.5

    def __repr__(self):
        try:
            s = "Turn: " + str(self.game.turn)
            s += "\n[" + str(self.game.players[0].hero.health) + " hp ~ " + str(len(self.game.players[0].hand)) + " in hand ~ " + str(self.game.players[0].tempMana) + "/" + str(self.game.players[0].maxMana) + " mana] "
            #s += "\n[" + str(self.game.players[0].hero.health) + " hp ~ " + str(len(self.game.players[0].hand)) + " in hand ~ " + str(self.game.players[0].deck.left) + "/" + str(len(self.game.players[0].deck.cards)) + " in deck ~ " + str(self.game.players[0].mana) + "/" + str(self.game.players[0].max_mana) + " mana] "
            for minion in self.game.players[0].field:
                s += str(minion.atk) + "/" + str(minion.health) + ":"
            s += "\n[" + str(self.game.players[1].hero.health) + " hp ~ " + str(len(self.game.players[1].hand)) + " in hand ~ " + str(self.game.players[1].tempMana) + "/" + str(self.game.players[1].maxMana) + " mana] "
            #s += "\n[" + str(self.game.players[1].hero.health) + " hp ~ " + str(len(self.game.players[1].hand)) + " in hand ~ " + str(self.game.players[1].deck.left) + "/" + str(len(self.game.players[1].deck.cards)) + " in deck ~ " + str(self.game.players[1].mana) + "/" + str(self.game.players[1].max_mana) + " mana] "
            for minion in self.game.players[1].field:
                s += str(minion.atk) + "/" + str(minion.health) + ":"
            s += "\n" + "Current Player: " + str(self.game.currentPlayer)
            return s
        except:
            s = "Deck 1: " + ", ".join(self.deck1)
            s += "\nDeck 2: " + ", ".join(self.deck2)
            return s


class Node:
    """ A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
        Crashes if state not specified.
    """
    def __init__(self, move = None, parent = None, state = None):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = []
        self.wins = 0
        self.visits = 0
        if move and (move[0] == MOVE.END_TURN or move[0] == MOVE.PRE_GAME):
            self.untriedMoves = []
        else:
            self.untriedMoves = state.GetMoves() # future child nodes
        self.playerJustMoved = state.playerJustMoved # the only part of the state that the Node needs later
        
    def UCTSelectChild(self):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + sqrt(2*log(self.visits)/c.visits))[-1]
        return s
    
    def AddChild(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(move = m, parent = self, state = s)
        self.untriedMoves.remove(m)
        self.childNodes.append(n)
        return n
    
    def Update(self, result):
        """ Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustMoved.
        """
        self.visits += 1
        self.wins += result

    def __repr__(self):
        return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + " U:" + str(self.untriedMoves) + "]"

    def TreeToString(self, indent):
        s = self.IndentString(indent) + str(self)
        for c in sorted(self.childNodes, key = lambda c: c.visits):
            s += c.TreeToString(indent+1)
        return s

    def IndentString(self,indent):
        s = "\n"
        for i in range (1,indent+1):
            s += "| "
        return s

    def ChildrenToString(self):
        s = ""
        for c in sorted(self.childNodes, key = lambda c: c.visits):
            s += str(c) + "\n"
        return s[:-2]

    #def clean(self):
        #for child in self.childNodes:
        #    child.clean()
        #del self.childNodes
        #del self.parentNode
        #del self.untriedMoves


def UCT(rootstate, seconds, verbose = False):
    """ Conduct a UCT search for seconds starting from rootstate.
        Return the best move from the rootstate.
        Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""
    rootnode = Node(state = rootstate)

    iterations = 0
    future = time.time() + seconds
    while time.time() < future:
        node = rootnode
        state = rootstate.Clone()

        # Select
        while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
            node = node.UCTSelectChild()
            state.DoMove(node.move)

        # Expand
        if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
            m = random.choice(node.untriedMoves)
            state.DoMove(m)
            node = node.AddChild(m, state) # add child and descend tree

        # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        while state.GetMoves() != []: # while state is non-terminal
            state.DoMove(random.choice(state.GetMoves()))

        # Backpropagate
        while node != None: # backpropagate from the expanded node and work back to the root node
            node.Update(state.GetResult(node.playerJustMoved)) # state is terminal. Update node with result from POV of node.playerJustMoved
            node = node.parentNode

        iterations += 1

    # Output some information about the tree - can be omitted
    if (verbose): print(rootnode.TreeToString(0))
    else: print(rootnode.ChildrenToString())

    print("Iterations: " + str(iterations) + "\n")

    bestmove = sorted(rootnode.childNodes, key = lambda c: c.visits)[-1].move # return the move that was most visited
    #rootnode.clean()
    #del rootnode
    
    return bestmove


def UCTPlayGame():
    """ Play a sample game between two UCT players where each player gets a different number 
        of UCT iterations (= simulations = tree nodes).
    """
    state = HearthState()
    while (state.GetMoves() != []):
        print(str(state))
        try:
            m = UCT(rootstate = state, seconds = 10, verbose = False)
        except:
            print(state.deck1)
            print(state.deck2)
            traceback.print_exc()
            sys.exit()
        print("Best Move: " + str(m) + "\n")
        state.DoMove(m)

        print(state.deck1)
        print(state.deck2)
        print()
    if state.GetResult(state.playerJustMoved) >= 1.0:
        print("Player " + str(state.playerJustMoved) + " wins!")
    elif state.GetResult(state.playerJustMoved) <= 0.0:
        print("Player " + str(3 - state.playerJustMoved) + " wins!")
    else: print("Nobody wins!")


if __name__ == "__main__":
    """ Play a single game to the end using UCT for both players. 
    """
    UCTPlayGame()
