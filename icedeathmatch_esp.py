# (see https://ballistica.net/wiki/meta-tag-system)
# ba_meta require api 8

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1lib.actor.bomb import Blast, Bomb, BombFactory, ExplodeHitMessage
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.spaz import BombDiedMessage
from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.game.deathmatch import DeathMatchGame
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.powerupbox import _TouchedMessage


if TYPE_CHECKING:
    from typing import Any, Sequence


class Blast(bs.Actor):

    def __init__(
        self,
        position: Sequence[float] = (0.0, 1.0, 0.0),
        velocity: Sequence[float] = (0.0, 0.0, 0.0),
        blast_radius: float = 2.0,
        blast_type: str = 'normal',
        source_player: bs.Player | None = None,
        hit_type: str = 'explosion',
        hit_subtype: str = 'normal',
    ):
        super().__init__()

        shared = SharedObjects.get()
        factory = BombFactory.get()

        self.blast_type = blast_type
        self._source_player = source_player
        self.hit_type = hit_type
        self.hit_subtype = hit_subtype
        self.radius = blast_radius

        # Set our position a bit lower so we throw more things upward.
        rmats = (factory.blast_material, shared.attack_material)
        self.node = bs.newnode(
            'region',
            delegate=self,
            attrs={
                'position': (position[0], position[1] - 0.1, position[2]),
                'scale': (self.radius, self.radius, self.radius),
                'type': 'sphere',
                'materials': rmats,
            },
        )

        bs.timer(0.05, self.node.delete)

        # Throw in an explosion and flash.
        # evel = (velocity[0], max(-1.0, velocity[1]), velocity[2])
        # explosion = bs.newnode(
        #     'explosion',
        #     attrs={
        #         'position': position,
        #         'velocity': evel,
        #         'radius': self.radius,
        #         'big': (self.blast_type == 'tnt'),
        #     },
        # )
        # explosion.color = (0, 0.05, 0.4)

        # bs.timer(1.0, explosion.delete)

        bs.emitfx(
            position=position,
            velocity=velocity,
            count=int(4.0 + random.random() * 4),
            emit_type='tendrils',
            tendril_type='ice',
        )
        bs.emitfx(
            position=position,
            emit_type='distortion',
            spread=1.0 if self.blast_type == 'tnt' else 2.0,
        )

        # And emit some shrapnel.
        if self.blast_type == 'ice':

            def emit() -> None:
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=30,
                    spread=2.0,
                    scale=0.4,
                    chunk_type='ice',
                    emit_type='stickers',
                )

            # It looks better if we delay a bit.
            bs.timer(0.05, emit)

        elif self.blast_type == 'sticky':

            def emit() -> None:
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(4.0 + random.random() * 8),
                    spread=0.7,
                    chunk_type='slime',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(4.0 + random.random() * 8),
                    scale=0.5,
                    spread=0.7,
                    chunk_type='slime',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=15,
                    scale=0.6,
                    chunk_type='slime',
                    emit_type='stickers',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=20,
                    scale=0.7,
                    chunk_type='spark',
                    emit_type='stickers',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(6.0 + random.random() * 12),
                    scale=0.8,
                    spread=1.5,
                    chunk_type='spark',
                )

            # It looks better if we delay a bit.
            bs.timer(0.05, emit)

        elif self.blast_type == 'impact':

            def emit() -> None:
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(4.0 + random.random() * 8),
                    scale=0.8,
                    chunk_type='metal',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(4.0 + random.random() * 8),
                    scale=0.4,
                    chunk_type='metal',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=20,
                    scale=0.7,
                    chunk_type='spark',
                    emit_type='stickers',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(8.0 + random.random() * 15),
                    scale=0.8,
                    spread=1.5,
                    chunk_type='spark',
                )

            # It looks better if we delay a bit.
            bs.timer(0.05, emit)

        else:  # Regular or land mine bomb shrapnel.

            def emit() -> None:
                if self.blast_type != 'tnt':
                    bs.emitfx(
                        position=position,
                        velocity=velocity,
                        count=int(4.0 + random.random() * 8),
                        chunk_type='rock',
                    )
                    bs.emitfx(
                        position=position,
                        velocity=velocity,
                        count=int(4.0 + random.random() * 8),
                        scale=0.5,
                        chunk_type='rock',
                    )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=30,
                    scale=1.0 if self.blast_type == 'tnt' else 0.7,
                    chunk_type='spark',
                    emit_type='stickers',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(18.0 + random.random() * 20),
                    scale=1.0 if self.blast_type == 'tnt' else 0.8,
                    spread=1.5,
                    chunk_type='spark',
                )

                # TNT throws splintery chunks.
                if self.blast_type == 'tnt':

                    def emit_splinters() -> None:
                        bs.emitfx(
                            position=position,
                            velocity=velocity,
                            count=int(20.0 + random.random() * 25),
                            scale=0.8,
                            spread=1.0,
                            chunk_type='splinter',
                        )

                    bs.timer(0.01, emit_splinters)

                # Every now and then do a sparky one.
                if self.blast_type == 'tnt' or random.random() < 0.1:

                    def emit_extra_sparks() -> None:
                        bs.emitfx(
                            position=position,
                            velocity=velocity,
                            count=int(10.0 + random.random() * 20),
                            scale=0.8,
                            spread=1.5,
                            chunk_type='spark',
                        )

                    bs.timer(0.02, emit_extra_sparks)

            # It looks better if we delay a bit.
            bs.timer(0.05, emit)

        lcolor = (0.6, 0.6, 1.0)
        light = bs.newnode(
            'light',
            attrs={
                'position': position,
                'volume_intensity_scale': 10.0,
                'color': lcolor,
            },
        )

        scl = random.uniform(0.6, 0.9)
        scorch_radius = light_radius = self.radius
        if self.blast_type == 'tnt':
            light_radius *= 1.4
            scorch_radius *= 1.15
            scl *= 3.0

        iscale = 1.6
        bs.animate(
            light,
            'intensity',
            {
                0: 2.0 * iscale,
                scl * 0.02: 0.1 * iscale,
                scl * 0.025: 0.2 * iscale,
                scl * 0.05: 17.0 * iscale,
                scl * 0.06: 5.0 * iscale,
                scl * 0.08: 4.0 * iscale,
                scl * 0.2: 0.6 * iscale,
                scl * 2.0: 0.00 * iscale,
                scl * 3.0: 0.0,
            },
        )
        bs.animate(
            light,
            'radius',
            {
                0: light_radius * 0.2,
                scl * 0.05: light_radius * 0.55,
                scl * 0.1: light_radius * 0.3,
                scl * 0.3: light_radius * 0.15,
                scl * 1.0: light_radius * 0.05,
            },
        )
        bs.timer(scl * 3.0, light.delete)

        # Make a scorch that fades over time.
        scorch = bs.newnode(
            'scorch',
            attrs={
                'position': position,
                'size': scorch_radius * 0.5,
                'big': (self.blast_type == 'tnt'),
            },
        )
        scorch.color = (1, 1, 1.5)

        bs.animate(scorch, 'presence', {3.000: 1, 13.000: 0})
        bs.timer(13.0, scorch.delete)

        factory.hiss_sound.play(0.8, position=light.position)

        lpos = light.position
        # factory.random_explode_sound().play(position=lpos)
        # factory.debris_fall_sound.play(position=lpos)

        bs.camerashake(intensity=5.0 if self.blast_type == 'tnt' else 1.0)

        # TNT is more epic.
        if self.blast_type == 'tnt':
            factory.random_explode_sound().play(position=lpos)

            def _extra_boom() -> None:
                factory.random_explode_sound().play(position=lpos)

            bs.timer(0.25, _extra_boom)

            def _extra_debris_sound() -> None:
                factory.debris_fall_sound.play(position=lpos)
                factory.wood_debris_fall_sound.play(position=lpos)

            bs.timer(0.4, _extra_debris_sound)

    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired

        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()

        elif isinstance(msg, ExplodeHitMessage):
            node = bs.getcollision().opposingnode
            assert self.node
            nodepos = self.node.position
            mag = 1000.0
            if self.blast_type == 'ice':
                mag *= 1.0
            elif self.blast_type == 'land_mine':
                mag *= 2.5
            elif self.blast_type == 'tnt':
                mag *= 2.0
            node.handlemessage(
                bs.HitMessage(
                    pos=nodepos,
                    velocity=(0, 0, 0),
                    magnitude=mag,
                    hit_type=self.hit_type,
                    hit_subtype=self.hit_subtype,
                    radius=self.radius,
                    source_player=bs.existing(self._source_player),
                )
            )
            BombFactory.get().freeze_sound.play(1, position=nodepos)
            node.handlemessage(bs.FreezeMessage())
        else:
            return super().handlemessage(msg)
        return None
    

class Bomb(Bomb):

    def explode(self) -> None:
        if self._exploded:
            return
        self._exploded = True
        if self.node:
            blast = Blast(
                position=self.node.position,
                velocity=self.node.velocity,
                blast_radius=self.blast_radius,
                blast_type=self.bomb_type,
                source_player=bs.existing(self._source_player),
                hit_type=self.hit_type,
                hit_subtype=self.hit_subtype,
            ).autoretain()
            for callback in self._explode_callbacks:
                callback(self, blast)
        bs.timer(0.001, bs.WeakCall(self.handlemessage, bs.DieMessage()))
        

class Power(bs.Actor):

    def __init__(
        self,
        position: Sequence[float] = (0.0, 1.0, 0.0),
        velocity: Sequence[float] = (0.0, 0.0, 0.0),
        max_position: float = 1.0,
        mesh_scale: float = 1.0,
    ) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self._time = 0
        self._max_position = max_position
        self._circle_timer: bs.Timer = None
        self.mesh_index = 0
        self._touched = False
        self._position = position
        self._mesh_scale = mesh_scale
        no_collision = bs.Material()
        no_collision.add_actions(
            actions=(
                ('modify_part_collision', 'collide', False),
                ('modify_part_collision', 'physical', False),
            )
        )
        no_collision.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', _TouchedMessage())
            )
        )
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': position,
                'velocity': velocity,
                'mesh': bs.getmesh('flash'),
                'color_texture': bs.gettexture('tipTopBGColor'),
                'body': 'sphere',
                'body_scale': 1.0,
                'mesh_scale': mesh_scale,
                'shadow_size': 0.0,
                'gravity_scale': 0,
                'reflection': 'powerup',
                'reflection_scale': [5.0],
                'materials': [no_collision],
            },
        )
        self.circle = bs.newnode(
            'locator',
            owner=self.node,
            attrs={
                'shape': 'circleOutline',
                'position': position,
                'color': (0, 0.9, 1),
                'opacity': 0.0,
                'draw_beauty': False,
                'additive': True,
            },
        )
        self.circle2 = bs.newnode(
            'locator',
            owner=self.node,
            attrs={
                'shape': 'circleOutline',
                'position': position,
                'color': (0, 0.9, 1),
                'opacity': 0.0,
                'draw_beauty': False,
                'additive': True,
            },
        )
        self.light = bs.newnode(
            'light',
            owner=self.node,
            attrs={
                'volume_intensity_scale': 10.0,
                'color': (0.6, 0.6, 1.0),
                'intensity': 0.0,
                'radius': 0.0,
            },
        )
        self._update()

    def _update(self) -> None:
        self.update_time()
        self._circle_timer = bs.Timer(
            1.0, self.update_time, repeat=True)
        self.circle_animation()
        bs.timer(0.8, self.do_sound, repeat=True)
        bs.animate_array(self.node, 'position', 3, {
            0.0: (
                self._position[0],
                self._position[1] + self._max_position,
                self._position[2],
            ),
            7.0: (
                self._position[0],
                self._position[1] + 0.6,
                self._position[2],
            ),
        })
        bs.timer(7.0, self.mesh_position)
        self.change_mesh()
        bs.timer(0.8, self.change_mesh, repeat=True)
        bs.timer(0.1, self.efx, repeat=True)

    def update_time(self) -> None:
        self._time += 1
        if self._time > 7:
            self._circle_timer = None

    def circle_animation(self) -> None:
        self.animate_circle()
        bs.timer(1.3, self.animate_circle2)
        bs.timer(2.6, self.animate_circle, repeat=True)
        bs.timer(1.3, lambda: bs.timer(
            2.6, self.animate_circle2, repeat=True))

    def animate_circle(self) -> None:
        if not self.node:
            return
        bs.animate_array(self.circle, 'size', 1, {
            0.0: [0.0],
            2.6: [1.5],
        })
        bs.animate(self.circle, 'opacity', {
            0.0: 0.0,
            0.2: (0.5 * self._time) / 7,
            1.8: (0.5 * self._time) / 7,
            2.6: 0.0,
        })

    def animate_circle2(self) -> None:
        if not self.node:
            return
        bs.animate_array(self.circle2, 'size', 1, {
            0.0: [0.0],
            2.6: [1.5],
        })
        bs.animate(self.circle2, 'opacity', {
            0.0: 0.0,
            0.2: (0.5 * self._time) / 7,
            1.8: (0.5 * self._time) / 7,
            2.6: 0.0,
        })

    def do_sound(self) -> None:
        if not self.node:
            return
        sound = bs.getsound('sparkle02')
        sound.play(0.2, position=self.node.position)
        
    def efx(self) -> None:
        if not self.node:
            return
        bs.emitfx(
            position=self.node.position,
            emit_type='fairydust',
        )
        
    def mesh_position(self) -> None:
        if not self.node:
            return
        bs.animate_array(self.node, 'position', 3, {
            0.0: (
                self._position[0],
                self._position[1] + 0.6,
                self._position[2],
            ),
            0.15: (
                self._position[0],
                self._position[1] + 0.55,
                self._position[2],
            ),
            0.4: (
                self._position[0],
                self._position[1] + 0.5,
                self._position[2],
            ),
            0.65: (
                self._position[0],
                self._position[1] + 0.55,
                self._position[2],
            ),
            0.8: (
                self._position[0],
                self._position[1] + 0.6,
                self._position[2],
            ),
            0.95: (
                self._position[0],
                self._position[1] + 0.65,
                self._position[2],
            ),
            1.2: (
                self._position[0],
                self._position[1] + 0.7,
                self._position[2],
            ),
            1.45: (
                self._position[0],
                self._position[1] + 0.65,
                self._position[2],
            ),
            1.6: (
                self._position[0],
                self._position[1] + 0.6,
                self._position[2],
            ),
        }, loop=True)
        
    def change_mesh(self) -> None:
        if not self.node:
            return
        if self.mesh_index == 0:
            self.node.mesh = bs.getmesh('flash')
            scale = 0.9 * self._mesh_scale
        elif self.mesh_index == 1:
            self.node.mesh = bs.getmesh('box')
            scale = 1.0 * self._mesh_scale
        elif self.mesh_index == 2:
            self.node.mesh = bs.getmesh('frostyPelvis')
            scale = 2.0 * self._mesh_scale
        bs.animate(self.node, 'mesh_scale', {
            0.0: 0,
            0.1: scale,
            0.7: scale,
            0.8: 0.0,
        })
        self.mesh_index += 1
        if self.mesh_index > 2:
            self.mesh_index = 0
    
    def do_flash(self) -> None:
        bs.animate(self.light, 'intensity', {
            0.0: 0.0,
            0.1: 0.5,
            0.2: 0.0,
        })
        bs.animate(self.light, 'radius', {
            0.0: 0.0,
            0.1: 0.2,
            0.2: 0.0,
        })

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.OutOfBoundsMessage):
            if not self.node:
                return
            self.node.delete()
        elif isinstance(msg, bs.DieMessage):
            if self.node:
                if msg.immediate:
                    self.node.delete()
                else:
                    bs.animate(self.node, 'mesh_scale', {0: 1, 0.1: 0})
                    bs.timer(0.1, self.node.delete)
        elif isinstance(msg, _TouchedMessage):
            if self._touched:
                return
            self._touched = True
            node = bs.getcollision().opposingnode
            node.handlemessage(
                bs.PowerupMessage('super_ice', sourcenode=self.node)
            )
            sound = bs.getsound('sparkle03')
            sound.play(0.5, position=self.node.position)
            self.activity._update_power()
            self.handlemessage(bs.DieMessage())
        else:
            super().handlemessage(msg)


class PlayerSpaz(PlayerSpaz):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ice_power: bool = False
        self._ice_power_timer: bs.Timer = None
        self._ice_power_efx_timer: bs.Timer = None
        self._ice_power_flash_timer: bs.Timer = None
        self._ice_power_wear_timer: bs.Timer = None
        self._old_impact_scale: Any = None
        self._old_color: Any = None
        self._old_highlight: Any = None
        self._old_color_texture: Any = None
        self._old_color_mask_texture: Any = None
        self._hockey_material = bs.Material()
        self._hockey_material.add_actions(
            actions=('modify_part_collision', 'friction', 500),
        )
        self._ice_light = bs.newnode(
            'light',
            owner=self.node,
            attrs={
                'volume_intensity_scale': 10.0,
                'color': (0.6, 0.6, 1.0),
                'intensity': 0.0,
                'radius': 0.0,
            },
        )
        self.node.connectattr('position', self._ice_light, 'position')

    def drop_bomb(self) -> Bomb | None:
        if (self.land_mine_count <= 0 and self.bomb_count <= 0) or self.frozen:
            return None
        assert self.node
        pos = self.node.position_forward
        vel = self.node.velocity

        if self.land_mine_count > 0:
            dropping_bomb = False
            self.set_land_mine_count(self.land_mine_count - 1)
            bomb_type = 'land_mine'
        else:
            dropping_bomb = True
            bomb_type = self.bomb_type

        bomb = Bomb(
            position=(pos[0], pos[1] - 0.0, pos[2]),
            velocity=(vel[0], vel[1], vel[2]),
            bomb_type=bomb_type,
            blast_radius=self.blast_radius,
            source_player=self.source_player,
            owner=self.node,
        ).autoretain()

        assert bomb.node
        if dropping_bomb:
            self.bomb_count -= 1
            bomb.node.add_death_action(
                bs.WeakCall(self.handlemessage, BombDiedMessage())
            )
        self._pick_up(bomb.node)

        for clb in self._dropped_bomb_callbacks:
            clb(self, bomb)

        return bomb
    
    def _ice_power_efx(self) -> None:
        if not self.node:
            return
        bs.emitfx(
            position=self.node.position,
            emit_type='fairydust',
        )

    def _equip_ice_power(self) -> None:
        if not self.node:
            return
        self.handlemessage(bs.ThawMessage())
        self.handlemessage(bs.PowerupMessage('health'))
        self._old_impact_scale = self.impact_scale
        self._old_color = self.node.color
        self._old_highlight = self.node.highlight
        self._old_color_texture = self.node.color_texture
        self._old_color_mask_texture = self.node.color_mask_texture
        self._ice_power_wear_custom()
        self.impact_scale = 0.2
        self.node.hockey = True
        self._ice_power = True
        self.node.roller_materials += (self._hockey_material, )
        self._ice_power_efx_timer = bs.Timer(
            0.1, self._ice_power_efx, repeat=True)
        bs.animate(self._ice_light, 'intensity', {
            0.0: 0.0,
            0.1: 0.5,
            0.2: 0.4,
        })
        bs.animate(self._ice_light, 'radius', {
            0.0: 0.0,
            0.1: 0.2,
            0.2: 0.15,
        })
        bs.getsound('powerup01').play(3, position=self.node.position)

    def _ice_power_wear_default(self) -> None:
        if not self.node:
            return
        self.node.color = self._old_color
        self.node.highlight = self._old_highlight
        self.node.color_texture = self._old_color_texture
        self.node.color_mask_texture = self._old_color_mask_texture

    def _ice_power_wear_custom(self) -> None:
        if not self.node:
            return
        self.node.color = self.node.highlight = (0.5, 1.5, 1.5)
        self.node.color_texture = bs.gettexture('flagColor')
        self.node.color_mask_texture = bs.gettexture('aliColorMask')
        
    def _ice_power_wear_off_flash(self) -> None:
        if not self.node:
            return
        self._ice_power_flash_timer = None
        self.custom = True
        def flash() -> None:
            if self.custom:
                self._ice_power_wear_default()
                self.custom = False
            else:
                self._ice_power_wear_custom()
                self.custom = True
        self._ice_power_wear_timer = bs.Timer(
            0.05, flash, repeat=True)

    def _ice_power_wear_off(self) -> None:
        if not self.node:
            return
        bs.getsound('powerdown01').play(position=self.node.position)
        self.impact_scale = self._old_impact_scale
        self._ice_power = False
        self._ice_power_timer = None
        self._ice_power_efx_timer = None
        self._ice_power_wear_timer = None
        self._ice_power_wear_default()
        self.node.hockey = False
        roller_materials = list(self.node.roller_materials)
        roller_materials.remove(self._hockey_material)
        self.node.roller_materials = tuple(roller_materials)
        bs.animate(self._ice_light, 'intensity', {
            0.0: 0.4,
            0.1: 0.5,
            0.2: 0.0,
        })
        bs.animate(self._ice_light, 'radius', {
            0.0: 0.15,
            0.1: 0.2,
            0.2: 0.0,
        })

    def on_punch_press(self) -> None:
        super().on_punch_press()
        print(self.node.position)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.FreezeMessage):
            if not self.node:
                return None
            if self._ice_power:
                SpazFactory.get().block_sound.play(
                    1.0,
                    position=self.node.position,
                )
                return None
            else:
                if self.node.invincible:
                    SpazFactory.get().block_sound.play(
                        1.0,
                        position=self.node.position,
                    )
                    return None
                if self.shield:
                    return None
                if not self.frozen:
                    self.frozen = True
                    self.node.frozen = True
                    bs.timer(self.activity._freezing_time, bs.WeakCall(self.handlemessage, bs.ThawMessage()))
                    # Instantly shatter if we're already dead.
                    # (otherwise its hard to tell we're dead).
                    if self.hitpoints <= 0:
                        self.shatter()
        elif isinstance(msg, bs.PowerupMessage):
            if self._dead or not self.node:
                return True
            if msg.poweruptype == 'super_ice':
                if not self._ice_power:
                    self._equip_ice_power()
                self._ice_power_wear_timer = None
                self._ice_power_wear_custom()
                self._ice_power_flash_timer = bs.Timer(
                    self.activity._ice_power_time - 1.5, self._ice_power_wear_off_flash)
                self._ice_power_timer = bs.Timer(
                    self.activity._ice_power_time, self._ice_power_wear_off)
            else:
                super().handlemessage(msg)
        else:
            return super().handlemessage(msg)
        return None


# ba_meta export bascenev1.GameActivity
class IceDeathMatchGame(DeathMatchGame):

    name = 'Ice Death Match'
    description = (
        'Mata a un número de enemigos.\n'
        'Todas las bombas son de hielo.\n'
        'Cada cierto tiempo aparece un poder.\n'
        'El poder contiene lo siguiente:\n'
        '+ Inmunidad a la Congelación\n'
        '+ Súper Velocidad\n'
        '+ Curación Total\n'
        '+ Reducción de Daño'
    )

    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[bs.Setting]:
        settings = [
            bs.IntSetting(
                'Kills to Win Per Player',
                min_value=1,
                default=5,
                increment=1,
            ),
            bs.IntSetting(
                'Tiempo De Congelación',
                min_value=1,
                default=5,
                increment=1,
            ),
            bs.IntSetting(
                'Tiempo De Poder De Hielo',
                min_value=1,
                default=10,
                increment=1,
            ),
            bs.IntSetting(
                'Tiempo para Aparecer Poder',
                min_value=1,
                default=10,
                increment=1,
            ),
            bs.IntChoiceSetting(
                'Time Limit',
                choices=[
                    ('None', 0),
                    ('1 Minute', 60),
                    ('2 Minutes', 120),
                    ('5 Minutes', 300),
                    ('10 Minutes', 600),
                    ('20 Minutes', 1200),
                ],
                default=0,
            ),
            bs.FloatChoiceSetting(
                'Respawn Times',
                choices=[
                    ('Shorter', 0.25),
                    ('Short', 0.5),
                    ('Normal', 1.0),
                    ('Long', 2.0),
                    ('Longer', 4.0),
                ],
                default=1.0,
            ),
            bs.BoolSetting('Habilitar Agarrar', default=False),
            bs.BoolSetting('Habilitar Golpear', default=False),
            bs.BoolSetting('Habilitar Potenciadores', default=False),
            bs.BoolSetting('Epic Mode', default=False),
        ]

        # In teams mode, a suicide gives a point to the other team, but in
        # free-for-all it subtracts from your own score. By default we clamp
        # this at zero to benefit new players, but pro players might like to
        # be able to go negative. (to avoid a strategy of just
        # suiciding until you get a good drop)
        if issubclass(sessiontype, bs.FreeForAllSession):
            settings.append(
                bs.BoolSetting('Allow Negative Scores', default=False)
            )

        return settings

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._freezing_time = int(settings['Tiempo De Congelación'])
        self._ice_power_time = int(settings['Tiempo De Poder De Hielo'])
        self._time_appear_ice_power = int(settings['Tiempo para Aparecer Poder'])
        self._power: Power | None = None
        self._power_timer: bs.Timer = None
        self._power_position: Sequence[float] = (0.0, 0.0, 0.0)
        self._max_power_position: float = 7
        self._enable_pickup = bool(settings['Habilitar Agarrar'])
        self._enable_punch = bool(settings['Habilitar Golpear'])
        self._enable_powerups = bool(settings['Habilitar Potenciadores'])

    def on_transition_in(self) -> None:
        super().on_transition_in()
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.0, 1.1, 1.3)
        gnode.ambient_color = (0.8, 1.2, 1.4)
        if self.map.name == 'Hockey Stadium':
            pos = (-0.0190422218, 0.10072644352, -0.109683029)
            self._max_power_position = 6
        elif self.map.name == 'Football Stadium':
            pos = (-0.1001374046, 0.04180340146, 0.1095578275)
        elif self.map.name == 'Bridgit':
            pos = (-0.5227795102, 3.802429326, -1.562586233)
        elif self.map.name == 'Big G':
            pos = (-7.563673017, 2.890652319, 0.08844978098)
        elif self.map.name == 'Roundabout':
            pos = (-1.548755407, 1.528324294, -1.1124807596)
        elif self.map.name == 'Monkey Face':
            pos = (-1.74430215358, 3.38925557136, -2.15618395805)
        elif self.map.name == 'Zigzag':
            pos = (-1.50993382930, 3.05306534767, -0.01529514975)
        elif self.map.name == 'The Pad':
            pos = (0.442086964845, 3.33380131721, -2.85514187812)
        elif self.map.name == 'Doom Shroom':
            pos = (0.729165613651, 2.30488162040, -4.04898214340)
            self._max_power_position = 6
        elif self.map.name == 'Lake Frigid':
            pos = (0.681899964809, 2.55772190093, 1.383500933647)
        elif self.map.name == 'Tip Top':
            pos = (0.057506140321, 8.90296630859, -4.632864952087)
            self._max_power_position = 5
        elif self.map.name == 'Crag Castle':
            pos = (0.608665583133, 6.24972562789, -0.126513488888)
        elif self.map.name == 'Tower D':
            pos = (-0.01690735171, 0.06139940044, -0.07659307272)
        elif self.map.name == 'Happy Thoughts':
            pos = (0.099852778017, 12.7525241851, -5.50424814224)
        elif self.map.name == 'Step Right Up':
            pos = (0.194533213973, 4.11249904632, -2.97467184066)
        elif self.map.name == 'Courtyard':
            pos = (0.038726758, 2.89662661, -2.19155263)
        elif self.map.name == 'Rampage':
            pos = (0.278286784887, 5.13772945404, -4.28152322769)
            self._max_power_position = 6
        else:
            pos = (0, 0, 0)
        self._power_position = pos

    def on_begin(self) -> None:
        bs.TeamGameActivity.on_begin(self)
        self.setup_standard_time_limit(self._time_limit)
        self._update_power()
        if self._enable_powerups:
            self.setup_standard_powerup_drops()

        # Base kills needed to win on the size of the largest team.
        self._score_to_win = self._kills_to_win_per_player * max(
            1, max((len(t.players) for t in self.teams), default=0)
        )
        self._update_scoreboard()

    def _update_power(self) -> None:
        self._power = None
        self._power_timer = bs.Timer(
            self._time_appear_ice_power, self._spawn_power)

    def _spawn_power(self) -> None:
        if self._power is not None or self._power:
            return
        
        self._power = Power(
            position=self._power_position,
            max_position=self._max_power_position,
            mesh_scale=0.5,
        ).autoretain()

    def spawn_player_spaz(
        self,
        player: bs.Player,
        position: Sequence[float] = (0, 0, 0),
        angle: float | None = None,
    ) -> PlayerSpaz:
        if isinstance(self.session, bs.DualTeamSession):
            position = self.map.get_start_position(player.team.id)
        else:
            position = self.map.get_ffa_start_position(self.players)

        name = player.getname()
        color = player.color
        highlight = player.highlight

        playerspaztype = getattr(player, 'playerspaztype', PlayerSpaz)
        if not issubclass(playerspaztype, PlayerSpaz):
            playerspaztype = PlayerSpaz

        light_color = bs.normalized_color(color)
        display_color = bs.safecolor(color, target_intensity=0.75)
        spaz = playerspaztype(
            color=color,
            highlight=highlight,
            character=player.character,
            player=player,
        )

        player.actor = spaz
        assert spaz.node

        spaz.node.name = name
        spaz.node.name_color = display_color
        spaz.connect_controls_to_player(
            enable_pickup=self._enable_pickup,
            enable_punch=self._enable_punch,
        )

        # Move to the stand position and add a flash of light.
        spaz.handlemessage(
            bs.StandMessage(
                position, random.uniform(0, 360)
            )
        )
        self._spawn_sound.play(1, position=spaz.node.position)
        light = bs.newnode('light', attrs={'color': light_color})
        spaz.node.connectattr('position', light, 'position')
        bs.animate(light, 'intensity', {0: 0, 0.25: 1, 0.5: 0})
        bs.timer(0.5, light.delete)

        spaz.bomb_type = 'ice'

        return spaz