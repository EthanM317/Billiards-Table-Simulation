import pygame, sys
import numpy as np
import util


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
    
    #moving walls to correct locations
    wall_right.set_pos((win_width - (wall_thickness / 2), win_height / 2))
    wall_bottom.set_pos((win_width / 2, win_height - (wall_thickness / 2)))

    #grouping sprites
    sprites_group = pygame.sprite.Group([wall_left, wall_right, wall_top, wall_bottom])
    
    #simulation setup code goes here
    
    #keypress events
    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            # other keypress events go here
        #Update ball positions here
    
        screen.fill(util.WHITE)
        #updates sprites_group data to screen
        #right now all sprites in group are constant so no change
        sprites_group.update()
        sprites_group.draw(screen)
        
        #draws rest of screen data to display
        pygame.display.flip()
        
        #sim.step()    
if __name__ == '__main__':
    main()
    