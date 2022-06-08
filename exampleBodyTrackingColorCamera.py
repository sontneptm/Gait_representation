import sys
import cv2
import os
import time
import datetime as dt
from datetime import datetime

sys.path.insert(1, '../')
sys.path.append(os.path.dirname(os.path.abspath("pykinect_azure")))
import pykinect_azure as pykinect

if __name__ == "__main__":
	pykinect.initialize_libraries(track_body=True)

	# Modify camera configuration
	device_config = pykinect.default_configuration
	device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_720P
	device_config.depth_mode = pykinect.K4A_DEPTH_MODE_NFOV_2X2BINNED
	device_config.camera_fps = pykinect.K4A_FRAMES_PER_SECOND_30
	#print(device_config)

	# Start device
	device = pykinect.start_device(config=device_config)

	# Start body tracker
	bodyTracker = pykinect.start_body_tracker()

	cv2.namedWindow('Color image with skeleton',cv2.WINDOW_NORMAL)

	while True:
		cap_time = datetime.now()

		capture = device.update()
		body_frame = bodyTracker.update()

		ret, color_image = capture.get_color_image()

		if not ret:
			continue

		# Draw the skeletons into the color image
		color_skeleton = body_frame.draw_bodies(color_image, pykinect.K4A_CALIBRATION_TYPE_COLOR)

		cv2.imshow('Color image with skeleton',color_skeleton)	

		if cv2.waitKey(1) == ord('q'):  
			break