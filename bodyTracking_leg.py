import sys
import os
from unittest.mock import ANY
import cv2
from datetime import datetime
import math
import csv
import time

sys.path.insert(1, '../')
sys.path.append(os.path.dirname(os.path.abspath("pykinect_azure")))

import pykinect_azure as pykinect

subject_name = "test"
file_name = "C:/Users/MSDL/Desktop/azure_data/" + subject_name +".csv"

def data_split(body_list):
    x_start_index = body_list.find("[")
    x_end_index = body_list.find(",")
    x = body_list[x_start_index+1 : x_end_index]

    y_start_index = body_list.find(",")
    y_end_index = body_list.rfind(",")
    y = body_list[y_start_index+1 : y_end_index]
    
    return x, y

def angle_calculate(hx, hy, kx, ky, ax, ay):
    o1 = math.atan2((float(hy)-float(ky)), (float(hx)-float(kx)))
    o2 = math.atan2((float(ay)-float(ky)), (float(ax)-float(kx)))
    angle = abs((o1-o2)*180/math.pi)

    return angle

if __name__ == "__main__":

    # Initialize the library, if the library is not found, add the library path as argument
    pykinect.initialize_libraries(track_body=True)

    # Modify camera configuration
    device_config = pykinect.default_configuration
    device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_OFF
    device_config.depth_mode = pykinect.K4A_DEPTH_MODE_WFOV_2X2BINNED
    device_config.camera_fps = pykinect.K4A_FRAMES_PER_SECOND_30
    #print(device_config)

    # Start device
    device = pykinect.start_device(config=device_config)

    # Start body tracker
    bodyTracker = pykinect.start_body_tracker()

    cv2.namedWindow('Depth image with skeleton',cv2.WINDOW_NORMAL)

    f = open(file_name, 'w', newline='')

    while True:
        start_time = datetime.now()
        # Get capture
        capture = device.update()

        cap_time = time.time()

        # Get body tracker frame
        body_frame = bodyTracker.update()

        # Get the color depth image from the capture
        ret, depth_color_image = capture.get_colored_depth_image()

        # Get the colored body segmentation
        ret, body_image_color = body_frame.get_segmentation_image()

        for body in body_frame.get_bodies():
            body_str = str(body)
            body_list = body_str.split("\n")

            at_time =datetime.now()

            print("whole time:", at_time - start_time)
            #print("cap time:", at_time - cap_time)
            capture_time = datetime.now()
            # print(capture_time)

            for j in range(len(body_list)):
                joint_pos = body_list[j]                    #joint position name(ex.left hip Join info:)
                if "left hip" in joint_pos or "left knee" in joint_pos or "left ankle" in joint_pos:                  
                    joint_coordinate = body_list[j+1]       #joint coordinate (ex. position:[x, y, z])
                    # print(joint_pos + joint_coordinate)

                    if "hip" in joint_pos:
                        hx, hy = data_split(joint_coordinate)
                    elif "knee" in joint_pos:
                        kx, ky = data_split(joint_coordinate)
                    elif "ankle" in joint_pos:
                        ax, ay = data_split(joint_coordinate)

            angle = angle_calculate(hx, hy, kx, ky, ax, ay)
            # print(angle)
            if angle < 60:
                angle = -1
                
            #print("angle: ", angle)
            data = [capture_time, angle]
            writer = csv.writer(f)
            writer.writerow(data)

        if not ret:
            continue

        # Combine both images
        combined_image = cv2.addWeighted(depth_color_image, 0.6, body_image_color, 0.4, 0)

        # Draw the skeletons
        combined_image = body_frame.draw_bodies(combined_image)

        # Overlay body segmentation on depth image
        cv2.imshow('Depth image with skeleton',combined_image)
        
        #total_time =  time.time() - start_time
        #print("fps:", int(1./total_time))

        # Press q key to stop
        if cv2.waitKey(1) == ord('q'):  
            f.close()
            break
