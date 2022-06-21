import sys
import os
import cv2
import csv
from datetime import datetime

sys.path.insert(1, '../')
sys.path.append(os.path.dirname(os.path.abspath("pykinect_azure")))
import pykinect_azure as pykinect

subject_name = "test"
file_name = "DATA" + subject_name +".csv"

names =[
    "pelvis",
    "spine - navel",
    "spine - chest",
    "neck",
    "left clavicle",
    "left shoulder",
    "left elbow",
    "left wrist",
    "right clavicle",
    "right shoulder",
    "right elbow",
    "right wrist",
    "left hip",
    "left knee",
    "left ankle",
    "left foot",
    "right hip",
    "right knee",
    "right ankle",
    "right foot"
]

class BodyTracker():
    def __init__(self) -> None:
        pykinect.initialize_libraries(track_body=True)
        self.file = open("./JOINT_DATA/joints.csv", "a")
        self.device, self.body_tracker = self.init_device()
        self.get_body_frame()

    def init_device(self):
        # NFOV 2X2 binned : exposure time : 12.8ms
        # NFOV 2X2 binned : working range : 0.5 ~ 5.46m 
        device_config = pykinect.default_configuration
        device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_720P
        device_config.depth_mode = pykinect.K4A_DEPTH_MODE_NFOV_2X2BINNED
        device_config.camera_fps = pykinect.K4A_FRAMES_PER_SECOND_30

        device = pykinect.start_device(config=device_config)
        bodyTracker = pykinect.start_body_tracker()

        return device, bodyTracker

    def get_ankle_position(self, data:str, name:str="pelvis"):
        start_index = data.find(name)
        position_index = start_index + data[start_index:].find("[")
        end_index = start_index + data[start_index:].find("orientation")
        position = data[position_index+1:end_index-3]

        return (name +","+ position)

    def get_body_frame(self):
        cv2.namedWindow('Depth image with skeleton',cv2.WINDOW_NORMAL)

        while True:
            try:
                cap_time = datetime.now()
                cap_time = cap_time.strftime("%H:%M:%S:%f")[:-3]

                capture = self.device.update()
                body_frame = self.body_tracker.update()

                ret, color_img = capture.get_color_image()

                if len(body_frame.get_bodies()) > 0:
                    target = body_frame.get_bodies()[0]
                    target_str = str(target)

                    joints = []

                    for name in names:
                        joints.append(self.get_ankle_position(data=target_str, name=name))
                    
                    write_str = ""
                    write_str += (cap_time + ",")

                    for joint in joints:
                        write_str += (joint+ ",")

                    write_str += "\n"

                    self.file.write(write_str)
                        

                combined_image = body_frame.draw_bodies(color_img, pykinect.K4A_CALIBRATION_TYPE_COLOR)

                try:
                    if ret:
                        cv2.imshow('Depth image with skeleton',combined_image)
                except Exception as e:
                    print(e)
                    pass

                # Press q key to stop
                if cv2.waitKey(1) == ord('q'):  
                    break
            except Exception as e:
                print(e)

if __name__ == "__main__":
    BodyTracker()