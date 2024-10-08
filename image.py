# Written by Brian Ejike (2017)
# Distributed under the MIT License

import serial, time

WIDTH = 256
HEIGHT = 288
READ_LEN = int(WIDTH * HEIGHT / 2)
    
DEPTH = 8
HEADER_SZ = 54

portSettings = ['', 0]

print("----------Extract Fingerprint Image------------")
print()

# assemble bmp header for a grayscale image
def assembleHeader(width, height, depth, cTable=False):
    header = bytearray(HEADER_SZ)
    header[0:2] = b'BM'   # bmp signature
    byte_width = int((depth*width + 31) / 32) * 4
    if cTable:
        header[2:6] = ((byte_width * height) + (2**depth)*4 + HEADER_SZ).to_bytes(4, byteorder='little')  #file size
    else:
        header[2:6] = ((byte_width * height) + HEADER_SZ).to_bytes(4, byteorder='little')  #file size
    #header[6:10] = (0).to_bytes(4, byteorder='little')
    if cTable:
        header[10:14] = ((2**depth) * 4 + HEADER_SZ).to_bytes(4, byteorder='little') #offset
    else:
        header[10:14] = (HEADER_SZ).to_bytes(4, byteorder='little') #offset

    header[14:18] = (40).to_bytes(4, byteorder='little')    #file header size
    header[18:22] = width.to_bytes(4, byteorder='little') #width
    header[22:26] = (-height).to_bytes(4, byteorder='little', signed=True) #height
    header[26:28] = (1).to_bytes(2, byteorder='little') #no of planes
    header[28:30] = depth.to_bytes(2, byteorder='little') #depth
    #header[30:34] = (0).to_bytes(4, byteorder='little')
    header[34:38] = (byte_width * height).to_bytes(4, byteorder='little') #image size
    header[38:42] = (1).to_bytes(4, byteorder='little') #resolution
    header[42:46] = (1).to_bytes(4, byteorder='little')
    #header[46:50] = (0).to_bytes(4, byteorder='little')
    #header[50:54] = (0).to_bytes(4, byteorder='little')
    return header

def options():
    print("Options:")
    print("\tPress 1 to enter serial port settings")
    print("\tPress 2 to scan a fingerprint and save the image")
    print("\tPress 3 to view help")
    print("\tPress 4 to exit")
    print()
    choice = input(">> ")
    print()
    return choice

def getSettings():
    portSettings[0] = input("Enter Arduino serial port number: ")
    portSettings[1] = int(input('Enter serial port baud rate: '))
    print()
    
def getPrint():
    '''
    First enter the port settings with menu option 1:
    >>> Enter Arduino serial port number: COM13
    >>> Enter serial port baud rate: 57600

    Then enter the filename of the image with menu option 2: 
    >>> Enter filename/path of output file (without extension): myprints
    Found fingerprint sensor!
    .
    .
    .
    (Here you communicate with the Arduino and follow instructions)
    .
    .
    .
    Extracting image...saved as <filename>.bmp

    '''
    out = open(input("Enter filename/path of output file (without extension): ")+'.bmp', 'wb')
    # assemble and write the BMP header to the file
    out.write(assembleHeader(WIDTH, HEIGHT, DEPTH, True))
    for i in range(256):
        # write the colour palette
        out.write(i.to_bytes(1,byteorder='little') * 4)
    try:
        # open the port; timeout is 1 sec; also resets the arduino
        ser = serial.Serial(portSettings[0], portSettings[1], timeout=1)
    except Exception as e:
        print('Invalid port settings:', e)
        print()
        out.close()
        return
    while ser.isOpen():
        try:
            # assumes everything recved at first is printable ascii
            curr = ser.read().decode(encoding="utf8")
            # based on the image_to_pc sketch, \t indicates start of the stream
            if curr != '\t':
                # print the debug messages from arduino running the image_to_pc sketch
                print(curr, end='')
                continue
            for i in range(READ_LEN): # start recving image
                byte = ser.read()
                # if we get nothing after the 1 sec timeout period
                if not byte:
                    print("Timeout!")
                    out.close()  # close port and file
                    ser.close()
                    return False
                    
                # Since each received byte contains info for 2 adjacent pixels,
                # assume that both pixels were originally close enough in colour
                # to now be assigned the same colour
                out.write(byte * 2)
                
            out.close()  # close file
            print('Image saved as', out.name)
            
            # read anything that's left and print
            left = ser.read(100)
            print(left.decode('ascii', errors='ignore'))
            ser.close()
            
            print()
            return True
        except Exception as e:
            print("Read failed: ", e)
            out.close()
            ser.close()
            return False
        except KeyboardInterrupt:
            print("Closing port.")
            out.close()
            ser.close()
            return False

while True:
    chose = options()
    if chose == "4":
        break
    elif chose == '1':
        getSettings()
    elif chose == "2":
        res = getPrint()
        if not res:
            print("Image extraction failed!")
        continue
    elif chose == '3':
        print('================= HELP ==================')
        print(getPrint.__doc__)
        print('=========================================')
