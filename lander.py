from easymunk import Vec2d, Arbiter, Body, Vec2d, ShapeFilter, pyxel as phys
import pyxel
import random

FPS = 30
WIDTH, HEIGHT = 256, 196
SCREEN = Vec2d(WIDTH, HEIGHT)


class Particles:
    def __init__(self, space):
        self.particles = []
        self.space = space

    def draw(self, camera=pyxel):
        for p in self.particles:
            x, y = p.position
            if random.random() < 0.15:
                camera.rect(x, y, 2, 2, self.get_color(p.duration))
            else:
                camera.pset(x, y, self.get_color(p.duration))

    def update(self):
        for p in self.particles.copy():
            p.velocity = p.velocity.rotated(random.uniform(-5, 5)) 
            p.duration -= 1
            if p.duration <= 0:
                self.particles.remove(p)

    def emmit(self, position, velocity):
        p = self.space.create_circle(
            radius=1,
            mass=0.1,
            moment=float("inf"),
            position=position,
            velocity=velocity,
            filter=ShapeFilter(group=1),
        )
        p.duration = 105 - random.expovariate(1 / 10)
        p.velocity_func = self.update_velocity
        self.particles.append(p)

    def update_velocity(self, body, gravity, damping, dt):
        body.update_velocity(body, -gravity / 2, 0.99, dt)

    def get_color(self, t):
        if t > 95:
            return pyxel.COLOR_WHITE
        elif t > 80:
            return pyxel.COLOR_YELLOW
        elif t > 65:
            return pyxel.COLOR_RED
        elif t > 40:
            return pyxel.COLOR_PURPLE
        elif t > 25:
            return pyxel.COLOR_BROWN
        else:
            return pyxel.COLOR_GRAY



#
# MOON LANDER (SISTEMA DE PARTÍCULAS)
#
class Game:
    PLAYER_SHAPE = [(0, 6), (-3, -3), (+3, -3)]
    BASE_SHAPE = (25, 5)
    PLAYER_SPEED = 90
    PLAYER_COLOR = pyxel.COLOR_PINK
    BASE_COLOR = pyxel.COLOR_ORANGE
    GRAVITY = Vec2d(0, -25)
    THRUST = -3 * GRAVITY
    ANGULAR_VELOCITY = 180
    FLOOR_STEP = 30
    FLOOR_DY = 15
    FLOOR_N = 42
    PLAYER_COL_TYPE = 1
    BASE_COL_TYPE = 2
    FLOOR_COL_TYPE = 3
    MAX_IMPULSE = 30
    PLANET_COL_TYPE = 2

    def __init__(self):
        self.space = space = phys.space(
            gravity=self.GRAVITY,
            camera=phys.Camera(flip_y=True),
            friction=1,
        )
        self.landed = False
        self.victory = False

        # Cria jogador
        self.player = space.create_poly(
            self.PLAYER_SHAPE,
            mass=1,
            moment=2,
            position=SCREEN / 2,
            friction=1.0,
            collision_type=self.PLAYER_COL_TYPE,
            filter=ShapeFilter(group=1),
        )
        self.particles = Particles(space)
        self.planets = []
        # Cria base
        dx = random.uniform(-WIDTH, WIDTH)
        self.base = space.create_box(
            self.BASE_SHAPE,
            position=self.player.position + (dx, -0.45 * HEIGHT),
            friction=1.0,
            collision_type=self.BASE_COL_TYPE,
            body_type=Body.STATIC,
        )

        # Cria chão
        shape = list(self.base.shapes)[0]
        bb = shape.cache_bb()
        self.make_floor(bb.right, bb.bottom, self.FLOOR_STEP, self.FLOOR_DY)
        self.make_floor(bb.left, bb.bottom, -self.FLOOR_STEP, self.FLOOR_DY)

        # Escuta colisões entre base/chão e jogador
        space.collision_handler(
            self.PLAYER_COL_TYPE, self.BASE_COL_TYPE, post_solve=self.on_land
        )
        self.space.collision_handler(
            self.PLAYER_COL_TYPE, self.FLOOR_COL_TYPE, begin=self.on_collision
        )

        # Escuta colisões entre jogador e planetas
        self.space.collision_handler(
            self.PLAYER_COL_TYPE, self.PLANET_COL_TYPE, post_solve=self.on_planet_collision
        )

        self.space.collision_handler(
            self.PLANET_COL_TYPE, self.FLOOR_COL_TYPE, post_solve=self.on_planet_floor_collision
        )

        self.space.collision_handler(
            self.PLANET_COL_TYPE, self.BASE_COL_TYPE, post_solve=self.on_planet_base_collision
        )


    def on_collision(self, arb: Arbiter):
        self.landed = True
        self.victory = False
        self.space.remove(self.player.shape, self.player)
        for _ in range(200):
            self.particles.emmit(
                position=self.player.local_to_world((random.uniform(-2, 2), -3)),
                velocity=-random.uniform(100, 200) * self.player.rotation_vector.perpendicular(),
            )
        return True

    def on_land(self, arb: Arbiter):
        if not self.landed:
            self.victory = arb.total_impulse.length < self.MAX_IMPULSE
        self.landed = True

    def on_planet_collision(self, arb: Arbiter):
        self.victory = False
        for _ in range(200):
            self.particles.emmit(
            position=arb.contact_point_set.points[0].point_b,
            velocity= -random.uniform(100, 200) * self.player.rotation_vector.perpendicular(),
        )
        self.space.remove(self.player.shape, self.player)
        self.landed = True
        self.status(self.landed)
        return True

    def on_planet_base_collision(self, arb: Arbiter):
        if len(self.planets) > 0 and arb.is_first_contact:
            self.space.remove(arb.shapes[0])
        return True

    def on_planet_floor_collision(self, arb: Arbiter):
        if len(self.planets) > 0 and arb.is_first_contact:
            for _ in range(20):
                self.particles.emmit(
                    position=arb.shapes[0].local_to_world((random.uniform(-2, 2), -3)),
                    velocity=-random.uniform(100, 200) * self.space.static_body.rotation_vector.perpendicular(),
                )
            self.space.remove(arb.shapes[0])
        return True
        
    def make_floor(self, x, y, step, dy):
        body = self.space.static_body

        a = Vec2d(x, y)
        for _ in range(self.FLOOR_N):
            b = a + (step, random.uniform(-dy, dy))
            body.create_segment(a, b, 1, collision_type=self.FLOOR_COL_TYPE)
            a = b

    def get_color_planets(self, radius):
        if 1 <= radius <= 2:
            return pyxel.COLOR_CYAN
        elif 3 <= radius <= 5:
            return pyxel.COLOR_NAVY
        elif 6 <= radius <= 8:
            return pyxel.COLOR_YELLOW
        elif 9 <= radius <= 11:
            return pyxel.COLOR_PURPLE
        elif radius == 12:
            return pyxel.COLOR_RED
        else:
            return pyxel.COLOR_GRAY

    def spawn_planets(self):
        if random.random() > 1/8:
            return False
        dx = random.uniform(-WIDTH, WIDTH)
        for _ in range(1):
            radius = random.randint(1,12)
            mass = radius * 2
            color = self.get_color_planets(radius)
            
            planet = self.space.create_circle(
                radius=radius,
                mass=mass,
                position=self.player.position + (dx, HEIGHT),
                collision_type=self.PLANET_COL_TYPE,
                body_type=Body.DYNAMIC,
                color=color
            )
        self.planets.append(planet)
        return True

    def update(self):
        if not self.landed:
            if pyxel.btn(pyxel.KEY_LEFT):
                self.player.angular_velocity = +self.ANGULAR_VELOCITY
            elif pyxel.btn(pyxel.KEY_RIGHT):
                self.player.angular_velocity = -self.ANGULAR_VELOCITY
            else:
                self.player.angular_velocity = 0.0

            if pyxel.btn(pyxel.KEY_UP):
                self.player.apply_force_at_local_point(4 * self.THRUST)
                
                for _ in range(2):
                    self.particles.emmit(
                        position=self.player.local_to_world((random.uniform(-2, 2), -3)),
                        velocity=-random.uniform(50, 90) * self.player.rotation_vector.perpendicular(),
                    )

        self.spawn_planets()
        dt = 1 / FPS
        self.particles.update()
        self.space.step(dt, sub_steps=4)
        self.space.camera.follow(self.player.position)

    def status(self, landed):
        if landed:
            msg = "PARABENS!" if self.victory else "PERDEU :("
            x = WIDTH / 2 - len(msg) * pyxel.FONT_WIDTH / 2
            pyxel.text(x, HEIGHT // 2 - 20, msg, pyxel.COLOR_RED)

    def draw(self):
        pyxel.cls(0)
        camera = self.space.camera
        camera.draw(self.space.static_body)
        camera.draw(self.base)
        self.particles.draw(camera)
        camera.draw(self.player)

        for planet in self.planets:
            if self.landed:
                self.space.remove(planet)
            else:
                camera.draw(planet)

        self.status(self.landed)


game = Game()
pyxel.init(WIDTH, HEIGHT, fps=FPS)
pyxel.mouse(True)
pyxel.run(game.update, game.draw)