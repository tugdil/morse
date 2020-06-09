import sys
import math
import numpy as np
from pymorse import Morse

with Morse() as morse:
    semantic_camera = morse.robot.semantic_camera
    semantic_camera_data = semantic_camera.get()
    print(semantic_camera_data)
    video_camera = morse.robot.video_camera
    video_camera_data = video_camera.get()
    print(video_camera_data)
    view_projection = video_camera_data['view_projection_matrix']
    view_projection_matrix = np.array([np.array(x) for x in view_projection])


    for visible_object in semantic_camera_data['visible_objects']:
        bbox = visible_object['bbox']
        for corner in bbox:
            

