import pygame.camera
import json
import time
import pygame
import math  # needed for joystick
import widgets2 as widgets # needed to make widgets function properly
import serial  # needed to talk with Arduino
import os  # for creating the picture folder

# GUI window setup
sideBarWidth = 300
pygame.init()  # Initializes the pygame modules
size = width, height = 900 + sideBarWidth, 800  # size of GUI
pygame.display.set_caption('ROV Control')
screen = pygame.display.set_mode(size)
screen.fill((16, 43, 87))

# Define the name of the output folder
folder_name = "ROV_3D"

# Create the folder if it doesn't exist
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

# camera setup
camera_width = 640
camera_height = 400
pygame.camera.init()  # Initializes the camera modules from the pygame library : Added 5/8/23

# initialize two cameras (loading the camera modules)
# Note: Camera indices typically begin with 0 (built in camera or first connected camera), then 1, 2, 3, etc..
cam1 = pygame.camera.Camera(0, (camera_width, camera_height))  # Main camera (adjust camera index for your unique PC setup)
# cam2 = pygame.camera.Camera(2, (camera_width, camera_height)) # Disabled to avoid servo claw jitter
cameraSurface = pygame.Surface((camera_width, camera_height*2), pygame.SRCALPHA)

transparency = 0
cameraSurface.fill((0, 0, 0, transparency))

# start the cameras (turn on cameras)
cam1.start()
# cam2.start() # Disabled to avoid sersvo claw jitter

# setup displays in GUI
guiScreen = pygame.Surface((80 + sideBarWidth, 800), pygame.SRCALPHA)
guiTransparency = 0
guiScreen.fill((0, 0, 0, guiTransparency))

onStatus = widgets.toggleable("Running", sideBarWidth)  # label and size toggle
zSlider = widgets.sliderdisplay("Z", 100, 320)
mLeftSlider = widgets.sliderdisplay("LeftSlider", 100, 320)
mRightSlider = widgets.sliderdisplay("RightSlider", 100, 320)

temp_display = widgets.display("Temp (C)", sideBarWidth)
th_up_display = widgets.display("Servo Up", sideBarWidth)
th_left_display = widgets.display("Servo Left", sideBarWidth)
th_right_display = widgets.display("Servo Right", sideBarWidth)
claw_display = widgets.display("Main Claw Value", sideBarWidth)
claw_rotate_display = widgets.display("claw rotate Value", sideBarWidth)

font = pygame.font.SysFont("monospace", 16)
leftText = font.render("Left", True, (255, 255, 255))
rightText = font.render("Right", True, (255, 255, 255))
ZAxisText = font.render("Z-axis", True, (255, 255, 255))

Controls = font.render("User Controls: ", True, (255, 255, 255)) 
left_button = font.render("LB: Close Claw", True, (255, 255, 255))
right_button = font.render("RB: Open Claw", True, (255, 255, 255))
button_A = font.render("A: Toggle Max Thrust", True, (255, 255, 255))
LF_Joy_Up = font.render("Left Joy Up: Forward", True, (255, 255, 255))
LF_Joy_Down = font.render("Left Joy Down: Reverse", True, (255, 255, 255))
LF_Joy_Left = font.render("Left Joy Left: Turn Left", True, (255, 255, 255))
LF_Joy_Right = font.render("Left Joy Right: Turn Right", True, (255, 255, 255))
RG_Joy_Up = font.render("Right Joy Up: Ascend", True, (255, 255, 255))
RG_Joy_Down = font.render("Right Joy Down: Descend", True, (255, 255, 255))

# Logo Image setup
# loading the image
# image = pygame.image.load("images/My project-1.png") # Can comment this line of code out if you do not have a logo file within same directory

# Scale the image
# scaledImage = pygame.transform.scale(image, (240, 200)) # Can comment this line of code out if you do not have a logo file within same directory

# open serial com to Arduino
ser = serial.Serial(port='COM12', baudrate=9600, timeout=.1, dsrdtr=True) # Can comment this out if Arduino board is not connected to USB serial port.
# dsrdtr=True stops Arduino Mega from auto resetting

trigger_button = [False, False]
claw_rotate_left = False
claw_rotate_right = False  # Initialize False Boolean values for Left Button and Right Button
# trigger_button = [(LeftButton State) = False, (RightButton State) = False].
# This is so that the trigger buttons do not increment/decrement the clawValue unless triggered by user.

#x_y_button = [False, False] # for D-pad controls

# Initialize min/max and clawValues
max_value = 80  # After some tests with the claw, 0-80 is the ideal safe operating range for the claw (0 = fully closed, 80 = fully opened.)
min_value = 0
clawValue = 0
clawRotate = 0
max_Rotate = 360
min_Rotate = 0
# Initialize joystick
joystick = None
if pygame.joystick.get_count() == 0:
    print('No joystick Detected')
else:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()  # initialize joystick
# Set the variable to control image capture
capture_count = 0
# Main Event Loop
while True:
    # Get input from joystick and keyboard
    pygame.event.pump()
    key = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            cam1.stop()
            # cam2.stop() # Disabled to avoid servo claw jitter
            pygame.quit()
            quit()
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # Button A; Button ID: 0 used for toggling max thruster status On/Off
                onStatus.toggle()

            if event.button == 4:  # Left Button on Controller
                trigger_button[0] = True
            elif event.button == 5:  # Right Button on Controller
                trigger_button[1] = True

            if event.button == 2:
                claw_rotate_left = True
                print("claw rotate is now true")
            if event.button == 3:
                claw_rotate_right = True
                print("claw rotate is now true")

        if event.type == pygame.JOYBUTTONUP:  # Using JoyButtonUp method (trigger button is released or x/y buttons are released)
            if event.button == 4:  # If Left Trigger Button is released, then set Boolean value back to False
                trigger_button[0] = False
            elif event.button == 5:  # If Right Trigger Button is released, then set Boolean value back to False
                trigger_button[1] = False

            if event.button == 2:
                claw_rotate_left = False
                print("claw rotate is now false")
            if event.button == 3:
                claw_rotate_right = False
                print("claw rotate is now true")

        
        # Originally for task 2.1 Coral Head 3D modeling via Underwater Photogrammetry. (Completely unused in the end)
        if event.type == pygame.JOYBUTTONDOWN:  # for taking pictures
            if event.button == 1:
                capture_count += 1
                img_filename = f'ROV_3D/capture_{capture_count}.jpg'
                img_surface = cam1.get_image()
                pygame.image.save(img_surface, img_filename)
                print(f"Image captured and saved as {img_filename}")

        # Optional: Rebinded forward/reverse thruster movement to D-pad (ran out of time to fully test this feature)
        # if event.type == pygame.JOYHATMOTION:
        #     hat_state = joystick.get_hat(0) # Index 0 means the first available d-pad on the controller
        #     if hat_state == (0, 1):  # D-pad pointing up
        #         x_y_button[0] = True
        #     elif hat_state == (0, -1):
        #         x_y_button[1] = True
        #     else:
        #         x_y_button = [False, False]

    # Incrementing/Decrementing the Main Claw Values
    if trigger_button[0] == True:
        if clawValue >= max_value:
            clawValue = max_value
        else:
            clawValue += 5  # After some testing, increment and decrement value of 5 is the most optimal.
    elif trigger_button[1] == True:
        if clawValue <= min_value:
            clawValue = min_value
        else:
            clawValue -= 5
    # Sets the ClawValue to the value the moment the button is released.

    #4
    elif trigger_button[0] == False:
        clawValue = clawValue
    # 3
    elif trigger_button[1] == False:
        clawValue = clawValue

    if claw_rotate_right == True:
        if clawRotate >= max_value:
            clawRotate = max_Rotate
            
        else:
            clawRotate += 5

        print("inside rotateright true, claw rotate value is now", clawRotate)
    elif claw_rotate_right == False:
        clawRotate = clawRotate
        print("inside rotateright false, claw rotate value is now", clawRotate)

    # 2
    if claw_rotate_left == True:
        if clawRotate <= min_Rotate:
            clawRotate = min_Rotate
        else:
            clawRotate -= 5

        print("inside rotateleft true, claw rotate value is now", clawRotate)
    elif claw_rotate_left == False:
        clawRotate = clawRotate

        print("inside rotatelft false, claw rotate value is now", clawRotate)
    # 1


# Commands to send ROV
    commands = {}  # define python dictionary
    if joystick is not None:
        x = joystick.get_axis(1)  # left joystick -1 is left to +1 is right (left thruster)
        y = joystick.get_axis(0)  # left joystick -1 is up +1 is down (right thruster)
        z = joystick.get_axis(3)  # right joystick x-axis, used for vertical
    else:
        x=0
        y=0
        z=0
    
    if abs(x) < .5:  # define a dead zone
        x = 0
    if abs(y) < .5:  # define a dead zone
        y = 0
    if abs(z) < .2:  # define a dead zone
        z = 0
    # When the status is toggled to "On" by pressing Button A on the controller:
    # Limits thrust for SURGE direction (forward/backward).
    if onStatus.state:
        x = x * 1.414  # gives value of 1 for full thrust forward and backwards
        y = y * 1.414  # gives value of 1 for full thrust forward and backwards

    # rotate x and y-axis of joystick 45 degrees
    x_new = (x * math.cos(math.pi / -4)) - (y * math.sin(math.pi / -4))  # horizontal left
    y_new = (x * math.sin(math.pi / -4)) + (y * math.cos(math.pi / -4))  # horizontal right

    # limits joystick values to +/- 1
    if x_new > 1:
        x_new = 1.0
    if y_new > 1:
        y_new = 1.0
    if x_new < -1:
        x_new = -1.0
    if y_new < -1:
        y_new = -1.0

    # add to dictionarya
    # Cubing the values gives more control with lower power
    # These are the commands being sent to the Arduino Mega Board
    commands['claw_rotate'] = clawRotate  # send the claw value
    commands['tleft'] = x_new ** 3
    commands['tright'] = y_new ** 3

    commands['claw'] = clawValue
    commands['tup'] = z ** 3
    print("Claw value is\n")
    print(clawRotate)
   

    # Optional rebinding of Forward/Reverse to D-pad on the Xbox controller.
    # if x_y_button[0] == True and joystick is not None:
    #     commands['tleft'] = 0.5 ** 3
    #     commands['tright'] = 0.5 ** 3
    # if x_y_button[1] == True and joystick is not None:
    #     commands['tleft'] == -0.5 ** 3
    #     commands['tright'] == -0.5 ** 3
    # if x_y_button[0] == False and x_y_button[1] == False and joystick is None:
    #     commands['tleft'] = 0
    #     commands['tright'] = 0

    mLeftSlider.value = - commands['tleft']  # assign thruster values to a display
    mRightSlider.value = commands['tright']
    zSlider.value = - commands['tup']
    
    print("Before parsing to JSON: ")
    print(commands['claw_rotate'])
    MESSAGE = json.dumps(commands)  # puts python dictionary in Json format
    ser.write(bytes(MESSAGE, 'utf-8'))  # byte format sent to arduino
    ser.flush()
    print("Before geting back from Arduino JSON: ")
    print(commands['claw_rotate'])
    try:
        data = ser.readline().decode("utf-8")  # decode into byte from Arduino
        dict_json = json.loads(data)  # data from arduino in dictionary form

        print("After getting JSON back from Arduino:")
        print(dict_json['claw_rotate'])


        print("Printing the whole JSOn file now")
        print(dict_json)
        
        temp_display.value = dict_json['volt']  # assign temp to dispaly
        th_up_display.value = dict_json['sig_up_1']  # vertical thruster value from Arduino
        th_left_display.value = dict_json['sig_lf']  # vertical thruster value from Arduino
        th_right_display.value = dict_json['sig_rt']  # vertical thruster value from Arduino
        claw_display.value = dict_json['claw']  # claw value from Arduino
        claw_rotate_display.value = dict_json['claw_rotate']
        #ser.flush()

    except Exception as e:
        print(e)

    pass
    # Draw Stuff (Rendering the data as a display for the GUI)
    dHeight = onStatus.get_height() # get the height of the toggleable widget
    guiScreen.blit(onStatus.render(), (0, 0)) # blitting the running status
    guiScreen.blit(mLeftSlider.render(), (0, 9 * dHeight)) # blitting thruster values
    guiScreen.blit(mRightSlider.render(), (100, 9 * dHeight)) # blitting thruster values
    guiScreen.blit(zSlider.render(), (200, 9 * dHeight))  # blitting thruster values

    guiScreen.blit(temp_display.render(), (0, dHeight))  # blitting temperature values# pick a font you have and set its size
    guiScreen.blit(th_up_display.render(), (0, 2 * dHeight)) # blitting thruster values
    guiScreen.blit(th_left_display.render(), (0, 3 * dHeight)) # blitting thruster values
    guiScreen.blit(th_right_display.render(), (0, 4 * dHeight)) # blitting thruster values
    guiScreen.blit(claw_display.render(), (0, 5 * dHeight))  # display the claw value on the screen
    guiScreen.blit(claw_rotate_display.render(),( 0, 6* dHeight))
    # Capture images from the camera (cameras 1 and 2)
    img1 = cam1.get_image()
    # img2 = cam2.get_image() # Camera 2 disabled to avoid servo claw jitter. 

    # Rendering camera display images onto the GUI menu
    cameraSurface.blit(img1, (0, 0))  # surface for camera 1
    # cameraSurface.blit(img2, (0, 400))  # surface for camera 2

    # Rendering more labeling and display elements onto Pygame window.
    screen.blit(cameraSurface, (460, 0))  # 2 cameras
    screen.blit(guiScreen, (0, 140))  # all the gui
    # screen.blit(scaledImage, (10, -60))  # discord logo
# Rending the text for the user controls onto the GUI window as defined in the beginning of the code.
    screen.blit(leftText, (15, 290))
    screen.blit(rightText, (115, 290))
    screen.blit(ZAxisText, (215, 290))
    screen.blit(Controls, (720, 390))
    screen.blit(left_button, (650, 425))
    screen.blit(right_button, (650, 450))
    screen.blit(button_A, (650, 470))
    screen.blit(LF_Joy_Up, (650, 495))
    screen.blit(LF_Joy_Down, (650, 520))
    screen.blit(LF_Joy_Left, (650, 550))
    screen.blit(LF_Joy_Right, (650, 570))
    screen.blit(RG_Joy_Up, (650, 600))
    screen.blit(RG_Joy_Down, (650, 620))

    pygame.display.flip()  # update screen for all rectangular images
