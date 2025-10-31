import math
import random

import pygame

from scripts.particle import Particle
from scripts.spark import Spark

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action('idle')
        
        self.last_movement = [0, 0]
    
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()
        
    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y
                
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
            
        self.last_movement = movement
        
        self.velocity[1] = min(5, self.velocity[1] + 0.1)
        
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0
            
        self.animation.update()
        
    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))
        
class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)
        
        self.walking = 0
        
    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if (self.collisions['right'] or self.collisions['left']):
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)
            if not self.walking:
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if (abs(dis[1]) < 16):
                    if (self.flip and dis[0] < 0):
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))
                    if (not self.flip and dis[0] > 0):
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)
        
        super().update(tilemap, movement=movement)
        
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
            
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx['hit'].play()
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
                return True
            
    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)
        
        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False), (self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0], self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        self.jumps = 1
        self.wall_slide = False
        self.dashing = 0
        # health / hit tracking (5 hits -> death by default)
        self.hits = 0
        self.max_hits = 5
        # item counters
        self.shuriken_count = 0
        # replace sword with kunai (throwable/short attack with cooldown)
        self.kunai_count = 0
        self.kunai_cooldown = 30  # frames (at 60fps -> 0.5s)
        self.kunai_cooldown_timer = 0
    
    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)
        
        self.air_time += 1
        
        if self.air_time > 120:
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1
        
        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1
            
        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')
        
        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')
        
        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
                
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
        # cooldown timers
        if hasattr(self, 'kunai_cooldown_timer') and self.kunai_cooldown_timer > 0:
            self.kunai_cooldown_timer = max(0, self.kunai_cooldown_timer - 1)
    
    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)
            
    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
                
        elif self.jumps:
            self.velocity[1] = -3
            self.jumps -= 1
            self.air_time = 5
            return True
    
    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60

    def take_hit(self):
        """
        Call when the player is hit. Increment hit counter, spawn effects and trigger death when hits >= max_hits.
        """
        self.hits += 1
        # play hit sfx and screen shake
        try:
            self.game.sfx['hit'].play()
        except Exception:
            pass
        self.game.screenshake = max(16, self.game.screenshake)

        # visual feedback: sparks/particles similar to projectile hit
        for i in range(30):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5
            self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0,7)))

        # if reached max hits, start death sequence (reuse existing game.dead flow)
        if self.hits >= self.max_hits:
            # start the dead counter so Game will do transition/reload
            self.game.dead += 1

    def give_item(self, item, amount=1):
        """Add items to player inventory. item: 'shuriken' or 'kunai'."""
        if item == 'shuriken':
            self.shuriken_count += amount
        elif item == 'kunai':
            self.kunai_count += amount

    def use_shuriken(self):
        """Throw a shuriken if available. Returns True if thrown."""
        if self.shuriken_count <= 0:
            return False
        self.shuriken_count -= 1
        # spawn a projectile from the player
        dir_x = -1 if self.flip else 1
        start = [self.rect().centerx + ( -6 if self.flip else 6), self.rect().centery]
        # use same format as Game.projectiles: [[x,y], direction, timer]
        self.game.projectiles.append([start, dir_x * 3.5, 0])
        # small effect
        for i in range(6):
            angle = random.random() * math.pi * 2
            speed = random.random() * 1.5
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle) * speed, math.sin(angle) * speed], frame=random.randint(0, 7)))
        try:
            self.game.sfx['shoot'].play()
        except Exception:
            pass
        return True
    def use_kunai(self):
        """Use a kunai attack if available and not on cooldown.
        Kunai acts as a short-range attack (like previous sword) but has a cooldown.
        Returns True if used."""
        if self.kunai_count <= 0:
            return False
        if self.kunai_cooldown_timer > 0:
            return False
        # consume one kunai and start cooldown
        self.kunai_count -= 1
        self.kunai_cooldown_timer = self.kunai_cooldown

        # short range attack like sword: hit enemies in front
        attack_rect = self.rect().copy()
        if self.flip:
            attack_rect.x -= 20
            attack_rect.width += 20
        else:
            attack_rect.width += 20

        removed = []
        for enemy in self.game.enemies.copy():
            if attack_rect.colliderect(enemy.rect()):
                removed.append(enemy)
                for i in range(12):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 2 + 0.5
                    self.game.particles.append(Particle(self.game, 'particle', enemy.rect().center, velocity=[math.cos(angle) * speed, math.sin(angle) * speed], frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(enemy.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(enemy.rect().center, math.pi, 5 + random.random()))
        for e in removed:
            try:
                self.game.enemies.remove(e)
            except Exception:
                pass
        try:
            self.game.sfx['hit'].play()
        except Exception:
            pass
        return True