#!/usr/bin/env python3
import pygame
import numpy as np
from flsMovement import calcDir, create_player_fls

pygame.init()
done = False
screenWidth = 600
screenHeight = 500

def rotate2D(M, phi):
    R = np.array([
        [np.cos(phi),-np.sin(phi)],
        [np.sin(phi),np.cos(phi)]]
    )
    return M.dot(R)

# This function is copied from:
# http://www.nerdparadise.com/programming/pygame/part4
def create_background():
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
        clock.tick(60)


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

    def __init__(self, x, y, size, speed, max_dist=0, fls=None):
        self.x = x
        self.y = y
        self.phi = np.pi
        self.rspeed = 5
        self.speed = speed
        self.size = size
        self.max_dist = max_dist
        self.fls = fls
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)
        # TODO for testing
        self.tmp = False
        self.drawline = None

    #TODO: read out raytrace in specific directions

    #TODO: input function so our fuzzy system can interact with the simulation

    def handleInput(self, keys):
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

        if self.fls:
            pass
#            df = self.get_distance(objects, 0)
#            db = self.get_distance(objects, .5 * np.pi)
#            dl = self.get_distance(objects, np.pi)
#            dr = self.get_distance(objects, 1.5 * np.pi)
#            self.phi = calcDir(dl, dr, df, db, self.phi)

            df = min(
#                self.get_distance(objects, 0),
                self.get_distance(objects, .1*np.pi),
                self.get_distance(objects, -.1*np.pi),
                self.max_dist
            )
            dl = min(
#                self.get_distance(objects, .35*np.pi),
                self.get_distance(objects, .25*np.pi),
                self.get_distance(objects, .45*np.pi),
                self.max_dist
            )
            dr = min(
#                self.get_distance(objects, -.35*np.pi),
                self.get_distance(objects, -.25*np.pi),
                self.get_distance(objects, -.45*np.pi),
                self.max_dist
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

        # TODO? Does not take into account the rotation of the player,
            # also there are no rotated objects yet
        nRect = pygame.Rect(nx, ny, self.size, self.size)
        for obj in objects:
            if (obj.checkCollsion_rect(nRect)):
                collision = True

        if (not collision):
            self.x = max(0, min(nx, screenWidth - self.size))
            self.y = max(0, min(ny, screenHeight - self.size))

        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

        # TODO remove later
        if self.tmp:
            print("Distance:", self.get_distance(objects, 0/180.*np.pi))
            self.tmp = False

    def checkCollsion_rect(self, rect):
        """ Checks for collsion with the given rect """
        return self.rect.colliderect(rect)

    def draw(self, screen):
        #TODO remove later
        if self.drawline:
            pygame.draw.line(screen,(255,0,0),self.drawline[0],self.drawline[1])
        R = np.array([
            [np.cos(self.phi),-np.sin(self.phi)],
            [np.sin(self.phi),np.cos(self.phi)]]
        )
        shift = 0.5 * self.size
        coords_O = np.array([[-1,-1],[-1,1],[1,1],[1,-1]]) * shift
        coords_O_R = coords_O.dot(R)
        coords = (coords_O_R + shift) + np.array([self.x,self.y])
        pygame.draw.polygon(screen, self.color, coords)

    def get_distance(self, objects, phi):
        x_pos, y_pos = self.x + 0.5 * self.size , self.y + 0.5 * self.size
        phi = (self.phi + phi) % (2 * np.pi)
        # Create bitmap of environment
        global screenWidth, screenHeight
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
        # Angle with x-axis is smallest
        if abs(phi % np.pi - .5*np.pi) < .25*np.pi:
            y = lambda x: x*np.tan(phi_sign*phi+.5*np.pi)
            get_pos_O = lambda i: (y_sign*y(i), x_sign*i)
        # Angle with y-axis is smallest
        else:
            x = lambda y: y*np.tan(phi_sign*phi)
            get_pos_O = lambda i: (y_sign*i, x_sign*x(i))
        # Determine first pixel of nearest object
        i = 0
        while 1:
            y_pos_O, x_pos_O = get_pos_O(i)
            if grid[int(1+y_pos+y_pos_O), int(1+x_pos+x_pos_O)] == 1:
                break
            i += 1
        # TODO remove later
        self.drawline = [(x_pos,y_pos),(x_pos+x_pos_O,y_pos+y_pos_O)]
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

    def __init__(self, x, y, width, height=None, speed=1.5, dChangeTime=30):
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

        nRect = pygame.Rect(nx, ny, self.width, self.height)
        for obj in objects:
            if (obj.checkCollsion_rect(nRect)):
                collision = True

        if (not collision):
            self.x = max(0, min(nx, screenWidth - self.width))
            self.y = max(0, min(ny, screenHeight - self.height))
        else:
            tDeg = 45
            cosT = np.cos(tDeg)
            sinT = np.sin(tDeg)
            self.d[0] = cosT * self.d[0] + -sinT * self.d[1]
            self.d[1] = sinT * self.d[0] +  cosT * self.d[1]

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)


class Simulation():
    dist_range = [0,5,25,70,100]
    phi_range = np.array(range(5))*np.pi/32
    fls = create_player_fls(dist_range, phi_range)
    player = Player(20, 460, 20, 2, dist_range[-1], fls)
    units = []
    background = create_background()

    def __init__(self):
        # Add obstaceels here in form (x, y, size)
        # Chose x, y and size to be multiples of 20 to allign with background
        # rect_Objs = [(240, 240, 8,6), (100, 100, 40, 40), (400, 400, 60, 60),
                     # (60, 400, 40, 40), (400, 60, 80, 80)]

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
        for x, y, w, h in rect_Objs:
            self.units.append(Obstacle_rect(x, y, w, h))

    def handleInput(self, event, keys):
        self.player.handleInput(keys)
        for unit in self.units:
            unit.handleInput(keys)

    def update(self):
        self.player.update(self.units)
        for i, unit in enumerate(self.units):
            objects = [unit for j, unit in enumerate(self.units) if i != j]
            objects.append(self.player)
            unit.update(objects)

    def draw(self, screen):
        screen.blit(self.background, (0, 0))

        for unit in self.units:
            unit.draw(screen)

        self.player.draw(screen)


if __name__ == "__main__":
    main(screenWidth, screenHeight)
