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
        # visual scale multiplier for rendering (1.0 = normal)
        self.visual_scale = 1.0
    
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            # try to use the configured asset prefix (self.type). If missing, fallback to 'player' or any available animation
            key = self.type + '/' + self.action
            try:
                self.animation = self.game.assets[key].copy()
                try:
                    # reset animation state to ensure it's not already marked done
                    self.animation.done = False
                    self.animation.frame = 0
                except Exception:
                    pass
            except Exception:
                # fallback to default player assets if available
                try:
                    self.animation = self.game.assets['player/' + self.action].copy()
                    try:
                        self.animation.done = False
                        self.animation.frame = 0
                    except Exception:
                        pass
                except Exception:
                    # final fallback: pick any animation-like asset if present
                    found = None
                    for k, v in self.game.assets.items():
                        if isinstance(k, str) and k.endswith('/' + self.action):
                            found = v
                            break
                    if found is not None:
                        try:
                            self.animation = found.copy()
                            try:
                                self.animation.done = False
                                self.animation.frame = 0
                            except Exception:
                                pass
                        except Exception:
                            self.animation = found
                    else:
                        # leave animation as-is or set to a dummy empty animation object
                        self.animation = getattr(self, 'animation', None)
        
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
        try:
            img = self.animation.img()
            if getattr(self, 'visual_scale', 1.0) != 1.0:
                vs = float(self.visual_scale)
                new_w = max(1, int(img.get_width() * vs))
                new_h = max(1, int(img.get_height() * vs))
                img = pygame.transform.scale(img, (new_w, new_h))
            surf.blit(pygame.transform.flip(img, self.flip, False), (self.pos[0] - offset[0] + int(self.anim_offset[0] * getattr(self, 'visual_scale', 1.0)), self.pos[1] - offset[1] + int(self.anim_offset[1] * getattr(self, 'visual_scale', 1.0))))
        except Exception:
            # fallback: original behavior
            try:
                surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))
            except Exception:
                pass
        
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

    def take_hit(self):
        """
        Default enemy dies immediately when hit. Return True if dead (so caller may remove it).
        """
        try:
            self.game.sfx['hit'].play()
        except Exception:
            pass
        return True

class Player(PhysicsEntity):
    def __init__(self, game, pos, size, asset_prefix='player'):
        """Player may use a custom asset prefix (e.g., 'player_ninja' or 'player_samurai').

        asset_prefix should match keys in Game.assets like 'player_ninja/idle'.
        If assets are missing, PhysicsEntity.set_action will fallback to 'player'.
        """
        super().__init__(game, asset_prefix, pos, size)
        # attack mode: 'ranged' uses shuriken/projectile, 'melee' uses sword
        self.attack_mode = 'ranged'
        # sword (melee) cooldown (frames)
        self.sword_cooldown = 20
        self.sword_cooldown_timer = 0
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
        # optional override for what primary_attack() should use: 'shuriken'|'kunai'|'sword' or None
        self.primary_attack_override = None
    
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
        
        # If an attack animation was triggered, keep it until it finishes
        if getattr(self, '_attack_override', False):
            # wall_slide always takes priority over attack animations
            if self.wall_slide:
                try:
                    self._attack_override = False
                except Exception:
                    pass
                # don't return here, let the normal logic handle wall_slide
            else:
                # animation.update() already ran in super().update; check if done
                try:
                    done = getattr(self.animation, 'done', False)
                except Exception:
                    done = False
                if done:
                    # attack finished, clear override and immediately set the next action
                    try:
                        self._attack_override = False
                    except Exception:
                        pass
                    # force clear the current action so set_action will actually change it
                    self.action = ''
                    # choose the appropriate follow-up action now so we don't remain stuck on the attack frame
                    try:
                        # prefer wall_slide/jump/run/idle in that order
                        if (self.collisions.get('right') or self.collisions.get('left')) and self.air_time > 4:
                            self.set_action('wall_slide')
                        elif self.air_time > 4:
                            self.set_action('jump')
                        elif movement[0] != 0:
                            self.set_action('run')
                        else:
                            self.set_action('idle')
                    except Exception:
                        try:
                            self.set_action('idle')
                        except Exception:
                            pass
                else:
                    # keep attack animation and skip other action changes
                    return

        # only set normal actions if not in attack override mode
        if not getattr(self, '_attack_override', False):
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
        # sword cooldown
        if getattr(self, 'sword_cooldown_timer', 0) > 0:
            self.sword_cooldown_timer = max(0, self.sword_cooldown_timer - 1)
    
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
        # only allow ranged shuriken if attack mode is ranged
        if self.attack_mode != 'ranged':
            return False
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

    def primary_attack(self):
        """Primary attack button. Behavior depends on attack_mode."""
        # allow explicit override (per-character) to map the primary button to a specific attack
        override = getattr(self, 'primary_attack_override', None)
        if override == 'kunai':
            return self.use_kunai()
        if override == 'shuriken':
            return self.use_shuriken()
        if override == 'sword':
            return self.use_sword()

        # default behavior: ranged -> shuriken, melee -> sword
        if self.attack_mode == 'ranged':
            return self.use_shuriken()
        else:
            return self.use_sword()

    def use_sword(self):
        """Melee sword attack. Does not consume items, uses a cooldown. Returns True if attack happened."""
        # unlimited melee: no required items and no cooldown gating
        # perform melee attack (same logic as use_kunai but without consuming)
        attack_rect = self.rect().copy()
        if self.flip:
            attack_rect.x -= 20
            attack_rect.width += 20
        else:
            attack_rect.width += 20

        removed = []
        # Attack regular enemies
        for enemy in self.game.enemies.copy():
            if attack_rect.colliderect(enemy.rect()):
                # call take_hit to handle HP properly
                if enemy.take_hit():
                    removed.append(enemy)
                # spawn hit effects
                for i in range(12):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 2 + 0.5
                    self.game.particles.append(Particle(self.game, 'particle', enemy.rect().center, velocity=[math.cos(angle) * speed, math.sin(angle) * speed], frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(enemy.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(enemy.rect().center, math.pi, 5 + random.random()))
        
        # Attack boss separately - but only if all enemies are dead
        if self.game.boss and attack_rect.colliderect(self.game.boss.rect()):
            if len(self.game.enemies) > 0:
                # Boss is protected by remaining enemies
                print("Boss is protected! Defeat all enemies first!")
                # Show protection effect
                for i in range(8):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 2
                    self.game.sparks.append(Spark(self.game.boss.rect().center, angle, 1 + random.random()))
                # Play a different sound to indicate protection
                try:
                    self.game.sfx['shoot'].play()  # Use shoot sound as "blocked" sound
                except Exception:
                    pass
            else:
                # All enemies defeated - boss can be damaged
                print("Player attacking boss with sword!")
                if self.game.boss.take_hit():
                    # Boss defeated - trigger win condition
                    self.game.boss = None  
                    self.game.boss_defeated = True
                # spawn hit effects for boss
                for i in range(12):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 2 + 0.5
                    self.game.particles.append(Particle(self.game, 'particle', self.game.boss.rect().center if self.game.boss else (0, 0), velocity=[math.cos(angle) * speed, math.sin(angle) * speed], frame=random.randint(0, 7)))
                if self.game.boss:
                    self.game.sparks.append(Spark(self.game.boss.rect().center, 0, 5 + random.random()))
                    self.game.sparks.append(Spark(self.game.boss.rect().center, math.pi, 5 + random.random()))
        
        for e in removed:
            try:
                self.game.enemies.remove(e)
            except Exception:
                pass
        # play knife sound if available, otherwise fallback to generic hit
        try:
            if self.game.sfx.get('knife'):
                self.game.sfx['knife'].play()
            else:
                self.game.sfx['hit'].play()
        except Exception:
            pass

        # try to play an attack animation if available in assets
        try:
            # possible keys for attack animation
            keys = [f"{self.type}/attack", f"{self.type}/slash", f"{self.type}/sword", 'player/attack', 'attack']
            attack_anim = None
            for k in keys:
                if k in self.game.assets:
                    attack_anim = self.game.assets[k]
                    break
            if attack_anim is not None:
                try:
                    # copy the animation and force non-looping so it finishes
                    new_anim = attack_anim.copy()
                    try:
                        new_anim.loop = False
                        new_anim.done = False
                        new_anim.frame = 0
                    except Exception:
                        pass
                    self.animation = new_anim
                except Exception:
                    # fallback: assign and try to ensure it won't loop
                    try:
                        attack_anim.loop = False
                        attack_anim.done = False
                        attack_anim.frame = 0
                    except Exception:
                        pass
                    self.animation = attack_anim
                try:
                    self._attack_override = True
                except Exception:
                    pass
        except Exception:
            pass

        return len(removed) > 0
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
        # Attack regular enemies
        for enemy in self.game.enemies.copy():
            if attack_rect.colliderect(enemy.rect()):
                # call take_hit to handle HP properly
                if enemy.take_hit():
                    removed.append(enemy)
                # spawn hit effects
                for i in range(12):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 2 + 0.5
                    self.game.particles.append(Particle(self.game, 'particle', enemy.rect().center, velocity=[math.cos(angle) * speed, math.sin(angle) * speed], frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(enemy.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(enemy.rect().center, math.pi, 5 + random.random()))
        
        # Attack boss separately - but only if all enemies are dead
        if self.game.boss and attack_rect.colliderect(self.game.boss.rect()):
            if len(self.game.enemies) > 0:
                # Boss is protected by remaining enemies
                print("Boss is protected! Defeat all enemies first!")
                # Show protection effect
                for i in range(6):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 1.5
                    self.game.sparks.append(Spark(self.game.boss.rect().center, angle, 1 + random.random()))
                # Play a different sound to indicate protection
                try:
                    self.game.sfx['shoot'].play()  # Use shoot sound as "blocked" sound
                except Exception:
                    pass
            else:
                # All enemies defeated - boss can be damaged
                print("Player attacking boss with kunai!")
                if self.game.boss.take_hit():
                    # Boss defeated - trigger win condition
                    self.game.boss = None
                    self.game.boss_defeated = True
                # spawn hit effects for boss
                for i in range(12):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 2 + 0.5
                    self.game.particles.append(Particle(self.game, 'particle', self.game.boss.rect().center if self.game.boss else (0, 0), velocity=[math.cos(angle) * speed, math.sin(angle) * speed], frame=random.randint(0, 7)))
                if self.game.boss:
                    self.game.sparks.append(Spark(self.game.boss.rect().center, 0, 5 + random.random()))
                    self.game.sparks.append(Spark(self.game.boss.rect().center, math.pi, 5 + random.random()))
        
        for e in removed:
            try:
                self.game.enemies.remove(e)
            except Exception:
                pass
        try:
            self.game.sfx['hit'].play()
        except Exception:
            pass
        # try to play a kunai/attack animation if available (so the attack is visible)
        try:
            keys = [f"{self.type}/kunai", f"{self.type}/attack", f"{self.type}/throw", 'player/kunai', 'player/attack', 'attack']
            attack_anim = None
            for k in keys:
                if k in self.game.assets:
                    attack_anim = self.game.assets[k]
                    break
            if attack_anim is not None:
                try:
                    new_anim = attack_anim.copy()
                    try:
                        new_anim.loop = False
                        new_anim.done = False
                        new_anim.frame = 0
                    except Exception:
                        pass
                    self.animation = new_anim
                except Exception:
                    try:
                        attack_anim.loop = False
                        attack_anim.done = False
                        attack_anim.frame = 0
                    except Exception:
                        pass
                    self.animation = attack_anim
                try:
                    self._attack_override = True
                except Exception:
                    pass
        except Exception:
            pass
        return True


class Boss:
    """A walking boss with stable movement and shooting."""
    def __init__(self, game, pos, size, hp=15):
        print(f"Boss.__init__ called at pos {pos}")
        self.game = game
        self.pos = list(pos)
        self.size = size
        self.hp = hp
        self.max_hp = hp
        self.flip = False
        self.attack_timer = 0
        self.walk_timer = 0
        self.walking = False
        self.walk_direction = 1  # 1 = right, -1 = left
        self.action = 'idle'
        self.hit_cooldown = 0  # Prevent multiple hits in short time
        self.attack_type = 1  # 1 = melee, 2 = ranged
        self.debug_timer = 0  # For debug output timing
        
        # Ground Y position - boss will stay at this Y level 
        # Boss spawn pos should be center position on platform
        self.ground_y = self.pos[1]  # Keep boss at spawn center position
        
        # try to use boss assets first, fallback to enemy assets  
        self.animation = None
        print("Boss: Trying to load initial animation...")
        
        # Try boss/idle first - MUST use .copy() to avoid shared frame counters
        if 'boss/idle' in self.game.assets and self.game.assets['boss/idle'] is not None:
            try:
                self.animation = self.game.assets['boss/idle'].copy()
                print("Boss: Using boss/idle animation (copied)")
            except Exception as e:
                print(f"Boss: Failed to copy boss/idle, using direct: {e}")
                self.animation = self.game.assets['boss/idle']
        
        # Fallback to enemy/idle
        if self.animation is None and 'enemy/idle' in self.game.assets:
            try:
                self.animation = self.game.assets['enemy/idle'].copy()
                print("Boss: Using enemy/idle animation (copied)")
            except Exception as e:
                print(f"Boss: Failed to copy enemy/idle, using direct: {e}")
                self.animation = self.game.assets['enemy/idle']
                
        if self.animation is None:
            print("Boss: WARNING - No animation loaded! Creating emergency fallback...")
            # Emergency fallback - create a simple animation from any available asset
            for key in ['boss/idle', 'boss/walk', 'enemy/idle', 'enemy/run']:
                if key in self.game.assets and self.game.assets[key] is not None:
                    self.animation = self.game.assets[key]
                    print(f"Boss: Emergency fallback using {key}")
                    break
                    
        if self.animation is None:
            print("Boss: CRITICAL ERROR - Still no animation after all fallbacks!")
        
        # Debug: print available boss animations
        boss_anims = [key for key in self.game.assets.keys() if key.startswith('boss/')]
        print(f"Available boss animations: {boss_anims}")
        
        # Debug: print all available assets
        all_assets = list(self.game.assets.keys())
        print(f"All available assets: {all_assets}")
        
        # If no boss animations available, create fallback references
        if not boss_anims:
            print("No boss animations found, creating fallbacks from enemy animations...")
            if 'enemy/idle' in self.game.assets:
                self.game.assets['boss/idle'] = self.game.assets['enemy/idle']
                print("Created boss/idle fallback")
            if 'enemy/run' in self.game.assets:
                self.game.assets['boss/walk'] = self.game.assets['enemy/run'] 
                self.game.assets['boss/run'] = self.game.assets['enemy/run']
                self.game.assets['boss/attack1'] = self.game.assets['enemy/run']
                self.game.assets['boss/attack2'] = self.game.assets['enemy/run']
                print("Created boss/walk, boss/run, boss/attack1, boss/attack2 fallbacks")
            if 'enemy/idle' in self.game.assets:
                self.game.assets['boss/hurt'] = self.game.assets['enemy/idle']
                print("Created boss/hurt fallback")
                
            # Update boss_anims list after creating fallbacks
            boss_anims = [key for key in self.game.assets.keys() if key.startswith('boss/')]
            print(f"Boss animations after fallback: {boss_anims}")
                
        print(f"Boss initialized successfully at {self.pos}")
                
    def rect(self):
        # Boss rect should match render position (centered)
        return pygame.Rect(self.pos[0] - self.size[0]//2, self.pos[1] - self.size[1]//2, self.size[0], self.size[1])
        
    def set_action(self, action):
        """Set animation action."""
        if action != self.action:
            self.action = action
            print(f"Boss trying to set action: {action}")
            
            # Use .copy() to get independent animation instance
            asset_key = f'boss/{action}'
            if asset_key in self.game.assets and self.game.assets[asset_key] is not None:
                try:
                    self.animation = self.game.assets[asset_key].copy()
                    print(f"Boss using animation: {asset_key} (copied)")
                except:
                    self.animation = self.game.assets[asset_key]
                    print(f"Boss using animation: {asset_key} (direct)")
            else:
                print(f"No {asset_key} found, checking alternatives...")
                # If boss animation not available, try alternatives
                if action in ['attack1', 'attack2']:
                    # For attack, try different boss animations first
                    alternatives = ['boss/run', 'boss/walk', 'boss/idle', 'enemy/idle']
                    for alt in alternatives:
                        if alt in self.game.assets and self.game.assets[alt] is not None:
                            try:
                                self.animation = self.game.assets[alt].copy()
                                print(f"Boss using fallback animation: {alt} (copied)")
                            except:
                                self.animation = self.game.assets[alt]
                                print(f"Boss using fallback animation: {alt} (direct)")
                            break
                else:
                    # For other actions, use boss/idle or enemy/idle
                    if 'boss/idle' in self.game.assets and self.game.assets['boss/idle'] is not None:
                        try:
                            self.animation = self.game.assets['boss/idle'].copy()
                            print("Boss using boss/idle fallback (copied)")
                        except:
                            self.animation = self.game.assets['boss/idle']
                            print("Boss using boss/idle fallback (direct)")
                    elif 'enemy/idle' in self.game.assets and self.game.assets['enemy/idle'] is not None:
                        try:
                            self.animation = self.game.assets['enemy/idle'].copy()
                            print("Boss using enemy/idle fallback (copied)")
                        except:
                            self.animation = self.game.assets['enemy/idle']
                            print("Boss using enemy/idle fallback (direct)")
                        
            # Final check
            if self.animation is None:
                print("Boss: ERROR - No animation set after set_action!")

    def update(self, tilemap, movement=(0, 0)):
        """Boss with controlled walking movement using walk animation."""
        # Increase debug timer
        self.debug_timer += 1
        
        # Reduce hit cooldown
        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1
            
        # Walking behavior timer
        self.walk_timer += 1
        
        # Change walking state every 3 seconds (180 frames at 60fps)
        if self.walk_timer >= 180:
            self.walk_timer = 0
            self.walking = not self.walking
            
            if self.walking:
                # Change direction randomly when starting to walk
                self.walk_direction = random.choice([-1, 1])
                # Check if walk animation exists, otherwise use idle
                if 'boss/walk' in self.game.assets:
                    self.set_action('walk')
                else:
                    # No walk animation, just use idle
                    self.set_action('idle')
                    print("Warning: No boss/walk animation found, using idle")
            else:
                self.set_action('idle')
        
        # Move boss if walking
        if self.walking:
            # Simple horizontal movement - stay on ground level
            new_x = self.pos[0] + self.walk_direction * 0.8  # walking speed
            
            # Keep boss within bounds (map boundaries)
            if new_x >= 100 and new_x <= 600:
                self.pos[0] = new_x
            else:
                # Hit boundary - reverse direction
                self.walk_direction *= -1
                
            # Boss sprite seems to be drawn backwards - use opposite flip logic
            # walk_direction: 1 = right, -1 = left  
            self.flip = self.walk_direction > 0  # Flip when going right (boss sprite is backwards)

            
        # ALWAYS force boss to stay on ground - prevent falling
        self.pos[1] = self.ground_y
        
        # Attack timer
        self.attack_timer += 1
        
        # Update animation if available
        if self.animation:
            try:
                self.animation.update()

                    
                # If attack or hurt animation is done, switch back to walking/idle
                if (self.action in ['attack1', 'attack2', 'hurt']) and hasattr(self.animation, 'done') and self.animation.done:
                    if self.walking:
                        self.set_action('walk')
                    else:
                        self.set_action('idle')
            except Exception as e:
                if self.debug_timer % 60 == 0:
                    print(f"Animation update error: {e}")
        
        # Attack every 120 frames (2 seconds at 60fps)
        if self.attack_timer >= 120:
            self.attack_timer = 0
            # Calculate direction and distance to player
            dis_x = self.game.player.pos[0] - self.pos[0]
            dis_y = self.game.player.pos[1] - self.pos[1]
            distance = math.sqrt(dis_x*dis_x + dis_y*dis_y)
            
            # Boss sprite seems backwards - try opposite flip  
            self.flip = dis_x > 0  # Flip when player is on right (boss sprite backwards)
            if self.animation:
                current_frame = getattr(self.animation, 'frame', 0) // getattr(self.animation, 'img_duration', 1)
                print(f"Boss: distance={distance:.1f}, action={self.action}, frame={current_frame}, flip={self.flip}")

            
            # Choose attack type based on distance
            print(f"Boss choosing attack: distance={distance:.1f}px to player")
            if distance < 80:  # Close range - melee attack
                print("→ Using MELEE attack (close range)")
                self.attack_type = 1
                self.melee_attack()
            elif distance < 300:  # Medium/long range - ranged attack
                print("→ Using RANGED attack (long range)")
                self.attack_type = 2  
                self.ranged_attack()
            else:
                print("→ Player too far, no attack")
    
    def melee_attack(self):
        """Boss melee attack - damages player if in range."""
        print("🗡️  BOSS MELEE ATTACK!")
        
        # Use attack1 animation for melee attack
        self.set_action('attack1')
        
        # Create attack area in front of boss
        attack_rect = self.rect().copy()
        if self.flip:  # facing right
            attack_rect.x += self.size[0]
            attack_rect.width = 30
        else:  # facing left
            attack_rect.x -= 30
            attack_rect.width = 30
        attack_rect.height += 10
        attack_rect.y -= 5
        
        # Check if player is hit
        if attack_rect.colliderect(self.game.player.rect()):
            print("Boss melee hit player!")
            # Damage player (you can adjust this)
            self.game.player.take_hit()
            
            # Screen shake
            self.game.screenshake = max(20, self.game.screenshake)
            
            # Spawn hit effects on player
            for i in range(15):
                angle = random.random() * math.pi * 2
                speed = random.random() * 3 + 1
                self.game.sparks.append(Spark(self.game.player.rect().center, angle, 3 + random.random()))
                self.game.particles.append(Particle(self.game, 'particle', self.game.player.rect().center, velocity=[math.cos(angle) * speed, math.sin(angle) * speed], frame=random.randint(0, 7)))
        
        try:
            self.game.sfx['hit'].play()
        except Exception:
            pass
    
    def ranged_attack(self):
        """Boss ranged attack - shoots projectile at player."""
        print("🏹 BOSS RANGED ATTACK!")
        
        # Use attack2 animation for ranged attack
        self.set_action('attack2')
        
        # Calculate direction to player
        dis_x = self.game.player.pos[0] - self.pos[0]
        dis_y = self.game.player.pos[1] - self.pos[1]
        
        try:
            self.game.sfx['shoot'].play()
        except Exception:
            pass
            
        # Shoot towards player
        dir_x = -1 if dis_x < 0 else 1
        
        # Create projectile
        start_pos = [self.rect().centerx, self.rect().centery]
        self.game.projectiles.append([start_pos, dir_x * 1.5, 0])
        
        # Spawn effects
        for i in range(4):
            angle = random.random() - 0.5 + (math.pi if dir_x < 0 else 0)
            self.game.sparks.append(Spark(start_pos, angle, 2 + random.random()))
        
        # Handle dash collision - take damage (only when player is actually dashing)
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                print("Boss hit by player dash!")  # Debug info
                if self.take_hit():
                    return True  # boss died
        
        return False  # boss still alive

    def take_hit(self):
        """Reduce HP. Return True when dead."""
        # Check hit cooldown to prevent multiple hits
        if self.hit_cooldown > 0:
            print("Boss hit blocked by cooldown")
            return False  # Still on cooldown, no damage
            
        # Apply damage and set cooldown
        self.hp -= 1
        self.hit_cooldown = 30  # 0.5 second cooldown at 60fps
        
        # Force hurt animation regardless of current action
        print(f"Boss hit! HP: {self.hp}/{self.max_hp} - Forcing hurt animation")
        
        # Always try to show hurt animation and reset it
        if 'boss/hurt' in self.game.assets and self.game.assets['boss/hurt'] is not None:
            self.action = 'hurt'  # Force change action
            self.animation = self.game.assets['boss/hurt']
            # Reset animation to play from beginning
            self.animation.frame = 0
            self.animation.done = False
            print("Boss using boss/hurt animation (reset)")
        elif 'enemy/hurt' in self.game.assets and self.game.assets['enemy/hurt'] is not None:
            self.action = 'hurt'  # Force change action  
            self.animation = self.game.assets['enemy/hurt']
            # Reset animation to play from beginning
            self.animation.frame = 0
            self.animation.done = False
            print("Boss using enemy/hurt animation (reset)")
        else:
            print("No hurt animation available")
        
        try:
            self.game.sfx['hit'].play()
        except Exception:
            pass
        # spawn smaller feedback
        for i in range(8):
            angle = random.random() * math.pi * 2
            speed = random.random() * 2
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle) * speed, math.sin(angle) * speed], frame=random.randint(0, 7)))
        self.game.sparks.append(Spark(self.rect().center, 0, 3 + random.random()))

        if self.hp <= 0:
            print("Boss defeated!")  # Debug info
            # stronger death effect
            for i in range(40):
                angle = random.random() * math.pi * 2
                speed = random.random() * 5
                self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
            return True
        return False

    def render(self, surf, offset=(0, 0)):
        """Render walking boss."""
        # Debug timer is now handled in update() method
            
        if self.debug_timer % 60 == 0:
            print(f"Boss render: pos={self.pos}, animation={self.animation}, action={self.action}")
            if self.animation:
                print(f"Animation type: {type(self.animation)}")
            
        # Always draw the boss - use purple rectangle if no animation
        try:
            # Boss pos is center position, adjust for top-left draw position
            draw_pos = (self.pos[0] - offset[0] - self.size[0]//2, self.pos[1] - offset[1] - self.size[1]//2)
            if self.animation:
                try:
                    img = self.animation.img()
                    if img is None:
                        raise Exception("animation.img() returned None")
                    
                    # Scale down the boss sprite if it's too big
                    original_size = img.get_size()
                    if original_size[0] > 32 or original_size[1] > 32:
                        # Scale down large sprites to max 32x32
                        scale_factor = min(32/original_size[0], 32/original_size[1])
                        new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                        img = pygame.transform.scale(img, new_size)
                    
                    final_img = pygame.transform.flip(img, self.flip, False)
                    surf.blit(final_img, draw_pos)
                        
                except Exception as e:
                    if self.debug_timer % 60 == 0:
                        print(f"Boss animation.img() error: {e}")
                    # Draw fallback rectangle for animation error
                    rect = pygame.Rect(draw_pos[0], draw_pos[1], self.size[0], self.size[1])
                    pygame.draw.rect(surf, (255, 0, 255), rect)  # Magenta for animation error
            else:
                # No animation available - draw colored rectangle
                rect = pygame.Rect(draw_pos[0], draw_pos[1], self.size[0], self.size[1])
                pygame.draw.rect(surf, (150, 50, 150), rect)  # Purple boss
                
            # No indicator rectangle needed
            
        except Exception as e:
            # Always have a fallback visual - centered position
            rect = pygame.Rect(self.pos[0] - offset[0] - self.size[0]//2, self.pos[1] - offset[1] - self.size[1]//2, self.size[0], self.size[1])
            pygame.draw.rect(surf, (255, 0, 0), rect)  # Red emergency rectangle
            print(f"Boss render error: {e}")
            
        # Draw health bar above boss - use same position calculation as draw_pos
        try:
            w = self.size[0]
            hp_ratio = max(0, self.hp / max(1, self.max_hp))
            bar_w = int(w * hp_ratio)
            bar_h = 6
            # Use same centering logic as draw_pos
            bar_x = draw_pos[0] - 2  # Align with indicator
            bar_y = draw_pos[1] - 20  # Above the indicator
            # Background bar (dark red)
            pygame.draw.rect(surf, (80, 20, 20), (bar_x, bar_y, w + 4, bar_h))
            # HP bar (green to red based on HP)
            if hp_ratio > 0.5:
                color = (30, 200, 30)   # Green
            elif hp_ratio > 0.2:
                color = (200, 150, 30)  # Orange  
            else:
                color = (200, 30, 30)   # Red
            if bar_w > 0:
                pygame.draw.rect(surf, color, (bar_x, bar_y, bar_w + 4, bar_h))
            # White border
            pygame.draw.rect(surf, (255, 255, 255), (bar_x, bar_y, w + 4, bar_h), 1)
        except Exception:
            pass