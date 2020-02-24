"""
BeeHive, a game for the iPhone based on the Scene module in Pythonista. 

You play as a bee in an enemy beehive, 
trying to collect as many honeycombs as possbile while avoiding the enemy 
bees which are entering the hive at regular time intervals. 

You control 
the friendly bee with the help of the iPhone's built-in accelerometer and 
gyroscope.

You lose a life everytime you collide with an enemy bee. This also stirs the enemy bees 
and they start flying faster for a limited time. Directly after such a collision 
you are immune to the enemy bees, indicated by the fact that your character is blinking. 

You grow in size each time you collect a honeycomb. The enemey bees entering the hive also 
increase in size with time. 

There are various power-ups to aid you: 

Heart: An extra life. 

Pink flower: Enables you to kill the enemy bees by colliding with them. This 
power-up only lasts for a limited time, indicated by your character blinking. 

Black flower: Like a pink flower, only you also dobules in size for the duration 
of the power-up, making it easier to kill of the enemy. 

Lightning: When you collect a lightning, it is visible at the bottom left of the screen. 
As you tap it, the enemy bees stop moving for a limited time. 

Mushroom: Halves your size. 

The high score is being saved and updated when beaten. 
"""

from scene import *
from random import *
import random
import math 
import sound
from menus import MenuScene

#The following constants determine the basic game parameters for the bees and the power-ups. 

PLAYERLIVES = 3 

BEESPEED = 1 #Determines the amount with which the enemy bees change their speed at a given time step 
BEEFREQUENCY = 4 #Determines how often a new enemy bee appears

FLOWERFREQUENCY = 40 #Determines how often a new flower appears
HONEYCOMBFREQUENCY = 6 #Determines how often a new honeycomb appears
HEARTFREQUENCY = 90 #Determines how often a new heart appears
LIGHTNINGFREQUENCY = 90 #Determines how often a new lightning appears
MUSHROOMFREQUENCY = 100 #Determines how often a new mushroom appears

#The class for the enemy bees. Each bee is represented by a yellow circle with a black centre. 
class Bee (ShapeNode):
        def __init__(self, **kwargs):
                ShapeNode.__init__(self, ui.Path.oval(0, 0, 0, 0), 'yellow', **kwargs) 
                self.child = ShapeNode(ui.Path.oval(0, 0, 0, 0), 'black')
                self.add_child(self.child)
                
                self.age = 0 
                self.speedup = 0
                self.speedright = 0
                self.fully_grown = randint(150, 250)
                self.entrance_x = 0
                self.entrance_y = 0
                self.inHive = False
                self.dying = False
                self.dead = False
                
        #This function controls how the enemy bees enter the hive. The bees grow gradually 
        #to their fully grown size. This size is increased with time: Every 240 seconds, 
        #another multiple of fully_grown is added to the size of the new-born bees.  
        def enter(self, time):
                if not self.inHive:
                        if self.age < int((1 + (time / 240)) * self.fully_grown):
                                self.age += 1
                                t = self.age
                                self.path = ui.Path.oval(0, 0, 0.1 * t, 0.1 * t)
                                self.child.path = ui.Path.oval(0, 0, 0.05 * t, 0.05 * t)
                        else:
                                self.inHive = True
        
        #This function controls the movement of the enemy bees. For every second cycle of the update loop, they change their
        #velocity in a random fashion, dictated by BEESPEED. The function makes sure the bees do not exceed
        #their speed limit, and that they do not move out of bounds. 
        def move(self, time, width, height, beeSpeedLimit):
                if self.inHive and not self.dead:
                        t = time % 2

                        if t == 0:
                                v = self.speedright
                                w = self.speedup

                                if v > beeSpeedLimit:
                                        v -= randint(0, BEESPEED)
                                elif v < - beeSpeedLimit:
                                        v += randint(0,BEESPEED)
                                else: 
                                        v += randint(-BEESPEED, BEESPEED)

                                if (self.position.x < 0) and (v < 0):  
                                        v = -v
                                elif (self.position.x > width) and (v > 0):
                                        v = -v 

                                if w > beeSpeedLimit:
                                        w -= randint(0, BEESPEED)
                                elif w < - beeSpeedLimit:    
                                        w += randint(0,BEESPEED) 
                                else: 
                                        w += randint(-BEESPEED, BEESPEED)

                                if (self.position.y < 0) and (w < 0):
                                        w = -w
                                elif (self.position.y > height) and (w > 0):
                                        w = -w 

                                self.speedright = v
                                self.speedup = w
                                self.position += (v, w)
        
        #This function controls the dying of the enemey bees when they get hit by the 
        #player with a flower power-up. When this happens, the enemy bee goes into a 
        #tail spin and drops to the floor of the hive. As it hits the floor, a dust cloud
        #rises and then evaporates. 
        def die(self, list):
                if self.dying: 
                        r = self.age
                        if r > 90:  
                                self.path = ui.Path.oval(0, 0, 0.1 * r, 0.1 * r)
                                self.child.path = ui.Path.oval(0, 0, 0.05 * r, 0.05 * r)
                                s = 0.5 * r / self.fully_grown
                                radius = s * 12
                                angle1 = (r / 15) * 2 * 3.14
                                angle2 = ((r +1) / 15) * 2 * 3.14

                                c1 = radius * (math.cos(angle2) - math.cos(angle1))
                                c2 = radius * (math.sin(angle2) - math.sin(angle1))

                                self.position += (c1, c2)
                                self.age -= 1
                        if r == 90:
                                self.dead = True
                                sound.play_effect('arcade:Explosion_5')

                                dustlist = []

                                for i in range(10):
                                        r = randint(3, 7)
                                        dustlist.append(ShapeNode(ui.Path.oval(0, 0, r, r), 'white'))
                                        self.add_child(dustlist[i])
                                        c1 = 7 * math.cos((i/5) * math.pi)
                                        c2 = 7 * math.sin((i/5) * math.pi)
                                        dustlist[i].position = (c1, c2)

                                self.run_action(Action.fade_to(0, 1))
                                list.remove(self)

#The class of the player, repsresented by a black circle with a yellow centre.                                 
class Player (ShapeNode):
        def __init__(self, **kwargs):
                ShapeNode.__init__(self, ui.Path.oval(0, 0, 20, 20), 'black', **kwargs) 
                self.child = ShapeNode(ui.Path.oval(0, 0, 10, 10), 'yellow')
                self.add_child(self.child)
                
                self.lives = PLAYERLIVES
                self.honeycombscollected = 0
                self.diameter = 20 #While self.size.x =21 - some sort of rounding error? 
                self.age = 200 #Adapted from Bee class
                self.fully_grown = 200 #Adapted from Bee class
                self.immune = False
                self.attack = False 
                self.dying = False
                self.half_dead = False
                self.dead = False
                
        #This function changes the size of the player as need in connection with 
        #the mushroom and black flower power-ups. 
        def change_size(self, factor):
                r = self.position.x
                s = self.position.y

                self.diameter *= factor
                X = self.diameter
                Y = X / 2

                self.path = ui.Path.oval(r, s, X, X)
                self.child.path = ui.Path.oval(r, s, Y, Y)
        
        #Same as the above function, but ensuring the dimensions of the 
        #player are integers. 
        def change_size_int(self, factor):
                r = self.position.x
                s = self.position.y

                x = self.diameter
                X = round(factor * x)
                Y = round(X / 2)

                self.path = ui.Path.oval(r, s, X, X)
                self.child.path = ui.Path.oval(r, s, Y, Y)

        def change_death(self):
                self.dead = True
        
        #This function controls the death of the player, after it has run out of lives. 
        #Adapted from the correspoding function for the enemy bees above. 
        def die(self):
                if self.dying: 
                        r = self.age
                        if r > 90:  
                                self.path = ui.Path.oval(0, 0, 0.1 * r, 0.1 * r)
                                self.child.path = ui.Path.oval(0, 0, 0.05 * r, 0.05 * r)
                                s = 0.5 * r / self.fully_grown
                                radius = s * 12
                                angle1 = (r / 15) * 2 * 3.14
                                angle2 = ((r +1) / 15) * 2 * 3.14

                                c1 = radius * (math.cos(angle2) - math.cos(angle1))
                                c2 = radius * (math.sin(angle2) - math.sin(angle1))

                                self.position += (c1, c2)
                                self.age -= 1
                        if 0 < r <= 90:
                                self.half_dead = True
                                self.age = 0
                                sound.play_effect('arcade:Explosion_4')

                                dustlist = []

                                for i in range(10):
                                        r = randint(3, 7)
                                        dustlist.append(ShapeNode(ui.Path.oval(0, 0, r, r), 'white'))
                                        self.add_child(dustlist[i])
                                        c1 = 7 * math.cos((i/5) * math.pi)
                                        c2 = 7 * math.sin((i/5) * math.pi)
                                        dustlist[i].position = (c1, c2)

                                actions = [Action.fade_to(0,1), Action.call(self.change_death)]

                                self.run_action(Action.sequence(actions))


#This is the class for the flower power-up, enabling the player to go into attack mode and 
#kill the enemy bees. The flower is represented by a yellow centre surrounded by five petals. 
class Flower (ShapeNode):
        def __init__(self, farbe, **kwargs):
                ShapeNode.__init__(self, ui.Path.oval(0, 0, 8, 8), 'black', **kwargs) 

                self.farbe = farbe 

                self.birthtime = 0
                self.z_position = 0.5
                
                self.dead = False 
                

                petals = []

                for i in range(5):
                        petals.append(ShapeNode(ui.Path.oval(0, 0, 8,8), farbe))
                        self.add_child(petals[i])
                        petals[i].position = (4 * math.cos(2 * math.pi * i / 5), 4 * math.sin(2 * math.pi * i / 5))

                cen = ShapeNode(ui.Path.oval(0, 0, 5,5), 'yellow')
                self.add_child(cen)

        
        #This function removes the flower if it is picked up, or if it is not picked up within a given time. 
        def die(self, list, time):
                if time - self.birthtime > 3:
                        self.run_action(Action.fade_to(0, 0.1))
                        list.remove(self)

#This is the class for the honeycombs. The aim of the game is for the player to collect these. 
class Honeycomb (ShapeNode):
        def __init__(self, **kwargs):
                SpriteNode.__init__(self,'pzl:Yellow5', **kwargs)

                self.size = (12, 12)

                self.birthtime = 0
                self.z_position = 0.5
                self.dead = False 

        #This function removes the honeycomb if it is picked up, or if it is not picked up within a given time. 
        def die(self, list, time):
                if time - self.birthtime > 5:
                        self.run_action(Action.fade_to(0, 0.1))
                        list.remove(self)               

#This is the class for the heart. Collecting a heart gives an extra life.                        
class Heart (ShapeNode):
        def __init__(self, **kwargs):
                SpriteNode.__init__(self,'plc:Heart', **kwargs)

                self.size = (15,23)

                self.birthtime = 0 
                self.z_position = 0.5
                self.dead = False

        #This function removes the heart if it is picked up, or if it is not picked up within a given time.
        def die(self, list, time):
                if time - self.birthtime > 5:
                        self.run_action(Action.fade_to(0, 0.1))
                        list.remove(self)               
#This is the class of the lightning power-up. 
class Lightning (ShapeNode):
        def __init__(self, **kwargs):
                SpriteNode.__init__(self,'spc:BoltGold', **kwargs)

                self.size = (15,23)

                self.birthtime = 0 
                self.z_position = 0.5
                self.dead = False

        #This function removes the lightning if it is picked up, or if it is not picked up within a given time.
        def die(self, list, time):
                if time - self.birthtime > 5:
                        self.run_action(Action.fade_to(0, 0.1))
                        list.remove(self)               

#This class is for the thunderbolt. This is used to keep track of the number of lighnings currently
#in the player's possesion. This is indicated in the bottom left of the screen. Pressing the symbol 
#of a thunderbolt stuns the enemy bees. 
class Thunderbolt (ShapeNode):
        def __init__(self, **kwargs):
                SpriteNode.__init__(self,'emj:High_Voltage_Sign', **kwargs)

                self.size = (35,40)

                self.birthtime = 0 
                self.z_position = 0.5
                self.dead = False

        #This function removes the thunderbolt when it is being tapped to release the lightning. 
        def die(self, list, time):
                if time - self.birthtime > 5:
                        self.run_action(Action.fade_to(0, 0.1))
                        list.remove(self)               

#This is the class of the mushroom. Collecting a mushroom makes the player halve in size, 
#and so makes it easier to avoid the enemy bees, but also more difficult to bring them down
#when a flower has been collected. 
class Mushroom (ShapeNode):
        def __init__(self, **kwargs):
                SpriteNode.__init__(self,'plf:Tile_MushroomRed', **kwargs)

                self.size = (35,40)

                self.birthtime = 0 
                self.z_position = 0.5
                self.dead = False

        #This function removes the mushroom if it is picked up, or if it is not picked up within a given time.
        def die(self, list, time):
                if time - self.birthtime > 5:
                        self.run_action(Action.fade_to(0, 0.1))
                        list.remove(self)               


#The class that controls the running of the game. 
class Game (Scene):
        def setup(self):
                self.background_color = 'yellow' #Later replaced with the hexagonal background pattern 
                self.time = 0 #Increased manually by one for each cycle of the update loop
                self.speed_limit = 3 #The speed limit of the enemy bees
                self.buzzing = False #Keeps track of whether the enemy bees have been stirred or not 
                self.time_last_buzz = 0 
                self.thunder = False #Keeps track of whether the enemy bees have been struck by a lightning power-up
                self.beebirth = True #Keeps track of whether a bee can be born
                self.flowergrowth = True #Keeps track of whether a flower can grow
                self.flowerbirth = 0
                self.flowercounter = 0 # Keeps track of the number of flowers as there are two types
                self.honeycombgrowth = True #Keeps track of whether a honeycomb can appear 
                self.honeycombbirth = 0
                self.heartgrowth = True #Keeps track of whether a heart can appear
                self.heartbirth = 0
                self.lightninggrowth = True #Keeps track of whether a lightning can appear
                self.lightningbirth = 0
                self.mushroomgrowth = True #Keeps track of whether a mushroom can appear
                self.mushroombirth = 0
                
                #Resets the iPhone's gyroscope used to move the player. 
                self.gx = 0
                self.gy = 0
                self.factor_x = 1
                self.factor_y = 1

                #The following parameters and for-loops create the hexagonal background effect. 
                m = 17
                k = (m-1) * 2 * math.sqrt(3) + 2
                r = self.size.w / k
                s = int(self.size.h / (2 * r)) 

                wall = Node(parent=self)

                for i in range(m): 
                        for j in range(s + 1):
                                face = ShapeNode(ui.Path.oval(0, 0, 2 * r, 2 * r), '#c17c00')
                                wall.add_child(face)
                                face.position = (r + 2 * math.sqrt(3) * r * i, r + 2 * r * j)

                for i in range(m + 1):
                        for j in range(s + 2):
                                face = ShapeNode(ui.Path.oval(0, 0, 2 * r, 2 * r), '#c17c00')
                                wall.add_child(face)
                                face.position = (r - math.sqrt(3) * r + 2 * math.sqrt(3) * r * i, 2 * r * j)



                #Lists for the enemy bees, honeycombs and power-ups. 
                self.bees = []
                self.flowers = []
                self.honeycombs = []
                self.hearts = []
                self.lightnings =[]
                self.thunderbolts = []
                self.mushrooms = []
                
                #The following block creates the counters for the number of collected honeycombs
                #and the number of lives left shown in the top left corner of the screen. 
                self.score = 0
                self.lives = PLAYERLIVES
                score_font = ('Futura',15)
                lives_font = ('Futura',15)
                self.honey = SpriteNode('pzl:Yellow1')
                self.honey.scale = 0.5
                self.add_child(self.honey)
                self.honey.position = (30, self.size.h - 20)
                self.honey.z_position = 2
                self.heart = SpriteNode('plc:Heart')
                self.heart.scale = 0.5
                self.add_child(self.heart)
                self.heart.position = (30, self.size.h - 45)
                self.heart.z_position = 2
                self.score_label = LabelNode('0', score_font, parent=self, color = 'black')
                self.lives_label = LabelNode('5', lives_font, parent=self, color = 'black') #This is set to PLAYERLIVES for each new game. 
                #self.score_label.anchor_point = (0,0)
                #self.lives_label.anchor_point = (0,0)
                self.score_label.position = (55, self.size.h - 20)
                self.lives_label.position = (55, self.size.h - 45)
                self.score_label.z_position = 2
                self.lives_label.z_position = 2

                self.load_highscore()
                self.show_start_menu()
        
        #Resets all variables as a new game is being started. 
        def new_game(self):     
                self.t = 0 #Time in seconds since the game started 
                self.time = 0  
                self.speed_limit = 3
                self.buzzing = False 
                self.time_last_buzz = 0 
                self.thunder = False
                self.time_last_thunder = 0
                self.beebirth = True
                self.flowergrowth = True
                self.honeycombgrowth = True
                self.heartgrowth = True
                self.lightninggrowth = True
                self.mushroomgrowth = True
                
                self.gx = 0
                self.gy = 0
                self.factor_x = 1
                self.factor_y = 1
                
                self.player = Player(parent=self) #Initializes the player
                self.player.position = (self.size.w/2, self.size.h / 2)
                
                for b in self.bees:
                        b.remove_from_parent()
                self.bees = []
                for f in self.flowers:
                        f.remove_from_parent()
                self.flowers = []
                for h in self.honeycombs:
                        h.remove_from_parent()
                self.honeycombs = []
                for h in self.hearts:
                        h.remove_from_parent()
                self.hearts = []
                for l in self.lightnings:
                        l.remove_from_parent()
                self.lightnings = []
                for t in self.thunderbolts:
                        t.remove_from_parent()
                self.thunderbolts = []
                for m in self.mushrooms:
                        m.remove_from_parent()
                self.mushrooms = []

                self.score = 0
                self.lives = PLAYERLIVES
                self.score_label.text = str(self.score)
                self.lives_label.text = str(self.lives)

        #The update()-method updates the screen approximately 60 times per second. 
        def update(self):
                self.set_position()
                self.update_player2()
                self.check_buzz()
                self.check_thunder()
                self.spawn_bee()
                self.grow_flower()
                self.grow_honeycomb()
                self.grow_heart()
                self.grow_lightning()
                self.grow_mushroom()
                self.check_lives()
                
                self.player.die()

                for bee in self.bees:
                        bee.enter(self.t)
                        bee.move(self.time, self.size.w, self.size.h, self.speed_limit)
                        self.bee_collision(bee)
                        self.bee_collision2(bee)
                        bee.die(self.bees)

                for flower in self.flowers: 
                        self.flower_collision(flower)
                        flower.die(self.flowers, self.t)

                for honeycomb in self.honeycombs:
                        self.honeycomb_collision(honeycomb)
                        honeycomb.die(self.honeycombs, self.t)

                for heart in self.hearts:
                        self.heart_collision(heart)
                        heart.die(self.hearts, self.t)

                for lightning in self.lightnings:
                        self.lightning_collision(lightning)
                        lightning.die(self.lightnings, self.t)

                for mushroom in self.mushrooms:
                        self.mushroom_collision(mushroom)
                        mushroom.die(self.mushrooms, self.t)

                self.time += 1          
        
        #This function allows the collected thunderbolts in the bottom left corner of the screen
        #to be tapped, whereupon the enemy bees get pacified for an amount of time. 
        def touch_began(self, touch):
                p = touch.location

                for T in self.thunderbolts:
                        if p in T.frame:
                                self.release_thunder()
                                T.run_action(Action.fade_to(0, 0.1))
                                self.thunderbolts.remove(T)     
                                self.sort_thunderbolts()
        
        #Primitve method for moving the player. Not used in this version of the game. 
        #The updated method is shown below. 
        def update_player(self):
                g = gravity()
                x = self.player.position.x
                y = self.player.position.y
                max_speed = 40

                if abs(g.x) > 0.05:
                        x = x + g.x * max_speed

                if abs(g.y) > 0.05:
                        y = y + g.y * max_speed

                x = max(0, min(self.size.w, x + randint(-1, 1)))
                y = max(0, min(self.size.h, y + randint(-1, 1)))
                self.player.position = (x, y)
        
        #The updated method for moving the player with the help of the iPhone's
        #built-in gyroscope and accelerometer. By using the set_position method, 
        #the player can be moved conveniently irrespective of the inital positioning 
        #of the phone. There is a max speed applying horizontally and vertically and 
        #the player cannot move out of the bounds of the screen. 
        def update_player2(self):
                if not self.player.half_dead:
                        g = gravity()
                        x = self.player.position.x
                        y = self.player.position.y
                        max_speed = 10

                        u = (g.x - self.gx) / self.factor_x
                        v = (g.y - self.gy) / self.factor_y

                        if abs(u) > 0.05:
                                if abs(u) < 1:
                                        x = x + u * max_speed
                                else: 
                                        x = x + (u / abs(u)) * max_speed

                        if abs(v) > 0.05:
                                if abs(v) < 1:
                                        y = y + v * max_speed
                                else:
                                        y = y + (v / abs(v)) * max_speed

                        x = max(0, min(self.size.w, x + randint(-1, 1)))
                        y = max(0, min(self.size.h, y + randint(-1, 1)))
                        self.player.position = (x, y)

        #This method makes sure the game can be played irrespective of the 
        #position of the phone when starting a new game, i.e. the starting 
        #position of the phone is seen as the neutral position where the 
        #player is not moving. 
        def set_position(self):
                if self.time == 0:
                        g = gravity()
                        self.gx = g.x
                        self.gy = g.y
                        self.factor_x = min(1 - self.gx, 1 + self.gx)
                        self.factor_y = min(1 - self.gy, 1 + self.gy)

        def double_size(self, node, progress):
                node.size *= 2

        def double_player_size(self):
                self.player.change_size(2)
                self.update_player_size()

        def halve_player_size(self):
                self.player.change_size(0.5)
                self.update_player_size()
        
        #Relates the age and fully_grown attributes. This is used for the Player's 
        #die method, to keep track of the size of the player as it dies. 
        def update_player_size(self):
                self.player.age = 10 * self.player.diameter
                self.player.fully_grown = self.player.age


        def load_highscore(self):
                try:
                        with open('.beehive_highscore', 'r') as f:
                                self.highscore = int(f.read())
                except:
                        self.highscore = 0

        def save_highscore(self):
                with open('.beehive_highscore', 'w') as f:
                        f.write(str(self.highscore))

        def check_lives(self):
                if self.player.dead:
                        self.player.remove_from_parent()
                        self.game_over()
        
        #Creates a new bee. How often this happens (in seconds) is controlled by BEEFREQUENCY.  
        #The self.beebirth boolean is used to make sure that only one bee (and not ~60) is created
        #each time (self.t changes only once in 60 update cycles). 
        def spawn_bee(self):
                t = int(self.t) % BEEFREQUENCY
                if t == 1 and self.beebirth:
                        bee = Bee(parent=self)
                        r = random.choice([50, self.size.w - 50])
                        s = random.choice([50, self.size.h - 50])
                        bee.position = (r, s)
                        self.bees.append(bee)
                        self.beebirth = False
                elif t == 2:
                        self.beebirth = True
        
        #Controls the forming of a flower power-up. The self.flowerbirth attribute 
        #sees to that one flower forms in every time window of FLOWERFREQENCY seconds, 
        #and that there is a random element to when the flower forms in this time span. 
        def grow_flower(self):
                t = int(self.t) % FLOWERFREQUENCY
                if t == 0:
                        self.flowergrowth = True
                        self.flowerbirth = random.randint(1, FLOWERFREQUENCY)
                        self.flowercounter = random.randint(1, 4)
                if t == self.flowerbirth and self.flowergrowth: 
                        self.flowergrowth = False
                        if self.flowercounter == 1:
                                flower = Flower(parent=self, farbe='rot')
                                r = random.randint(50, self.size.w - 50)
                                s = random.randint(50, self.size.h - 50)
                                flower.position = (r, s)
                                flower.birthtime = self.t
                                self.flowers.append(flower)
                        else: 
                                flower = Flower(parent=self, farbe='white')
                                r = random.randint(50, self.size.w - 50)
                                s = random.randint(50, self.size.h - 50)
                                flower.position = (r, s)
                                flower.birthtime = self.t
                                self.flowers.append(flower)
        
        #Controls the forming of a honeycomb. The self.honeycombbirth attribute 
        #sees to that one honeycomb forms in every time window of HONEYCOMBFREQENCY seconds, 
        #and that there is a random element to when the honeycomb forms in this time span.
        def grow_honeycomb(self):
                t = int(self.t) % HONEYCOMBFREQUENCY
                if t == 0:
                        self.honeycombgrowth = True
                        self.honeycombbirth = random.randint(1, HONEYCOMBFREQUENCY)
                if t == self.honeycombbirth and self.honeycombgrowth:
                        honeycomb = Honeycomb(parent=self)
                        r = random.randint(50, self.size.w - 50)
                        s = random.randint(50, self.size.h - 50)
                        honeycomb.position = (r, s)
                        honeycomb.birthtime = self.t
                        self.honeycombs.append(honeycomb)
                        self.honeycombgrowth = False

        #Controls the forming of a heart power-up. The self.heartbirth attribute 
        #sees to that one heart forms in every time window of HEARTFREQENCY seconds, 
        #and that there is a random element to when the heart forms in this time span.                        
        def grow_heart(self):
                t = int(self.t) % HEARTFREQUENCY
                if t == 0:
                        self.heartgrowth = True
                        self.heartbirth = random.randint(1, HEARTFREQUENCY)
                if t == self.heartbirth and self.heartgrowth:
                        heart = Heart(parent=self)
                        r = random.randint(50, self.size.w - 50)
                        s = random.randint(50, self.size.h - 50)
                        heart.position = (r, s)
                        heart.birthtime = self.t
                        self.hearts.append(heart)
                        self.heartgrowth = False

        #Controls the forming of a lightning power-up. The self.lightningbirth attribute 
        #sees to that one lightning forms in every time window of LIGHTNINGFREQENCY seconds, 
        #and that there is a random element to when the lightning forms in this time span.
        def grow_lightning(self):
                t = int(self.t) % LIGHTNINGFREQUENCY
                if t == 0:
                        self.lightninggrowth = True
                        self.lightningbirth = random.randint(1, LIGHTNINGFREQUENCY)
                if t == self.lightningbirth and self.lightninggrowth:
                        lightning = Lightning(parent=self)
                        r = random.randint(50, self.size.w - 50)
                        s = random.randint(50, self.size.h - 50)
                        lightning.position = (r, s)
                        lightning.birthtime = self.t
                        self.lightnings.append(lightning)
                        self.lightninggrowth = False

        #Controls the forming of a mushroom power-up. The self.mushroombirth attribute 
        #sees to that one mushroom forms in every time window of MUSHROOMFREQENCY seconds, 
        #and that there is a random element to when the mushroom forms in this time span.
        def grow_mushroom(self):
                t = int(self.t) % MUSHROOMFREQUENCY
                if t == 0:
                        self.mushroomgrowth = True
                        self.mushroombirth = random.randint(1, MUSHROOMFREQUENCY)
                if t == self.mushroombirth and self.mushroomgrowth:
                        mushroom = Mushroom(parent=self)
                        r = random.randint(50, self.size.w - 50)
                        s = random.randint(50, self.size.h - 50)
                        mushroom.position = (r, s)
                        mushroom.birthtime = self.t
                        self.mushrooms.append(mushroom)
                        self.mushroomgrowth = False
        
        #The enemy bees fly at increased speed for five seconds when provoked. 
        def check_buzz(self):
                if self.buzzing and self.t - self.time_last_buzz > 5:
                        self.speed_limit = 3
                        self.buzzing = False
        
        #The enemy bees are pacified for 7 seconds when hit by lightning. 
        def check_thunder(self):
                if self.thunder and self.t - self.time_last_thunder > 7:
                        self.speed_limit = 3
                        self.thunder = False
        
        #When the player is immune, he is not harmed by the enemy bees. 
        def change_immunity(self):
                if self.player.immune:
                        self.player.immune = False
                else:
                        self.player.immune = True               
        
        #When the player is in attack mode, it can kill off the enemy bees. 
        def change_attack(self):
                if self.player.attack:
                        self.player.attack = False
                else:
                        self.player.attack = True       
        
        #This method controls whether the player has collided with any of the enemy bees. If this is the case, and the player
        #is not immune or in attack mode, nor dying, and the enemy bee is also not dying, then the player loses a life and 
        #the enemy bees get stirred and so move faster for a limited period of time. 
        def bee_collision(self, bnode):
                v1 = Vector2(self.player.position.x, self.player.position.y)
                v2 = Vector2(bnode.position.x, bnode.position.y)

                if abs(v1 - v2) < 0.5 * (self.player.size.x + bnode.size.x) and not self.player.immune and not self.player.attack and not bnode.dying: 
                        if self.lives > 0:
                                self.lives -= 1
                                self.lives_label.text = str(self.lives)
                                if self.lives > 0:
                                        self.speed_limit = 10
                                        self.buzzing = True
                                        self.time_last_buzz = self.t
                                        self.player.immune = True
                                        sound.play_effect('digital:LowDown')

                                        actions = [Action.fade_to(0.1, 0.5), Action.fade_to(1, 0.5), Action.fade_to(0.1, 1), Action.fade_to(1, 0.5), Action.fade_to(0.1, 0.5), Action.fade_to(1, 0.5), Action.call(self.change_immunity)]               
                                        self.player.run_action(Action.sequence(actions))
                                if self.lives == 0:
                                        sound.play_effect('arcade:Jump_1')
                                        self.player.dying = True
        
        #This method controls whether the player has collided with any of the enemy bees. If this is the case, and the player
        #is in attack mode (and if the enemy bee in question has fully entered the hive, and is not dying), then the enemy bee dies.  
        def bee_collision2(self, bnode):
                v1 = Vector2(self.player.position.x, self.player.position.y)
                v2 = Vector2(bnode.position.x, bnode.position.y)                        

                if abs(v1 - v2) < 0.5 * (self.player.size.x + bnode.size.x) and bnode.inHive and self.player.attack and not bnode.dying: 
                        sound.play_effect('arcade:Laser_2')
                        bnode.dying = True
        
        #Controls if the player has collided with a flower power-up. In this case, the attack mode is initiated, the 
        #consequences of which depend on if the flower was white or red. 
        def flower_collision(self, flower):
                v1 = Vector2(self.player.position.x, self.player.position.y)
                v2 = Vector2(flower.position.x, flower.position.y)                      

                if abs(v1 - v2) < 0.5 * (self.player.size.x + flower.size.x): 
                        flower.run_action(Action.fade_to(0, 0.1))
                        flower.birthtime = 0
                        sound.play_effect('arcade:Powerup_1')
                        self.player.attack = True

                        if flower.farbe == 'white':
                                actions = [Action.fade_to(0.1, 0.5), Action.fade_to(1, 0.5), Action.fade_to(0.1, 1), Action.fade_to(1, 0.5), Action.fade_to(0.1, 0.5), Action.fade_to(1, 0.5), Action.fade_to(0.1, 0.5), Action.fade_to(1, 0.5), Action.fade_to(0.1, 1), Action.fade_to(1, 0.5), Action.fade_to(0.1, 0.5), Action.fade_to(1, 0.5), Action.call(self.change_attack)]     
                        elif flower.farbe == 'rot':
                                actions = [Action.call(self.double_player_size), Action.fade_to(0.1, 0.5), Action.fade_to(1, 0.5), Action.fade_to(0.1, 1), Action.fade_to(1, 0.5), Action.fade_to(0.1, 0.5), Action.fade_to(1, 0.5), Action.fade_to(0.1, 0.5), Action.fade_to(1, 0.5), Action.fade_to(0.1, 1), Action.fade_to(1, 0.5), Action.fade_to(0.1, 0.5), Action.fade_to(1, 0.5), Action.call(self.halve_player_size), Action.call(self.change_attack)]

                        self.player.child.run_action(Action.sequence(actions))

        #Checks if the player has collided with a honeycomb. In this case, the score is being updated. 
        #For every second honeycomb collected, the player grows in size. 
        def honeycomb_collision(self, honeycomb):
                v1 = Vector2(self.player.position.x, self.player.position.y)
                v2 = Vector2(honeycomb.position.x, honeycomb.position.y)                        

                if abs(v1 - v2) < 0.5 * (self.player.size.x + honeycomb.size.x): 
                        honeycomb.run_action(Action.fade_to(0, 0.1))
                        honeycomb.birthtime = -10 
                        self.player.honeycombscollected += 1
                        self.score += 1
                        self.score_label.text = str(self.score)
                        x = self.score % 2
                        if x == 0:
                                r = self.player.position.x
                                s = self.player.position.y
                                self.player.diameter += 2
                                self.update_player_size()
                                X = self.player.diameter
                                Y = X / 2
                                self.player.path = ui.Path.oval(r, s, X, X)
                                self.player.child.path = ui.Path.oval(r, s, Y, Y)

                        sound.play_effect('arcade:Coin_4')
                        if self.score > self.highscore:
                                self.highscore = self.score
                                self.save_highscore()

        def heart_collision(self, heart):
                v1 = Vector2(self.player.position.x, self.player.position.y)
                v2 = Vector2(heart.position.x, heart.position.y)                        

                if abs(v1 - v2) < 0.5 * (self.player.size.x + heart.size.x): 
                        heart.run_action(Action.fade_to(0, 0.1))
                        heart.birthtime = -10 
                        self.lives += 1
                        self.lives_label.text = str(self.lives)
                        sound.play_effect('arcade:Powerup_3')

        def lightning_collision(self, lightning):
                v1 = Vector2(self.player.position.x, self.player.position.y)
                v2 = Vector2(lightning.position.x, lightning.position.y)                        

                if abs(v1 - v2) < 0.5 * (self.player.size.x + lightning.size.x): 
                        lightning.run_action(Action.fade_to(0, 0.1))
                        sound.play_effect('arcade:Powerup_2')   
                        lightning.birthtime = -10 

                        thunderbolt = Thunderbolt(parent=self)
                        #thunderbolt.position = (100, 100)
                        self.thunderbolts.append(thunderbolt)
                        self.sort_thunderbolts()

        def mushroom_collision(self, mushroom):
                v1 = Vector2(self.player.position.x, self.player.position.y)
                v2 = Vector2(mushroom.position.x, mushroom.position.y)                  

                if abs(v1 - v2) < 0.5 * (self.player.size.x + mushroom.size.x): 
                        mushroom.run_action(Action.fade_to(0, 0.1))
                        mushroom.birthtime = -10 
                        sound.play_effect('arcade:Jump_1')
                        self.halve_player_size()
                        self.update_player_size()


        def sort_thunderbolts(self):
                for T in self.thunderbolts:
                        T.position = (20 + self.thunderbolts.index(T) * 30, 20)


        def release_thunder(self):
                        self.speed_limit = 0.5
                        self.thunder = True
                        self.time_last_thunder = self.t
                        sound.play_effect('arcade:Powerup_2')                                                           

        def show_start_menu(self):
                self.paused = True
                self.menu = MenuScene('Beehive', 'Highscore: %i' % self.highscore, ['New Game'])
                self.present_modal_scene(self.menu)

        def game_over(self):
                self.paused = True
                self.menu = MenuScene('Game Over', 'Score: %i' % self.score, ['New Game'])
                self.present_modal_scene(self.menu)

        def menu_button_selected(self, title):
                if title in ('Continue', 'New Game'):
                        self.dismiss_modal_scene()
                        self.menu = None
                        self.paused = False
                if title == 'New Game':
                        self.new_game()


if __name__ == '__main__':
        run(Game(), PORTRAIT, frame_interval = 1, show_fps=True)
