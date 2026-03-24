import util

class Ball(util.MyCircle):
    def __init__(self, color, width, height):
        super().__init__(color, width, height)
        self.selected = False
    
    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)