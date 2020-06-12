Simulation has to be created (morse create ...)
    property "Type" = "Object" has to be added to objects to be recognized by the semantic_camera
    adjust default.py
    default.py has to contain:

        # Add robot etc.

        video_camera = VideoCamera()
        video_camera.translate(0.0, 0.0, 1.7)
        video_camera.properties(cam_width=800, cam_height=800)
        semantic_camera = SemanticCamera()
        semantic_camera.properties(tag="Object")
        semantic_camera.translate(0.0, 0.0, 1.7)

        robot.append(video_camera)
        robot.append(semantic_camera)

        video_camera.add_service('socket')
        semantic_camera.add_service('socket')

        motion = Teleport()
        robot.append(motion)
        motion.add_service('socket')

        robot.add_default_interface('socket')

        # Add environment etc.

Simulation has to be started (morse run ...)
change view to robot camera (use F9)

change bboxes/simulationData/images/positions.csv as you need
    position csv contains: x_pos, y_pos, yaw

run try.py
try.py will save the bbox images and meta_data.csv in bboxes/simulationData/images/*currentDateAndTime*

images are named by index_objectName.png
meta_data.csv contains: index, pathToImage, objectCategory, objectName