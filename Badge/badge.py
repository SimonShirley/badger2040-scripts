import time
import badger2040
import badger_os
import os
import jpegdec
import pngdec
import gc

# Multiple badge text and image files supported. All files to be placed in newly created '/badges/' folder.
# Associated image files to be named the same as the text file.
# For each text file e.g. 'badge.txt', an associated image file e.g. 'badge.jpg' or 'badge.png' will load

# ------------------------------
#       Global Constants
# ------------------------------

WIDTH = badger2040.WIDTH
HEIGHT = badger2040.HEIGHT

IMAGE_WIDTH = 104

COMPANY_HEIGHT = 30
DETAILS_HEIGHT = 20
NAME_HEIGHT = HEIGHT - COMPANY_HEIGHT - (DETAILS_HEIGHT * 2) - 2
TEXT_WIDTH = WIDTH - IMAGE_WIDTH - 1

COMPANY_TEXT_SIZE = 0.6
DETAILS_TEXT_SIZE = 0.5

LEFT_PADDING = 5
NAME_PADDING = 20
DETAIL_SPACING = 10

DEFAULT_TEXT = """mustelid inc
H. Badger
RP2040
2MB Flash
E ink
296x128px"""

PEN_THICKNESS_1 = 1
PEN_THICKNESS_2 = 1
PEN_THICKNESS_3 = 2
PEN_THICKNESS_4 = 3

FONT_SERIF = "sans"
FONT_SANS = "sans"

BADGE_DIR = "/badges" # Note: No trailing slash. Code will add it when referencing.

# ------------------------------
#      Utility functions
# ------------------------------
# Reduce the size of a string until it fits within a given width
def truncatestring(text, text_size, width):
    while True:
        length = display.measure_text(text, text_size)
        if length > 0 and length > width:
            text = text[:-1]
        else:
            text += ""
            return text
        
def set_state_current_index_in_range():
    badger_os.state_load("badges", state)
    
    if state["current_badge"] >= len(BADGES):
        state["current_badge"] = len(BADGES) - 1  # set to last index (zero-based). Note: will set to -1 if currently 0
        
    if state["current_badge"] < 0:  # check that the index is not negative, thus still out of range
        state["current_badge"] = 0
        
    badger_os.state_save("badges", state)

# ------------------------------
#      Drawing functions
# ------------------------------

# Draw the badge, including user text
def draw_badge(n):
    # Reset to default badge if state badge removed
    if len(BADGES) <= n:
        n = 0
        badger_os.state_modify("badges", {"current badge": n})
        
    file = BADGES[n]
    badge_text_file_path = ""
    image_file_path = ""
    company = ""
    name = ""
    detail1_title = ""
    detail1_text = ""
    detail2_title = ""
    detail2_text = ""    

    try:
        badge_text_file_path = f"{BADGE_DIR}/{file}"
        
        with open(badge_text_file_path, "r") as badge_text_file:
            # Read in the next 6 lines
            company = badge_text_file.readline()        # "mustelid inc"
            name = badge_text_file.readline()           # "H. Badger"
            detail1_title = badge_text_file.readline()  # "RP2040"
            detail1_text = badge_text_file.readline()   # "2MB Flash"
            detail2_title = badge_text_file.readline()  # "E ink"
            detail2_text = badge_text_file.readline()   # "296x128px"
    except:
        display_warning(f"Unable to open / read badge text file\n{badge_text_file_path}")
        return

    # Truncate all of the text (except for the name as that is scaled)
    company = truncatestring(company, COMPANY_TEXT_SIZE, TEXT_WIDTH)

    detail1_title = truncatestring(detail1_title, DETAILS_TEXT_SIZE, TEXT_WIDTH)
    detail1_text = truncatestring(detail1_text, DETAILS_TEXT_SIZE,
                                  TEXT_WIDTH - DETAIL_SPACING - display.measure_text(detail1_title, DETAILS_TEXT_SIZE))

    detail2_title = truncatestring(detail2_title, DETAILS_TEXT_SIZE, TEXT_WIDTH)
    detail2_text = truncatestring(detail2_text, DETAILS_TEXT_SIZE,
                                  TEXT_WIDTH - DETAIL_SPACING - display.measure_text(detail2_title, DETAILS_TEXT_SIZE))

    display.set_pen(0)
    display.clear()
        
    # draw a white rectangle where the image will sit, in case the image has an error
    display.set_pen(15)
    display.rectangle(WIDTH - IMAGE_WIDTH, 0, IMAGE_WIDTH, HEIGHT)
    
    # Try and import image related to txt file
    image_filename = str(file).split(".")[0] + ".jpg"
    image_file_path = f"{BADGE_DIR}/{image_filename}"
    
    try:
        if image_filename in os.listdir(BADGE_DIR):
            with open(image_file_path, "rb") as jpeg_file:
                jpeg_file_bytes = jpeg_file.read()
                jpeg.open_RAM(jpeg_file_bytes)
                jpeg.decode(WIDTH - IMAGE_WIDTH, 0)
        else:
            image_filename = str(file).split(".")[0] + ".png"
            image_file_path = f"{BADGE_DIR}/{image_filename}"
            
            if image_filename in os.listdir(BADGE_DIR):
                with open(image_file_path, "rb") as png_file:
                    png_file_bytes = png_file.read()
                    png.open_RAM(png_file_bytes)
                    png.decode(WIDTH - IMAGE_WIDTH, 0)
    except:
        pass
    
    gc.collect()
            
    # Draw a border around the image
    display.set_pen(0)
    display.set_thickness(1)
    display.line(WIDTH - IMAGE_WIDTH, 0, WIDTH - 1, 0)
    display.line(WIDTH - IMAGE_WIDTH, 0, WIDTH - IMAGE_WIDTH, HEIGHT - 1)
    display.line(WIDTH - IMAGE_WIDTH, HEIGHT - 1, WIDTH - 1, HEIGHT - 1)
    display.line(WIDTH - 1, 0, WIDTH - 1, HEIGHT - 1)

    # Uncomment this if a white background is wanted behind the company
    # display.set_pen(15)
    # display.rectangle(1, 1, TEXT_WIDTH, COMPANY_HEIGHT - 1)

    # Draw the company
    display.set_pen(15)  # Change this to 0 if a white background is used
    display.set_font(FONT_SERIF)
    display.set_thickness(PEN_THICKNESS_3)
    display.text(company, LEFT_PADDING, (COMPANY_HEIGHT // 2) + 1, WIDTH, COMPANY_TEXT_SIZE)

    # Draw a white background behind the name
    display.set_pen(15)
    display.set_thickness(1)
    display.rectangle(1, COMPANY_HEIGHT + 1, TEXT_WIDTH, NAME_HEIGHT)

    # Draw the name, scaling it based on the available width
    display.set_pen(0)
    display.set_font(FONT_SANS)
    display.set_thickness(PEN_THICKNESS_4)
    name_size = 2.0  # A sensible starting scale
    
    while True:
        name_length = display.measure_text(name, name_size)            
        if name_length >= (TEXT_WIDTH - NAME_PADDING) and name_size >= 0.1:
            name_size -= 0.01
        else:                
            display.text(name, (TEXT_WIDTH - name_length) // 2, (NAME_HEIGHT // 2) + COMPANY_HEIGHT + 1, WIDTH, name_size)
            break

    # Draw a white backgrounds behind the details
    display.set_pen(15)
    display.set_thickness(1)
    display.rectangle(1, HEIGHT - DETAILS_HEIGHT * 2, TEXT_WIDTH, DETAILS_HEIGHT - 1)
    display.rectangle(1, HEIGHT - DETAILS_HEIGHT, TEXT_WIDTH, DETAILS_HEIGHT - 1)

    # Draw the first detail's title and text
    display.set_pen(0)
    display.set_font(FONT_SERIF)
    display.set_thickness(PEN_THICKNESS_3)
    name_length = display.measure_text(detail1_title, DETAILS_TEXT_SIZE)
    display.text(detail1_title, LEFT_PADDING, HEIGHT - ((DETAILS_HEIGHT * 3) // 2), WIDTH, DETAILS_TEXT_SIZE)
    display.set_thickness(PEN_THICKNESS_2)
    display.text(detail1_text, 5 + name_length + DETAIL_SPACING, HEIGHT - ((DETAILS_HEIGHT * 3) // 2), WIDTH, DETAILS_TEXT_SIZE)

    # Draw the second detail's title and text
    display.set_thickness(PEN_THICKNESS_3)
    name_length = display.measure_text(detail2_title, DETAILS_TEXT_SIZE)
    display.text(detail2_title, LEFT_PADDING, HEIGHT - (DETAILS_HEIGHT // 2), WIDTH, DETAILS_TEXT_SIZE)
    display.set_thickness(PEN_THICKNESS_2)
    display.text(detail2_text, LEFT_PADDING + name_length + DETAIL_SPACING, HEIGHT - (DETAILS_HEIGHT // 2), WIDTH, DETAILS_TEXT_SIZE)

    # Draw selection indicator to bottom right of image
    if TOTAL_BADGES > 1:
        for i in range(TOTAL_BADGES):
            x = 291
            y = int((128) - (TOTAL_BADGES * 5) + (i * 5))
            display.set_pen(0)
            display.rectangle(x, y, 4, 4)
            if state["current_badge"] != i:
                display.set_pen(15)
                display.rectangle(x + 1, y + 1, 2, 2)
    display.update();                
                
def display_warning(message):        
    display.clear()
    badger_os.warning(display, message)
    time.sleep(4)             

def make_badges_folder_if_not_exists():
    # Check that the badges directory exists, if not, make it
    try:
        os.mkdir(BADGE_DIR)
    except OSError:
        pass
    
def get_list_of_badge_files():
    # Load all available badge Files
    try:
        BADGES = [f for f in os.listdir(BADGE_DIR) if f.endswith(".txt")]
    except OSError:
        pass

    if len(BADGES) == 0:
        new_badge_file_name = "badge.txt"
        
        # Check that there is a badges.txt, if not preload
        if not new_badge_file_name in os.listdir(BADGE_DIR):
            with open(f"{BADGE_DIR}/{new_badge_file_name}", "w") as text:
                text.write(DEFAULT_TEXT)
                text.flush()
        
        BADGES = [new_badge_file_name]
        
    return BADGES

# ------------------------------
#        Program setup
# ------------------------------

make_badges_folder_if_not_exists()
BADGES = get_list_of_badge_files()
    
TOTAL_BADGES = len(BADGES)

state = { "current_badge": 0 }

# Create a new Badger and set it to update NORMAL
display = badger2040.Badger2040()
display.led(128)
display.set_update_speed(badger2040.UPDATE_NORMAL)
display.set_thickness(2)

jpeg = jpegdec.JPEG(display.display)
png = pngdec.PNG(display.display)

set_state_current_index_in_range()
changed = True

# ------------------------------
#       Main program
# ------------------------------

while True:
    # Sometimes a button press or hold will keep the system
    # powered *through* HALT, so latch the power back on.
    display.keepalive();
    
    if TOTAL_BADGES > 1:
        if display.pressed(badger2040.BUTTON_UP):
            if state["current_badge"] > 0:
                state["current_badge"] -= 1
                changed = True

        if display.pressed(badger2040.BUTTON_DOWN):
            if state["current_badge"] < TOTAL_BADGES - 1:
                state["current_badge"] += 1
                changed = True
                
    if display.pressed(badger2040.BUTTON_B):
        # Refresh the screen
        changed = True

    if changed:
        draw_badge(state["current_badge"])
        badger_os.state_save("badges", state)
        changed = False

    # If on battery, halt the Badger to save power, it will wake up if any of the front buttons are pressed
    display.halt()