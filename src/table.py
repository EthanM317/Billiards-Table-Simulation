import pygame, sys
import numpy as np
import util
from ball import Ball


def main():
    pygame.init()
    clock = pygame.time.Clock()
    #Standard billiards table is 244cm x 122cm (each pixel is 0.5 cm)
    wall_thickness = 30
    win_width, win_height = 244 + wall_thickness, 488 + wall_thickness 
    screen = pygame.display.set_mode((win_width, win_height))
    pygame.display.set_caption("Billiards Table Simulation")
    
    #text
    text = util.MyText(util.BLACK)
    
    
    
    #sprites
    wall_left = util.MyRect(util.BLUE, wall_thickness, win_height)
    wall_right = util.MyRect(util.BLUE, wall_thickness, win_height)
    wall_top = util.MyRect(util.BLUE, win_width, wall_thickness)
    wall_bottom = util.MyRect(util.BLUE, win_width, wall_thickness)
    
    #balls
    #standard radius is 5.7cm, we will round to 5.5cm to match our cm->pixel scaling
    ball1 = Ball(util.RED, 11, 11)
    #moving ball
    ball1.set_pos((100,100))
    
    #moving walls to correct locations
    wall_right.set_pos((win_width - (wall_thickness / 2), win_height / 2))
    wall_bottom.set_pos((win_width / 2, win_height - (wall_thickness / 2)))

    #grouping sprites
    group_walls = pygame.sprite.Group([wall_left, wall_right, wall_top, wall_bottom])
    #don't need to update walls since they don't move, but balls do
    #so we will place balls in a separate group
    group_balls = pygame.sprite.Group([ball1])
    
    
    
    #simulation setup code goes here
    
    #keypress events
    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            # other keypress events go here
            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_pos = pygame.mouse.get_pos()
                #check each ball to see if they were clicked
                for ball in group_balls:
                    if ball.is_clicked(mouse_pos):
                        ball.selected = True
                        print(f"{ball.color} Ball clicked!")
        screen.fill(util.WHITE)
        #updates sprites_group data to screen
        #walls are constant so no update needed
        group_walls.draw(screen)
        #Update ball positions here
        group_balls.update()
        group_balls.draw(screen)
        
        #draws rest of screen data to display
        pygame.display.flip()
        
        #sim.step()    
if __name__ == '__main__':
    main()
    