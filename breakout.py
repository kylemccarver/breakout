import sys, random, math, pygame
from pygame.locals import *

FPS = 60

WINWIDTH = 640
WINHEIGHT = 420
HALF_WINHEIGHT = WINHEIGHT / 2
HALF_WINWIDTH = WINWIDTH / 2

WALLSIZE = 30
WALLHEIGHT = WINHEIGHT - 36
BRICKHEIGHT = 12
BRICKWIDTH = 32
PADDLEHEIGHT = 8
PADDLEWIDTH = 64
BALLSIZE = 8
BRICKROWS = 6
BRICKCOLS = int((WINWIDTH - (2 * BRICKWIDTH)) / BRICKWIDTH)
MAXANGLE = 5 * math.pi / 12

Y_MARGIN = 26
GAP = Y_MARGIN + (4 * BRICKHEIGHT) + 2

# Colors
BLACK = (0, 0, 0)
GRAY = (171, 171, 171)
PURPLE = (205, 62, 207)
RED = (250, 82, 85)
ORANGE = (255, 129, 30)
YELLOW = (255, 145, 29)
GREEN = (11, 175, 29)
BLUE = (107, 100, 255)
BGCOLOR = BLACK

def main():
    global SCREEN, FPSCLOCK, BRICKCOLORS, NORMALS, FONT, PSFONT, BOOP, BEEP

    pygame.init()

    SCREEN = pygame.display.set_mode((WINWIDTH, WINHEIGHT))
    pygame.display.set_caption("Breakout")
    FPSCLOCK = pygame.time.Clock()
    BRICKCOLORS = (PURPLE, RED, ORANGE, YELLOW, GREEN, BLUE)
    NORMALS = {"LEFT": pygame.math.Vector2(-1, 0),
               "RIGHT": pygame.math.Vector2(1, 0),
               "UP": pygame.math.Vector2(0, -1),
               "DOWN": pygame.math.Vector2(0, 1)}  
    FONT = pygame.font.Font(None, 24)
    PSFONT = pygame.font.Font("prstart.ttf", 24)
    BOOP = pygame.mixer.Sound("boop.wav")
    BEEP = pygame.mixer.Sound("beep.wav")

    pygame.mouse.set_pos([HALF_WINWIDTH, HALF_WINHEIGHT])
    pygame.mouse.set_visible(False)

    playerRect = pygame.Rect(HALF_WINWIDTH - (PADDLEWIDTH / 2), WINHEIGHT - 50, PADDLEWIDTH, PADDLEHEIGHT)
    ball = {"rect": pygame.Rect(HALF_WINWIDTH - (BALLSIZE / 2), WINHEIGHT - 100, BALLSIZE, BALLSIZE),
            "dir": pygame.math.Vector2(random.choice((-1, 1)), 1),
            "speed": 3}
    bricks = generateBricks()
    clearedBricks = [[None] * BRICKCOLS] * BRICKROWS
    
    # State variables
    ballInPlay = False
    score = 0
    lives = 5
    
    showIntro(bricks, playerRect)
    while True:
        while True: # Game loop

            for e in pygame.event.get():
                if e.type == QUIT:
                    terminate()
                elif e.type == KEYUP:
                    if e.key == K_ESCAPE:
                        terminate()
                    elif e.key == K_f:
                        if SCREEN.get_flags() & FULLSCREEN:
                            pygame.display.set_mode((WINWIDTH, WINHEIGHT))
                        else:
                            pygame.display.set_mode((WINWIDTH, WINHEIGHT), FULLSCREEN)
                elif e.type == MOUSEMOTION:
                    playerRect.centerx = e.pos[0]
                elif e.type == MOUSEBUTTONUP:
                    if ballInPlay == False:
                        ballInPlay = True
                        # spawn ball
                        ball["rect"].topleft = (HALF_WINWIDTH - (BALLSIZE / 2), HALF_WINHEIGHT)
            
            if playerRect.left < BRICKWIDTH:
                playerRect.left = BRICKWIDTH
            elif playerRect.right > WINWIDTH - BRICKWIDTH:
                playerRect.right = WINWIDTH - BRICKWIDTH
            
            if ballInPlay:
                # Move ball
                ball["rect"].move_ip(ball["dir"][0] * ball["speed"], ball["dir"][1] * ball["speed"])

                # Check collisions; bounce off wall, paddle, or brick
                if ball["rect"].top > WINHEIGHT: # ball went past the player
                    lives -= 1
                    reset(playerRect, ball)
                    ballInPlay = False
                    # Check game over
                    if lives == 0:
                        break
                if ball["rect"].left < BRICKWIDTH: # hit left wall
                    ball["dir"].reflect_ip(NORMALS["RIGHT"])
                if ball["rect"].right > WINWIDTH - BRICKWIDTH: # hit right wall
                    ball["dir"].reflect_ip(NORMALS["LEFT"])
                if ball["rect"].top < Y_MARGIN + WALLSIZE: # hit top wall
                    ball["dir"].reflect_ip(NORMALS["DOWN"])
                if ball["rect"].colliderect(playerRect):
                    ball["dir"] = paddleAngle(ball["rect"].centerx, playerRect.centerx)
                    BOOP.play()
                
                brickCollide = False
                colBrick = None
                for x in range(len(bricks)):
                    for y in range(len(bricks[x])):
                        if bricks[x][y] != None:
                            if ball["rect"].colliderect(bricks[x][y]):
                                brickCollide = True
                                colBrick = bricks[x][y]
                                bricks[x][y] = None
                                break
                if brickCollide:
                    # TODO: get accurate reflect normal
                    ball["dir"].reflect_ip(brickAngle(ball, colBrick))
                    score += 1
                    BEEP.play()
                # TODO: check if all bricks are cleared
                if bricks == clearedBricks: # All bricks have been cleared
                    bricks = generateBricks()
                    reset(playerRect, ball)
                    ballInPlay = False
                    ball["speed"] += 2

                
            # Draw
            SCREEN.fill(BGCOLOR)
            drawScoreAndLives(score, lives)
            drawWalls()
            drawBricks(bricks)
            pygame.draw.rect(SCREEN, PURPLE, playerRect)
            if ballInPlay:
                pygame.draw.rect(SCREEN, PURPLE, ball["rect"])

            pygame.display.update()
            FPSCLOCK.tick(FPS)
        showGameOver(score)
        score = 0
        lives = 5
        bricks = generateBricks()

def terminate():
    pygame.quit()
    sys.exit()

def generateBricks():
    bricks = []
    startx = BRICKWIDTH
    starty = Y_MARGIN + GAP

    for i in range(BRICKROWS):
        row = []
        for j in range(BRICKCOLS):
            row.append(pygame.Rect(startx, starty, BRICKWIDTH, BRICKHEIGHT))
            startx += BRICKWIDTH
        startx = BRICKWIDTH
        starty += BRICKHEIGHT
        bricks.append(row)

    return bricks

def drawScoreAndLives(score, lives):
    scoreSurf = PSFONT.render("SCORE: %s" % str(score), 1, GRAY)
    scoreRect = scoreSurf.get_rect()
    scoreRect.center = (HALF_WINWIDTH / 2, Y_MARGIN / 2)

    livesSurf = PSFONT.render("LIVES: %s" % str(lives), 1, GRAY)
    livesRect = livesSurf.get_rect()
    livesRect.center = (HALF_WINWIDTH + (HALF_WINWIDTH / 2), Y_MARGIN / 2)

    SCREEN.blit(scoreSurf, scoreRect)
    SCREEN.blit(livesSurf, livesRect)

def drawBricks(bricks):
    startx = BRICKWIDTH
    starty = Y_MARGIN + GAP

    for x in range(BRICKROWS):
        for y in range(BRICKCOLS):
            if bricks[x][y] != None:
                pygame.draw.rect(SCREEN, BRICKCOLORS[x], bricks[x][y])
            startx += BRICKWIDTH
        startx = BRICKWIDTH
        starty += BRICKHEIGHT

def drawWalls():
    pygame.draw.rect(SCREEN, GRAY, (0, Y_MARGIN, WINWIDTH, WALLSIZE)) # top wall
    pygame.draw.rect(SCREEN, GRAY, (0, Y_MARGIN, BRICKWIDTH, WINHEIGHT - 50)) # left wall
    pygame.draw.rect(SCREEN, GRAY, (WINWIDTH - BRICKWIDTH, Y_MARGIN, BRICKWIDTH, WINHEIGHT - 50)) # right wall

def paddleAngle(ballCenter, paddleCenter):
    dist = paddleCenter - ballCenter
    ratio = dist / (PADDLEWIDTH / 2)
    if ratio > 1:
        ratio = 1
    return pygame.math.Vector2(-math.sin(ratio * MAXANGLE), -1)

def brickAngle(ball, brick):
    ballRect = ball["rect"]
    
    # Do not change order of if statements; the first two act as short circuits
    if brick.collidepoint(ballRect.topright) and brick.collidepoint(ballRect.bottomright): # hit right side
        return NORMALS["LEFT"]
    elif brick.collidepoint(ballRect.topleft) and brick.collidepoint(ballRect.bottomleft): # hit left side
        return NORMALS["RIGHT"]
    elif brick.collidepoint(ballRect.topleft) or brick.collidepoint(ballRect.topright): # hit bottom side
        return NORMALS["DOWN"]
    elif brick.collidepoint(ballRect.bottomleft) or brick.collidepoint(ballRect.bottomright): # hit top side
        return NORMALS["UP"]
    
def reset(playerRect, ball):
    playerRect.topleft = (HALF_WINWIDTH - (PADDLEWIDTH / 2), WINHEIGHT - 50)
    ball["rect"].topleft = (HALF_WINWIDTH - (BALLSIZE / 2), WINHEIGHT - 100)
    ball["dir"] = pygame.math.Vector2(random.choice((-1, 1)), 1)
    pygame.mouse.set_pos([HALF_WINWIDTH, HALF_WINHEIGHT])

def showIntro(bricks, playerRect):
    infoSurf = PSFONT.render("Click to begin", 1, (255, 255, 255))
    infoRect = infoSurf.get_rect()
    infoRect.center = (HALF_WINWIDTH, HALF_WINHEIGHT)

    SCREEN.fill(BGCOLOR)
    drawWalls()
    drawBricks(bricks)
    pygame.draw.rect(SCREEN, PURPLE, playerRect)
    SCREEN.blit(infoSurf, infoRect)
    pygame.display.update()

    while checkForClick() == False:
        pygame.display.update()
        FPSCLOCK.tick(FPS)

def showGameOver(score):
    gameOverSurf = PSFONT.render("GAME OVER", 1, (255, 0, 0))
    gameOverRect = gameOverSurf.get_rect()
    gameOverRect.center = (HALF_WINWIDTH, HALF_WINHEIGHT / 2)

    scoreSurf = PSFONT.render("Your score was: %s" % str(score), 1, (255, 255, 255))
    scoreRect = scoreSurf.get_rect()
    scoreRect.center = (HALF_WINWIDTH, HALF_WINHEIGHT)

    infoSurf = PSFONT.render("Click to play again", 1, (255, 255, 255))
    infoRect = infoSurf.get_rect()
    infoRect.center = (HALF_WINWIDTH, HALF_WINHEIGHT + (HALF_WINHEIGHT / 2))

    SCREEN.fill(BGCOLOR)
    drawWalls()
    SCREEN.blit(gameOverSurf, gameOverRect)
    SCREEN.blit(scoreSurf, scoreRect)
    SCREEN.blit(infoSurf, infoRect)
    pygame.display.update()
    checkForClick()
    pygame.time.wait(500)

    while checkForClick() == False:
        pygame.display.update()
        FPSCLOCK.tick(FPS)

def checkForClick():
    if len(pygame.event.get(QUIT)) > 0:
        terminate()
    
    keyUpEvents = pygame.event.get(KEYUP)
    if len(keyUpEvents) > 0 and keyUpEvents[0].key == K_ESCAPE:
        terminate()
    mouseUpEvents = pygame.event.get(MOUSEBUTTONUP)
    if len(mouseUpEvents) == 0:
        return False
    else:
        return True

if __name__ == "__main__":
    main()