from fltk import *
from PIL import Image
import io
import pygame
import random
import vlc


# Class for rotation of the pieces
class Piece:
    def __init__(self, coords):
        self.coords = coords
        # to make things easier, when you pass in your list of tuple coordinates
        # you could have the first coordinate be the center
        self.center = coords[0]

    def rotate(self, dir="clockwise"):
        offset_x, offset_y = self.center
        match dir:
            case "clockwise":
                self.coords = [(-(y - offset_y) + offset_x, (x - offset_x) + offset_y) for x, y in self.coords]
                return self.coords

            case "counterclockwise":
                self.coords = [((y - offset_y) + offset_x, -(x - offset_x) + offset_y) for x, y in self.coords]
                return self.coords


# Class for song to loop in background
class Song:
    def __init__(self, song_path):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.media_list = self.instance.media_list_new([song_path])
        self.media_list_player = self.instance.media_list_player_new()
        self.media_list_player.set_media_list(self.media_list)

    def loop_sound(self):
        self.media_list_player.set_playback_mode(1)
        self.media_list_player.play()

    def stop_sound(self):
        self.media_list_player.stop()


# Main Class
class Tetris(Fl_Window):
    def __init__(self, x, y, w, h, label=None):
        super(Tetris, self).__init__(x, y, w, h, label)
        self.player = None
        self.begin()

        # Game variables
        self.lines_score = 0
        self.score = 0
        self.formatted_score = "{:06d}".format(self.score)

        # Highscore
        try:
            with open("highscore.txt", "r") as file:
                self.top = int(file.read())

        except FileNotFoundError:
            print('Error. It seems the file \'highscore.txt\' has been deleted or missing!')
            self.top = 0

        except ValueError:
            print('Error. Incorrect value type in \'highscore.txt\'')
            self.top = 0

        # Game variables
        self.formatted_top = "{:06d}".format(self.top)
        self.next_shape = []
        self.next_shape_num = -1
        self.speed = 0.8
        self.level = 1
        self.block_list = []
        self.game = False

        # Sounds and song
        self.gameover_sound = "Sounds/gameover.wav"
        self.rotate_sound = "Sounds/rotate.wav"
        self.land_sound = "Sounds/land.wav"
        self.tetris_song = "Sounds/tetris.mp3"
        self.move_sound = "Sounds/move_horizontal.wav"
        # self.highscore_sound = "Sounds\\tetris_sound.mp3" (Don't currently have a highscore noise!)
        self.clearline_sound = "Sounds/clearline.wav"
        self.tetris_sound = "Sounds/tetris_sound.wav"

        # Sound on game startup
        pygame.mixer.init()
        pygame.mixer.music.load(self.tetris_sound)
        pygame.mixer.music.play()

        # Shapes for the pieces
        T_shape = [(5, 5), (6, 5), (5, 6), (4, 5), Fl_PNG_Image('Images/color1.png')]
        S_shape = [(5, 5), (6, 5), (4, 6), (5, 6), Fl_PNG_Image("Images/color2.png")]
        Z_shape = [(5, 5), (6, 6), (4, 5), (5, 6), Fl_PNG_Image("Images/color3.png")]
        J_shape = [(5, 5), (4, 5), (6, 6), (6, 5), Fl_PNG_Image("Images/color4.png")]
        L_shape = [(5, 5), (4, 5), (4, 6), (6, 5), Fl_PNG_Image("Images/color5.png")]
        I_shape = [(5, 5), (4, 5), (3, 5), (6, 5), Fl_PNG_Image("Images/color6.png")]
        O_shape = [(4, 6), (5, 6), (4, 5), (5, 5), Fl_PNG_Image("Images/color7.png")]
        # Color for bricks in gameover
        self.gameover_color = Fl_PNG_Image("Images/color8.png")

        self.shapes = [T_shape, S_shape, Z_shape, J_shape, L_shape, I_shape, O_shape]
        self.shape_names = ["T_shape", "S_shape", "Z_shape", "J_shape", "L_shape", "I_shape", "O_shape"]
        self.shape = []
        self.current_shape = ''

        # Statistics board nums
        self.T_stats = 0
        self.S_stats = 0
        self.Z_stats = 0
        self.L_stats = 0
        self.J_stats = 0
        self.I_stats = 0
        self.O_stats = 0

        # Logo creation
        self.logo_highlight2 = Fl_Box(190, 5, 310, 120)
        self.logo_highlight2.box(FL_BORDER_BOX)
        self.logo_highlight2.color(FL_DARK_CYAN)

        self.logo = Fl_Box(195, 15, 300, 100)
        self.logo.image(self.img_resize('Images/logo.png', 300))

        # Score creation
        self.score_highlight1 = Fl_Box(484, 140, 200, 200)
        self.score_highlight1.box(FL_BORDER_BOX)
        self.score_highlight1.color(FL_DARK_CYAN)

        self.score_highlight2 = Fl_Box(489, 145, 190, 190)
        self.score_highlight2.box(FL_BORDER_BOX)
        self.score_highlight2.color(FL_WHITE)

        self.score_highlight3 = Fl_Box(494, 150, 180, 180)
        self.score_highlight3.box(FL_FLAT_BOX)
        self.score_highlight3.color(FL_BLACK)

        self.score_top = Fl_Box(505, 145, 75, 75, "TOP  ")
        self.score_top.labelcolor(FL_WHITE)
        self.score_top.labelsize(30)

        self.score_top_display = Fl_Box(519, 175, 75, 75, str(self.formatted_top))
        self.score_top_display.labelcolor(FL_WHITE)
        self.score_top_display.labelsize(30)

        self.score_score = Fl_Box(520, 225, 75, 75, "SCORE")
        self.score_score.labelcolor(FL_WHITE)
        self.score_score.labelsize(30)

        self.score_score_display = Fl_Box(519, 255, 75, 75, self.formatted_score)
        self.score_score_display.labelcolor(FL_WHITE)
        self.score_score_display.labelsize(30)

        # Next object creation
        self.next_highlight1 = Fl_Box(484, 339, 200, 200)
        self.next_highlight1.box(FL_BORDER_BOX)
        self.next_highlight1.color(FL_DARK_CYAN)

        self.next_highlight2 = Fl_Box(489, 344, 190, 190)
        self.next_highlight2.box(FL_BORDER_BOX)
        self.next_highlight2.color(FL_WHITE)

        self.next_highlight3 = Fl_Box(494, 349, 180, 180)
        self.next_highlight3.box(FL_FLAT_BOX)
        self.next_highlight3.color(FL_BLACK)

        self.next_shape = Fl_Box(524, 354, 50, 50, "NEXT ")
        self.next_shape.labelcolor(FL_WHITE)
        self.next_shape.labelsize(30)

        self.next_grid = []

        # Grid to display next piece
        for a in range(4):
            temp = []
            for b in range(4):
                x = 530 + (25 * a)
                y = 420 + (25 * b)
                Box = Fl_Box(x, y, 25, 25)
                Box.box(FL_FLAT_BOX)
                Box.color(FL_BLACK)
                temp.append(Box)
            self.next_grid.append(temp)

        # MAKE GRID FOR NEXT BLOCKS

        # Speed/level creation
        self.level_highlight1 = Fl_Box(484, 538, 200, 60)
        self.level_highlight1.box(FL_BORDER_BOX)
        self.level_highlight1.color(FL_DARK_CYAN)

        self.level_highlight2 = Fl_Box(489, 543, 190, 50)
        self.level_highlight2.box(FL_BORDER_BOX)
        self.level_highlight2.color(FL_WHITE)

        self.level_highlight3 = Fl_Box(494, 548, 180, 40)
        self.level_highlight3.box(FL_FLAT_BOX)
        self.level_highlight3.color(FL_BLACK)

        self.level_display = Fl_Box(460, 543, 200, 50, "LEVEL 1")
        self.level_display.labelcolor(FL_WHITE)
        self.level_display.labelsize(30)

        # Lines creation
        self.line_highlight1 = Fl_Box(484, 597, 200, 63)
        self.line_highlight1.box(FL_BORDER_BOX)
        self.line_highlight1.color(FL_DARK_CYAN)

        self.line_highlight2 = Fl_Box(489, 602, 190, 53)
        self.line_highlight2.box(FL_BORDER_BOX)
        self.line_highlight2.color(FL_WHITE)

        self.line_highlight3 = Fl_Box(494, 607, 180, 43)
        self.line_highlight3.box(FL_FLAT_BOX)
        self.line_highlight3.color(FL_BLACK)

        self.line_display = Fl_Box(460, 605, 200, 50, "LINES 0")
        self.line_display.labelcolor(FL_WHITE)
        self.line_display.labelsize(30)

        # Statistics creation
        self.statistics_highlight1 = Fl_Box(25, 200, 191, 460)
        self.statistics_highlight1.box(FL_BORDER_BOX)
        self.statistics_highlight1.color(FL_DARK_CYAN)

        self.statistics_highlight2 = Fl_Box(30, 205, 181, 450)
        self.statistics_highlight2.box(FL_BORDER_BOX)
        self.statistics_highlight2.color(FL_WHITE)

        self.statistics_highlight3 = Fl_Box(35, 210, 171, 440)
        self.statistics_highlight3.box(FL_FLAT_BOX)
        self.statistics_highlight3.color(FL_BLACK)

        self.statistics_display = Fl_Box(90, 210, 50, 50, f" STATISTICS")
        self.statistics_display.labelcolor(FL_WHITE)
        self.statistics_display.labelsize(25)

        self.statistics_list = []
        self.stats_grid = []

        # Grid to show piece statistics
        for a in range(4):
            temp = []

            for b in range(21):
                x = 60 + (18 * a)
                y = 260 + (18 * b)
                Box = Fl_Box(x, y, 18, 18)
                Box.box(FL_FLAT_BOX)
                Box.color(FL_BLACK)
                temp.append(Box)
            self.stats_grid.append(temp)

        for a in range(7):
            stats_box = Fl_Box(140, 250 + a * 53, 50, 50, "0")
            stats_box.labelcolor(FL_RED)
            stats_box.labelsize(20)
            stats_box.box(FL_FLAT_BOX)
            stats_box.color(FL_BLACK)
            self.statistics_list.append(stats_box)

            for b in range(4):
                self.stats_grid[self.shapes[a][b][0] - 4][self.shapes[a][b][1] + a * 3 - 5].image(
                    self.shapes[a][-1].copy(18, 18))

        # Game grid
        self.grid_highlight1 = Fl_Box(215, 140, 270, 520)
        self.grid_highlight1.box(FL_BORDER_BOX)
        self.grid_highlight1.color(FL_DARK_CYAN)

        self.grid_highlight2 = Fl_Box(220, 145, 260, 510)
        self.grid_highlight2.box(FL_BORDER_BOX)
        self.grid_highlight2.color(FL_WHITE)

        self.grid = []
        for a in range(10):
            temp = []
            for b in range(25):
                x = 225 + (25 * a)
                y = 25 + (25 * b)

                Box = Fl_Box(x, y, 25, 25)
                Box.box(FL_FLAT_BOX)
                Box.color(FL_BLACK)
                temp.append(Box)
                if b < 5:
                    Box.hide()
            self.grid.append(temp)

    # Controls
    def handle(self, event):
        if event == FL_KEYDOWN:
            key = Fl.event_key()

            if key == FL_Enter:  # Start/reset the game
                self.game = True
                song_path = "Sounds/tetris.mp3"
                self.player = Song(song_path)
                self.player.loop_sound()
                self.reset()

            elif not self.game:  # Only allow controls if game is playing
                return False

            elif key == FL_Left:  # Move Piece left
                pygame.mixer.init()
                pygame.mixer.music.load(self.move_sound)
                pygame.mixer.music.play()
                self.move_left()

            elif key == FL_Right:  # Move Piece right
                pygame.mixer.init()
                pygame.mixer.music.load(self.move_sound)
                pygame.mixer.music.play()
                self.move_right()

            elif key == FL_Up:  # Drop piece
                self.insta_down()

            elif key == FL_Down:
                self.move_down(True)

            elif key == ord('x'):  # Rotate piece clockwise
                pygame.mixer.init()
                pygame.mixer.music.load(self.rotate_sound)
                pygame.mixer.music.play()

                if self.current_shape == "O_shape":  # Don't need to rotate square
                    return False

                rotated_shape = Piece(self.shape[:-1])
                self.rotate_shape(rotated_shape.rotate('clockwise'))

            elif key == ord('z'):  # Rotate piece counter clockwise
                pygame.mixer.init()
                pygame.mixer.music.load(self.rotate_sound)
                pygame.mixer.music.play()

                if self.current_shape == "O_shape":  # Don't need to rotate square
                    return False

                rotated_shape = Piece(self.shape[:-1])
                self.rotate_shape(rotated_shape.rotate('counterclockwise'))

            else:
                return False
            return True
        return super(Tetris, self).handle(event)

    # Better image resizer (Thanks Mr. Ark)
    def img_resize(self, fname, width):
        """resizes any image type using high quality PIL library"""
        img = Image.open(fname)  # opens all image formats supported by PIL
        w, h = img.size
        height = int(width * h / w)  # correct aspect ratio
        img = img.resize((width, height), Image.Resampling.BICUBIC)  # high quality resizing
        mem = io.BytesIO()  # byte stream memory object
        img.save(mem, format="PNG")  # converts image type to PNG byte stream
        siz = mem.tell()  # gets size of image in bytes without reading again
        return Fl_PNG_Image(None, mem.getbuffer(), siz)

    # Display the next shape
    def nextshape(self):
        ns = self.next_shape_num
        self.next_shape_num = random.randrange(len(self.shapes))
        self.next_shape = self.shapes[self.next_shape_num].copy()

        # Clear next grid and draw new shape
        for x in range(4):
            for y in range(4):
                self.next_grid[x][y].image(None)
                self.next_grid[x][y].redraw()

        for x in range(len(self.next_shape) - 1):
            self.next_grid[self.next_shape[x][0] - 4][self.next_shape[x][1] - 9].image(self.next_shape[-1].copy(25, 25))
            self.next_grid[self.next_shape[x][0] - 4][self.next_shape[x][1] - 9].redraw()

        # Only for first piece
        if ns == -1:
            ns = random.randrange(len(self.shapes))
        return ns

    # Creates a new shape, if there is no room for it, gameover
    def newshape(self):
        ns = self.nextshape()
        self.shape = self.shapes[ns].copy()
        self.current_shape = self.shape_names[ns]
        self.statistics_list[self.shapes.index(self.shape)].label(
            str(int(self.statistics_list[self.shapes.index(self.shape)].label()) + 1))
        for x in range(len(self.shape) - 1):

            self.grid[self.shape[x][0]][self.shape[x][1]].redraw()

            if self.grid[self.shape[x][0]][self.shape[x][1]].image() != None:
                self.gameover()
                return False

        for x in range(len(self.shape) - 1):
            self.grid[self.shape[x][0]][self.shape[x][1]].image(self.shape[-1].copy(25, 25))
            self.grid[self.shape[x][0]][self.shape[x][1]].redraw()
        Fl_add_timeout(self.speed, self.move_down, False)

    # Move the block down repeatedly by either timeout and player control(to speed up)
    def move_down(self, key):
        for x in range(len(self.shape) - 1):
            if self.shape[x][1] + 1 >= 25:  # Bottom of grid, can not be moved down
                if not key:
                    pygame.mixer.init()
                    pygame.mixer.music.load(self.land_sound)
                    pygame.mixer.music.play()

                    Fl_remove_timeout(self.move_down)
                    self.clear_lines()

                    self.newshape()

                return
            if self.grid[self.shape[x][0]][self.shape[x][1] + 1].image() != None:  # Hit a piece, can not move down
                if (self.shape[x][0], self.shape[x][1] + 1) not in self.shape:  # Make sure image isn't part of the current piece
                    if key == False:
                        pygame.mixer.init()
                        pygame.mixer.music.load(self.land_sound)
                        pygame.mixer.music.play()
                        Fl_remove_timeout(self.move_down)
                        self.clear_lines()

                        self.add_points(50, 0)
                        self.newshape()

                    return

        # Moving of the piece down (y+1)
        for x in range(len(self.shape) - 1):
            self.grid[self.shape[x][0]][self.shape[x][1]].image(None)
            self.grid[self.shape[x][0]][self.shape[x][1]].redraw()
            self.shape[x] = (self.shape[x][0], self.shape[x][1] + 1)

        for x in range(len(self.shape) - 1):
            if self.shape[x][1] < 0:
                continue
            self.grid[self.shape[x][0]][self.shape[x][1]].image(self.shape[-1].copy(25, 25))
            self.grid[self.shape[x][0]][self.shape[x][1]].redraw()

        if key == False:
            Fl_add_timeout(self.speed, self.move_down, False)

    # Player left input
    def move_left(self):
        for x in range(len(self.shape) - 1):  # Make sure in bounds of grid and not moving into other pieces
            if self.shape[x][0] - 1 < 0:
                return
            if self.grid[self.shape[x][0] - 1][self.shape[x][1]].image() != None:
                if (self.shape[x][0] - 1, self.shape[x][1]) not in self.shape:
                    return

        for x in range(len(self.shape) - 1):
            self.grid[self.shape[x][0]][self.shape[x][1]].image(None)
            self.grid[self.shape[x][0]][self.shape[x][1]].redraw()
            self.shape[x] = (self.shape[x][0] - 1, self.shape[x][1])

        for x in range(len(self.shape) - 1):
            self.grid[self.shape[x][0]][self.shape[x][1]].image(self.shape[-1].copy(25, 25))
            self.grid[self.shape[x][0]][self.shape[x][1]].redraw()

    # Player right input
    def move_right(self):
        for x in range(len(self.shape) - 1):  # Make sure in bounds of grid and not moving into other pieces
            if self.shape[x][0] + 1 >= 10:
                return
            if self.grid[self.shape[x][0] + 1][self.shape[x][1]].image() != None:
                if (self.shape[x][0] + 1, self.shape[x][1]) not in self.shape:
                    return

        for x in range(len(self.shape) - 1):
            self.grid[self.shape[x][0]][self.shape[x][1]].image(None)
            self.grid[self.shape[x][0]][self.shape[x][1]].redraw()
            self.shape[x] = (self.shape[x][0] + 1, self.shape[x][1])

        for x in range(len(self.shape) - 1):
            self.grid[self.shape[x][0]][self.shape[x][1]].image(self.shape[-1].copy(25, 25))
            self.grid[self.shape[x][0]][self.shape[x][1]].redraw()

    # Instantly drops piece to the lowest position
    def insta_down(self):  # Similar to move down but instant and only redefines image at end of process
        for x in range(len(self.shape) - 1):
            self.grid[self.shape[x][0]][self.shape[x][1]].image(None)
            self.grid[self.shape[x][0]][self.shape[x][1]].redraw()

        for x in range(len(self.shape) - 1):
            if self.shape[x][1] + 1 >= 25:
                for x in range(len(self.shape) - 1):
                    self.grid[self.shape[x][0]][self.shape[x][1]].image(self.shape[-1].copy(25, 25))
                    self.grid[self.shape[x][0]][self.shape[x][1]].redraw()

                pygame.mixer.init()
                pygame.mixer.music.load(self.land_sound)
                pygame.mixer.music.play()

                Fl_remove_timeout(self.move_down)
                self.clear_lines()
                self.newshape()

                return
            if self.grid[self.shape[x][0]][self.shape[x][1] + 1].image() != None:
                if (self.shape[x][0], self.shape[x][1] + 1) not in self.shape:
                    for x in range(len(self.shape) - 1):
                        self.grid[self.shape[x][0]][self.shape[x][1]].image(self.shape[-1].copy(25, 25))
                        self.grid[self.shape[x][0]][self.shape[x][1]].redraw()

                    pygame.mixer.init()
                    pygame.mixer.music.load(self.land_sound)
                    pygame.mixer.music.play()
                    Fl_remove_timeout(self.move_down)
                    self.clear_lines()

                    self.add_points(50, 0)
                    self.newshape()

                    return

        for x in range(len(self.shape) - 1):
            self.shape[x] = (self.shape[x][0], self.shape[x][1] + 1)

        self.insta_down()

    # Rotation of current piece
    def rotate_shape(self, newshape):
        for x in range(len(newshape)):  # Make sure in bounds

            if newshape[x][0] >= 10:
                return

            if newshape[x][1] >= 20:
                return

            if newshape[x][0] < 0:
                return

            if self.grid[newshape[x][0]][newshape[x][1]].image() != None:  # Make sure not to rotate into other blocks
                if (newshape[x][0], newshape[x][1]) not in self.shape:
                    if newshape[x][1] > 0:
                        return

        for x in range(len(self.shape) - 1):
            if self.shape[x][1] > 0:
                self.grid[self.shape[x][0]][self.shape[x][1]].image(None)
                self.grid[self.shape[x][0]][self.shape[x][1]].redraw()

        self.shape[:-1] = newshape

        for x in range(len(self.shape) - 1):
            if self.shape[x][1] > 0:
                self.grid[self.shape[x][0]][self.shape[x][1]].image(self.shape[-1].copy(25, 25))
                self.grid[self.shape[x][0]][self.shape[x][1]].redraw()

    # Check if line is full, clear full lines and move everything above down
    def clear_lines(self):

        cleared_lines = []
        for y in range(5, 25):  # Checks all lines
            line_empty = False
            for x in range(10):
                if self.grid[x][y].image() == None:
                    line_empty = True
                    break
            if not line_empty:
                cleared_lines.append(y)  # List of lines needed to be cleared
        if cleared_lines == 0:
            return

        for line in cleared_lines:
            for x in range(10):
                self.grid[x][line].image(None)
                self.grid[x][line].redraw()
            for y in range(line, 0, -1):
                for x in range(10):  # Moving everything above down
                    if self.grid[x][y - 1].image() != None:
                        self.grid[x][y].image(self.grid[x][y - 1].image().copy(25, 25))
                        self.grid[x][y].redraw()
                        self.grid[x][y - 1].image(None)
                        self.grid[x][y - 1].redraw()

        if len(cleared_lines) > 0:
            self.add_points(len(cleared_lines), len(cleared_lines))

    # Score, Highscore, lines, and level calculation
    def add_points(self, points, lines):
        if lines > 0:
            if lines < 4:
                pygame.mixer.init()
                pygame.mixer.music.load(self.clearline_sound)
                pygame.mixer.music.play()

            if lines == 1:
                points = 400

            elif lines == 2:
                points = 800

            elif lines == 3:
                points = 1200

            if lines == 4:  # Tetris!
                points = 2000

                pygame.mixer.init()
                pygame.mixer.music.load(self.tetris_sound)
                pygame.mixer.music.play()

        # Reformatting displays
        self.lines_score += lines
        if self.lines_score > 0:
            self.line_display.label(f"  LINES {str(self.lines_score)}")
            self.line_display.redraw_label()

        self.score += points
        self.formatted_score = "{:06d}".format(self.score)
        self.score_score_display.label(self.formatted_score)
        self.score_score_display.redraw_label()

        if self.score > self.top:
            self.top = self.score
            self.formatted_top = "{:06d}".format(self.top)
            self.score_top_display.label(self.formatted_top)

        if self.level == 5:
            return
        if self.level != self.lines_score // 10 + 1:  # Increase speed every 10 lines or 1 level up to 5 times
            self.speed = self.speed / 1.5
        self.level = self.lines_score // 10 + 1
        self.level_display.label(f"  LEVEL {str(self.level)}")
        self.level_display.redraw_label()
        return

    # Resets the game
    def reset(self):
        self.player.stop_sound()
        for x in range(10):
            for y in range(25):
                self.grid[x][y].image(None)

        for x in range(7):
            self.statistics_list[x].label("0")

        for x in range(4):
            for y in range(4):
                self.next_grid[x][y].image(None)

        self.lines_score = 0
        self.level = 1
        self.score = 0
        self.formatted_score = "{:06d}".format(self.score)
        self.score_top_display.label(str(self.formatted_top))
        self.line_display.label("LINES 0")
        self.level_display.label("LEVEL 1")
        self.speed = 0.8
        Fl_remove_timeout(self.move_down)
        self.redraw()

        self.newshape()

        return

    # Gameover D:
    def gameover(self):
        self.game = False
        self.player.stop_sound()
        if self.score == self.top:  # If new highscore, save it
            with open("highscore.txt", "w") as file:
                file.write(str(self.top))
                print('New Highscore!')

        pygame.mixer.init()
        pygame.mixer.music.load(self.gameover_sound)
        pygame.mixer.music.play()

        for x in range(10):
            for y in range(25):
                self.grid[x][y].image(self.gameover_color.copy(25, 25))

        self.redraw()


if __name__ == "__main__":
    window = Tetris(100, 100, 700, 700, "Tetris")
    window.end()
    window.show()
    Fl.run()
