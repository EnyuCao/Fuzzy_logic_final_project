#!/usr/bin/env python3
import pygame
import numpy as np
from flsMovement import create_player_fls, create_player_fls_from_fis

pygame.init()
done = False
screenWidth = 600
screenHeight = 500
stop = False

# Variables used to change the Simulation
# See readme
g_fisFile = './fls/V1.fis'

TestCollisionObs = False
N_ObsCol = 0
reset = False

N_tests = 1
max_ticks = 5000
g_testing = True
g_obstSpeed = 0
g_playerSpeed = 5
N_collisions = 0
prev_data = []

def rotate2D(M, phi):
    """Create a 2d rotation matrix and multipy the given matrix with it"""
    R = np.array([
        [np.cos(phi),-np.sin(phi)],
        [np.sin(phi),np.cos(phi)]]
    )
    return M.dot(R)

# This function is copied from:
# http://www.nerdparadise.com/programming/pygame/part4
def create_background():
    """Creates a checker board pattern background"""
    global screenWidth, screenHeight
    width = screenWidth
    height = screenHeight
    colors = [(255, 255, 255), (212, 212, 212)]
    background = pygame.Surface((width, height))
    tile_width = 21
    y = 0
    while y < height:
        x = 0
        while x < width:
            row = y // tile_width
            col = x // tile_width
            pygame.draw.rect(
                    background,
                    colors[(row + col) % 2],
                    pygame.Rect(x, y, tile_width, tile_width))
            x += tile_width
        y += tile_width
    return background


def filterEvents():
    global done
    keysPressed = pygame.key.get_pressed()
    # Quit on escape
    if keysPressed[pygame.K_ESCAPE]:
        done = True

    filteredEvents = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

        else:
            filteredEvents.append(event)

    return (filteredEvents, keysPressed)


class Unit():
    def handleInput(self, keys):
        print("Implement handleInput in child class unit")

    def update(self):
        print("Implement update in child class of unit")

    def draw(self, screen):
        print("Implement draw in child class unit")


class Player(Unit):
    color = (255, 100, 0)
    dx = 0
    dy = 0

    def __init__(self, x, y, size, speed, fls=None):
        self.x = x
        self.y = y
        self.phi = np.pi
        self.rspeed = 5
        self.speed = speed
        self.size = size
        self.fls = fls
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)
        self.colliding = False
        self.draw_vision = True
        self.vision_lines = []
        # TODO for testing
        self.tmp = False

    def handleInput(self, keys):
        # Don't lissen to input when the player is controled by a FLS
        if (not self.fls):
            self.dx = 0
            self.dy = 0
            if keys[pygame.K_UP]:
                self.dx = np.sin(self.phi)
                self.dy = np.cos(self.phi)
            if keys[pygame.K_DOWN]:
                self.dx = -np.sin(self.phi)
                self.dy = -np.cos(self.phi)
            if keys[pygame.K_LEFT]:
                self.phi = (self.phi + np.pi*self.rspeed/180.) % (2 * np.pi)
            if keys[pygame.K_RIGHT]:
                self.phi = (self.phi - np.pi*self.rspeed/180.) % (2 * np.pi)
            # TODO remove later
            if keys[pygame.K_SPACE]:
                self.tmp = True
            if keys[pygame.K_LCTRL]:
                self.phi = 0
            if keys[pygame.K_LALT]:
                self.phi = (self.phi+.5*np.pi)%(2*np.pi)

    def update(self, objects):
        """Caluclate new position and rotation of player"""
        global reset, N_ObsCol, N_collisions, prev_data, stop

        self.vision_lines = []

        if self.fls:
            # Cacluctate the input values for the FLS
            df = min(
                self.get_distance(objects, -15/180.*np.pi),
                self.get_distance(objects, -5/180.*np.pi),
                self.get_distance(objects, 5/180.*np.pi),
                self.get_distance(objects, 15/180.*np.pi)
            )
            dl = min(
                self.get_distance(objects, 25/180.*np.pi),
                self.get_distance(objects, 45/180.*np.pi),
                self.get_distance(objects, 65/180.*np.pi),
                self.get_distance(objects, 85/180.*np.pi),
            )
            dr = min(
                self.get_distance(objects, -25/180.*np.pi),
                self.get_distance(objects, -45/180.*np.pi),
                self.get_distance(objects, -65/180.*np.pi),
                self.get_distance(objects, -85/180.*np.pi),
            )

            datapoint = {'distf':df, 'distl':dl, 'distr':dr}
            phi_dict = self.fls(datapoint)
            delta_phi = phi_dict['phil'] - phi_dict['phir']
            self.phi = (self.phi + delta_phi) % (2*np.pi)

            self.dx = np.sin(self.phi)
            self.dy = np.cos(self.phi)

        collision = False
        nx = self.x + self.dx * self.speed
        ny = self.y + self.dy * self.speed

        # Check for collision
        nRect = pygame.Rect(nx, ny, self.size, self.size)
        for obj in objects:
            if (obj.checkCollsion_rect(nRect)):
                collision = True

        # Handle movement based on if the player is collidiong with somthing
        if (not collision):
            if nx >= screenWidth - self.size or nx <= 0 \
            or ny >= screenHeight - self.size or ny <= 0:
                if not self.colliding:
                    N_collisions += 1
                    self.colliding = True
            else:
                self.colliding = False
            self.x = max(0, min(nx, screenWidth - self.size))
            self.y = max(0, min(ny, screenHeight - self.size))
        else:
            reset = True
            if not self.colliding:
                N_collisions += 1
                self.colliding = True

        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

        if prev_data != []:
            if abs(self.x - prev_data[0]) < self.speed/10. \
            and abs(self.y - prev_data[1]) < self.speed/10. \
            and abs(self.phi - prev_data[2]) < 2*np.pi/10.:
                stop = True
        prev_data = [self.x, self.y, self.phi]

    def checkCollsion_rect(self, rect):
        """ Checks for collsion with the given rect """
        return self.rect.colliderect(rect)

    def draw(self, screen):
        # Draws the raycasts
        if self.draw_vision:
            for i in range(len(self.vision_lines)):
                pygame.draw.line(screen, (255,0,0),
                                 self.vision_lines[i][0],
                                 self.vision_lines[i][1] )

        shift = 0.5 * self.size
        coords_O = np.array([[-1,-1],[-1,1],[1,1],[1,-1]]) * shift
        coords_O_R = rotate2D(coords_O, self.phi)
        coords = (coords_O_R + shift) + np.array([self.x,self.y])
        pygame.draw.polygon(screen, self.color, coords)

    def get_distance(self, objects, phi):
        """
        Returns the distance to the nearest object in the given direction
        Distance is measured from the edge of the player
        """
        global screenWidth, screenHeight
        x_pos, y_pos = self.x + 0.5 * self.size , self.y + 0.5 * self.size
        phi = (self.phi + phi) % (2 * np.pi)

        # Create bitmap of environment
        grid = np.zeros((screenHeight+2, screenWidth+2))
        grid[[0,-1],:] = 1
        grid[:,[0,-1]] = 1
        for obj in objects:
            x, y = np.meshgrid(range(int(obj.width)), range(int(obj.height)))
            grid[y.ravel()+int(obj.y)+1,x.ravel()+int(obj.x)+1] = 1

        # Determine formula to do raytracing
        x_sign = 1 if phi < np.pi else -1
        y_sign = 1 if phi < .75*np.pi or phi >= 1.75*np.pi else -1
        phi_sign = 1 if phi%np.pi < .25*np.pi else -1

        if abs(phi % np.pi - .5*np.pi) < .25*np.pi:
            # Angle with x-axis is smallest
            y = lambda x: x*np.tan(phi_sign*phi+.5*np.pi)
            get_pos_O = lambda i: (y_sign*y(i), x_sign*i)
        else:
            # Angle with y-axis is smallest
            x = lambda y: y*np.tan(phi_sign*phi)
            get_pos_O = lambda i: (y_sign*i, x_sign*x(i))

        # Determine first pixel of nearest object
        i = 0
        while 1:
            y_pos_O, x_pos_O = get_pos_O(i)
            if grid[int(1+y_pos+y_pos_O), int(1+x_pos+x_pos_O)] == 1:
                break
            i += 1
        self.vision_lines += [[(x_pos,y_pos),(x_pos+x_pos_O,y_pos+y_pos_O)]]

        # Determine distance to object, adjust for size of player.
        if (abs(np.array([y_pos_O, x_pos_O])) < .5 * self.size + 1).all():
            return 0
        else:
            return np.linalg.norm(
                np.array([y_pos_O, x_pos_O])
                - np.array([1, -1]) * (.5 * self.size + 1)
                * rotate2D(np.array([1, 0]), phi)
            )


class Obstacle_rect(Unit):
    color = (0, 0, 0)
    dTime = 1

    def __init__(self, x, y, width, height=None, speed=2, dChangeTime=30):
        self.x = x
        self.y = y
        self.width = width
        self.speed = speed

        # Checks when to pick a new direction for the obstacle
        self.dChangeTime = dChangeTime

        if(height is None):
            self.height = width
        else:
            self.height = height

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def checkCollsion_rect(self, rect):
        """ Checks for collsion with the given rect """
        return self.rect.colliderect(rect)

    def handleInput(self, keys):
        pass

    def update(self, objects):
        global reset, N_ObsCol, TestCollisionObs

        # if speed is 0 no update is needed
        if (self.speed == 0): return
        self.dTime -= 1

        if (self.dTime == 0): 
            d = np.array([np.random.rand() - .5, np.random.rand() - .5])
            self.d = (d * self.speed) / np.linalg.norm(d)
            self.dTime = self.dChangeTime

        collision = False
        nx = self.x + self.d[0]
        ny = self.y + self.d[1]

        # check for collision
        nRect = pygame.Rect(nx, ny, self.width, self.height)
        for i, obj in enumerate(objects):
            if (obj.checkCollsion_rect(nRect)):
                collision = True
                if (i == len(objects) - 1) and TestCollisionObs:
                    reset = True
                    N_ObsCol += 1

        # move the obstacle based on if colliding or not
        if (not collision):
            self.x = max(0, min(nx, screenWidth - self.width))
            self.y = max(0, min(ny, screenHeight - self.height))
        else:
            # I colliding rotate direction by 45 degrees
            tDeg = 45
            cosT = np.cos(tDeg)
            sinT = np.sin(tDeg)
            self.d[0] = cosT * self.d[0] + -sinT * self.d[1]
            self.d[1] = sinT * self.d[0] +  cosT * self.d[1]

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        return collision

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)


class Simulation():
    units = []
    background = create_background()

    def __init__(self):
        global g_playerSpeed, g_obstSpeed
        self.players = []
        self.units = []

        # Add obstaceels here in form (x, y, size)
        # Chose x, y and size to be multiples of 20 to allign with background
        rect_Objs = [
                (100, 100, 40, 40),
                (100, 200, 40, 40),
                (100, 400, 40, 40),
                (250, 250, 30, 30),
                (200, 200, 30, 30),
                (200, 100, 30, 30),
                (200, 300, 30, 30),
                (200, 400, 30, 30),
                (300,  50, 50, 50),
                (300, 300, 50, 50),
                (300, 400, 50, 50),
                (400,  60, 80, 80),
                (400, 200, 40, 40),
                (400, 400, 60, 60)]

        rect_Objs2 = [
                (100, 100, 40, 40),
                (100, 200, 40, 40),
                (100, 400, 40, 40),
                (250, 250, 30, 30),
                (200, 200, 30, 30),
                (200, 100, 30, 30),
                (50, 300, 30, 30),
                (500, 300, 30, 30),
                (200, 400, 30, 30),
                (300,  50, 50, 50),
                (300, 300, 50, 50),
                (300, 400, 50, 50),
                (400,  60, 80, 80),
                (400, 200, 40, 40),
                (400, 400, 60, 60)]

        for x, y, w, h in rect_Objs:
            self.units.append(Obstacle_rect(x, y, w, h, speed=g_obstSpeed))

        # Create FLS
        if not g_testing:
            fls = create_player_fls_from_fis(g_fisFile)
        else:
            dist_range = [0,5,25,70,1000]
            phi_range = np.array(range(5))*np.pi/32
            fls = create_player_fls(
                dist_range,
                phi_range,
                aggregation='max',
                defuzzification='centroid'
            )
        self.players = [Player(20, 460, 20, g_playerSpeed, fls)]

    def handleInput(self, event, keys):
        if(g_testing): return
        for player in self.players:
            player.handleInput(keys)
        for unit in self.units:
            unit.handleInput(keys)

    def update(self):
        for player in self.players:
            player.update(self.units)
        for i, unit in enumerate(self.units):
            objects = [unit for j, unit in enumerate(self.units) if i != j]
            for player in self.players:
                objects.append(player)
            unit.update(objects)

    def draw(self, screen):
        screen.blit(self.background, (0, 0))

        for unit in self.units:
            unit.draw(screen)

        for player in self.players:
            player.draw(screen)


def test_collisions():
    """ 
    Used in for collection data, the simulation is not shown
    Data is printed to the stdout
    """
    global done, stop, N_tests, N_collisions, max_ticks
    n = 0
    player_speeds = [5, 10]
    dist_ranges = [[0,5,25,70,1000]]
    phi_ranges = [np.array(range(5))*np.pi/32]
    aggregations = ['max', 'sum']
    defuzzifications = ['som', 'mom', 'lom', 'centroid']
    print('RESULT ORDER:')
    print('[1] number of ticks')
    print('[2] number of collisions')
    print('[3] ([1]+1)/([2]+1)')
    print('[4] ([2]+1)/([1]+1)')
    while not done and n < N_tests:
        for player_speed in player_speeds:
            for dist_range in dist_ranges:
                for phi_range in phi_ranges:
                    for aggregation in aggregations:
                        for defuzzification in defuzzifications:
                            print()
                            print('CURRENT PARAMETERS:')
                            print('player_speed = ' + str(player_speed))
                            print('dist_range = ' + str(dist_range))
                            print('phi_range = ' + str(phi_range))
                            print('aggregation = ' + str(aggregation))
                            print('defuzzification = ' + str(defuzzification))
                            stop = False
                            ticks = 0
                            N_collisions = 0
                            active_scene = Simulation()
                            for player in active_scene.players:
                                player.speed = player_speed
                                player.fls = create_player_fls(
                                    dist_range,
                                    phi_range,
                                    aggregation=aggregation,
                                    defuzzification=defuzzification
                                )
                            while not (stop or done or ticks >= max_ticks):
                                filteredEvents = filterEvents()
                                active_scene.handleInput(*filteredEvents)
                                active_scene.update()
                                ticks += 1
                            print('RESULTS')
                            print(ticks)
                            print(N_collisions)
                            print((ticks+1)/float(N_collisions+1))
                            print((N_collisions+1)/float(ticks+1))
                            n += 1

def main(width, height):
    global done
    screen = pygame.display.set_mode((width, height))
    active_scene = Simulation()

    while not done:
        clock = pygame.time.Clock()

        filteredEvents = filterEvents()
        active_scene.handleInput(*filteredEvents)
        active_scene.update()
        active_scene.draw(screen)

        pygame.display.flip()
        clock.tick(120)


if __name__ == "__main__":
    if g_testing:
        test_collisions()
    else:
        main(screenWidth, screenHeight)
