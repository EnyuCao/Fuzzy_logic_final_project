#!/usr/bin/env python3
import pygame
import numpy as np

pygame.init()
done = False
screenWidth = 600
screenHeight = 500


# This function is copied from:
# http://www.nerdparadise.com/programming/pygame/part4
def create_background():
    global screenWidth, screenHeight
    width = screenWidth
    height = screenHeight
    colors = [(255, 255, 255), (212, 212, 212)]
    background = pygame.Surface((width, height))
    tile_width = 20
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

    def __init__(self, x, y, size, speed, fl=False):
        self.x = x
        self.y = y
        self.phi = np.pi
        self.rspeed = 5
        self.speed = speed
        self.size = size
        self.fl = fl
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

    #TODO: read out raytrace in specific directions

    #TODO: input function so our fuzzy system can interact with the simulation

    def handleInput(self, keys):
        if (not self.fl):
            self.dx = 0
            self.dy = 0
            if keys[pygame.K_UP]:
                self.dx = np.sin(self.phi)
                self.dy = np.cos(self.phi)
            if keys[pygame.K_DOWN]:
                self.dx = -np.sin(self.phi)
                self.dy = -np.cos(self.phi)
            if keys[pygame.K_LEFT]:
                self.phi += np.pi*self.rspeed/180.
            if keys[pygame.K_RIGHT]:
                self.phi -= np.pi*self.rspeed/180.

    def update(self, objects):

        if self.fl:
            # Handle fuzzy logic system here
            pass

        collision = False
        nx = self.x + self.dx * self.speed
        ny = self.y + self.dy * self.speed

        # TODO Does not take into account the rotation of the player,
        # TODO also there are no rotated objects yet
        nRect = pygame.Rect(nx, ny, self.size, self.size)
        for obj in objects:
            if (obj.checkCollsion_rect(nRect)):
                collision = True

        if (not collision):
            self.x = nx
            self.y = ny

        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

    def draw(self, screen):
        R = np.array([
            [np.cos(self.phi),-np.sin(self.phi)],
            [np.sin(self.phi),np.cos(self.phi)]]
        )
        coords_O = np.array([[-1,-1],[-1,1],[1,1],[1,-1]])
        coords_O_R = coords_O.dot(R)
        coords = (coords_O_R + 1)* 0.5*self.size + np.array([self.x,self.y])
        pygame.draw.polygon(screen, self.color, coords)


class Obstacle_rect(Unit):
    color = (0, 0, 0)

    def __init__(self, x, y, width, height=None):
        self.x = x
        self.y = y
        self.width = width

        if(height is None):
            self.height = width
        else:
            self.height = height

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def checkCollsion_rect(self, rect):
        return self.rect.colliderect(rect)

    def handleInput(self, keys):
        pass

    def update(self):
        pass

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)


class Simulation():
    player = Player(20, 460, 20, 2)
    units = []
    background = create_background()

    def __init__(self):
        # Add obstaceels here in form (x, y, size)
        # Chose x, y and size to be multiples of 20 to allign with background
        rect_Objs = [(240, 240, 80), (100, 100, 40), (400, 400, 60), 
                     (60, 400, 40), (400, 60, 80)]
        for x, y, size in rect_Objs:
            self.units.append(Obstacle_rect(x, y, size))

    def handleInput(self, event, keys):

        self.player.handleInput(keys)
        for unit in self.units:
            unit.handleInput(keys)

    def update(self):
        self.player.update(self.units)
        for unit in self.units:
            unit.update()

    def draw(self, screen):
        screen.blit(self.background, (0, 0))

        for unit in self.units:
            unit.draw(screen)

        self.player.draw(screen)


if __name__ == "__main__":
    main(screenWidth, screenHeight)
