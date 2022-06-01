import sys
import cv2

sys.path.insert(1, '../')

import os
sys.path.append(os.path.dirname(os.path.abspath("pykinect_azure")))
import pykinect_azure as pykinect

if __name__ == "__main__":

	# Initialize the library, if the library is not found, add the library path as argument
	pykinect.initialize_libraries(track_body=True)

	# Modify camera configuration
	device_config = pykinect.default_configuration
	device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
	device_config.depth_mode = pykinect.K4A_DEPTH_MODE_WFOV_2X2BINNED
	#print(device_config)

	# Start device
	device = pykinect.start_device(config=device_config)

	# Start body tracker
	bodyTracker = pykinect.start_body_tracker()

	cv2.namedWindow('Color image with skeleton',cv2.WINDOW_NORMAL)
	while True:
		
		# Get capture
		capture = device.update()

		# Get body tracker frame
		body_frame = bodyTracker.update()
		#print(bodyTracker.pop_result())

		try:
			print(body_frame.get_bodies()[0])
		except Exception as e:
			print(e)

		# Get the color image
		ret, color_image = capture.get_color_image()

		if not ret:
			continue

		# Draw the skeletons into the color image
		color_skeleton = body_frame.draw_bodies(color_image, pykinect.K4A_CALIBRATION_TYPE_COLOR)

		# Overlay body segmentation on depth image
		cv2.imshow('Color image with skeleton',color_skeleton)	

		# Press q key to stop
		if cv2.waitKey(1) == ord('q'):  
			break