import logging; logger = logging.getLogger("morse." + __name__)
from morse.core import blenderapi

import morse.sensors.camera

from morse.helpers import passive_objects
from morse.helpers.components import add_data, add_property
from morse.helpers.transformation import Transformation3d
from morse.core.mathutils import Vector

class SemanticCamera(morse.sensors.camera.Camera):
    """
    This sensor emulates a high level *abstract* camera that outputs the
    name and 6D pose of visible objects (*i.e.* objects in the field of
    view of the camera). It also outputs the *type* of the object if the ``Type``
    property is set (:python:`my_object.properties(Type="Bottle")` for
    instance).

    General usage
    -------------

    You need to *tag* the objects you want your camera to track by either
    adding a boolean property ``Object`` to your object:
    :python:`my_object.properties(Object=True)`, or by setting a *type* and
    using this type as the value of the ``tag`` property of the camera:

    .. code-block:: python

        object_to_track = PassiveObject(...)
        object_to_track.properties(Type="Bottle")

        ...

        semcam = SemanticCamera()
        semcam.properties(tag="Bottle")

        ...

    See the *Examples* section below for a complete working example.

    If the ``Label`` property is defined, it is used as exported
    name. Otherwise, the Blender object name is used.

    By default, the pose of the objects is provided in the **world** frame.
    When setting the ``relative`` property to ``True``
    (:python:`semcam.properties(relative=True)`), the pose is computed in the
    **camera** frame instead.

    Details of implementation
    -------------------------

    A test is made to identify which of these objects are inside of
    the view frustum of the camera. Finally, a single visibility test is
    performed by casting a ray from the center of the camera to the
    center of the object. If anything other than the test object is
    found first by the ray, the object is considered to be occluded by
    something else, even if it is only the center that is being blocked.
    This occulsion check can be deactivated (for slightly improved
    performances) by setting the sensor property ``noocclusion`` to ``True``.

    See also :doc:`../sensors/camera` for generic informations about MORSE cameras.

   .. note::

        As any other MORSE camera, the semantic camera *only* works if the
        rendering mode is set to `GLSL` (default). In particular, it does 
        not work in `fastmode` (ie, wireframe mode).

    .. example::
        from morse.builder import *

        # add a 'passive' object visible to the semantic cameras
        table = PassiveObject('props/objects','SmallTable')
        table.translate(x=3.5, y=-3, z=0)
        table.rotate(z=0.2)

        # by setting the 'Object' property to true, this object becomes
        # visible to the semantic cameras present in the simulation.
        # Note that you can set this property on any object (other robots, humans,...).
        table.properties(Type = "table", Label = "MY_FAVORITE_TABLE")

        # then, create a robot
        robot = Morsy()

        # creates a new instance of the sensor, that tracks all tables.
        # If you do not specify a particular 'tag', the camera tracks by default
        # all object with the properties 'type="Object"' or 'Object=True'.
        semcam = SemanticCamera()
        semcam.properties(tag = "table")

        # place the camera at the correct location
        semcam.translate(<x>, <y>, <z>)
        semcam.rotate(<rx>, <ry>, <rz>)

        robot.append(semcam)

        # define one or several communication interface, like 'socket'
        semcam.add_interface(<interface>)

        env = Environment('empty')

    :noautoexample:
    """

    _name = "Semantic camera"
    _short_desc = "A smart camera allowing to retrieve objects in its \
    field of view"

    add_data('visible_objects', [], 'list<objects>',
           "A list containing the different objects visible by the camera. \
            Each object is represented by a dictionary composed of: \n\
                - **name** (String): the name of the object \n\
                - **type** (String): the type of the object \n\
                - **position** (vec3<float>): the position of the \
                  object, in meter, in the blender frame       \n\
                - **orientation** (quaternion): the orientation of the \
                  object, in the blender frame")

    add_property('relative', False, 'relative', 'bool', 'Return object position'
                 ' relatively to the sensor frame.')
    add_property('noocclusion', False, 'noocclusion', 'bool', 'Do not check for'
                 ' objects possibly hiding each others (faster but less '
                 'realistic behaviour)')
    add_property('tag', 'Object',  'tag',  "string",  "The type of "
            "detected objects. This type is looked for as a game property of scene "
            "objects or as their 'Type' property. You must then add fix this "
            "property to the objects you want to be detected by the semantic "
            "camera.")

    def __init__(self, obj, parent=None):
        """ Constructor method.

        Receives the reference to the Blender object.
        The second parameter should be the name of the object's parent.
        """
        logger.info('%s initialization' % obj.name)
        # Call the constructor of the parent class
        morse.sensors.camera.Camera.__init__(self, obj, parent)

        # Locate the Blender camera object associated with this sensor
        main_obj = self.bge_object
        for obj in main_obj.children:
            if hasattr(obj, 'lens'):
                self.blender_cam = obj
                logger.info("Camera object: {0}".format(self.blender_cam))
                break
        if not self.blender_cam:
            logger.error("no camera object associated to the semantic camera. \
                         The semantic camera requires a standard Blender  \
                         camera in its children.")

        # TrackedObject is a dictionary containing the list of tracked objects
        # (->meshes with a class property set up) as keys
        #  and the bounding boxes of these objects as value.
        self.trackedObjects = {}
        for o in blenderapi.scene().objects:
            tagged = ('Type' in o and o['Type'] == self.tag) or (self.tag in o and bool(o[self.tag]))
                               
            if tagged:
                self.trackedObjects[o] = blenderapi.objectdata(o.name).bound_box
                logger.warning('    - tracking %s' % o.name)

        if self.noocclusion:
            logger.info("Semantic camera running in 'no occlusion' mode (fast mode).")
        logger.info("Component initialized, runs at %.2f Hz ", self.frequency)


    def default_action(self):
        """ Do the actual semantic 'grab'.

        Iterate over all the tracked objects, and check if they are
        visible for the robot.  Visible objects must have a bounding box
        and be active for physical simulation (have the 'Actor' checkbox
        selected)
        """
        # Call the action of the parent class
        morse.sensors.camera.Camera.default_action(self)

        # Create dictionaries
        self.local_data['visible_objects'] = []
        self.local_data['disturbing_bboxes'] = []
        for obj, bb in self.trackedObjects.items():
            if self._check_distance(obj) and self._check_visible(obj, bb):
                occlusion = 'not given'#self._check_occlusion(obj)
                # Create dictionary to contain object name, type,
                # description, position, orientation and bounding box
                pos = obj.position
                bbox = [[bb_corner[i] + pos[i] for i in range(3)] for bb_corner in bb]
                if self.relative:
                    t3d = Transformation3d(obj)
                    logger.debug("t3d(obj) = {t}".format(t=t3d))
                    logger.debug("t3d(cam) = {t}".format(t=self.position_3d))
                    transformation = self.position_3d.transformation3d_with(t3d)
                    logger.debug("transform = {t}".format(t=transformation))
                else:
                    transformation = Transformation3d(obj)
                obj_dict = {'name': obj.get('Label', obj.name),
                            'description': obj.get('Description', ''),
                            'type': obj.get('Type', ''),
                            'position': transformation.translation,
                            'orientation': transformation.rotation,
                            'yaw': transformation.yaw,
                            'bbox': bbox,
                            'occlusion': occlusion}
                self.local_data['visible_objects'].append(obj_dict)
            if self._check_visible(obj, bb, False):
                pos = obj.position
                bbox = [[bb_corner[i] + pos[i] for i in range(3)] for bb_corner in bb]
                disturbing_bbox = {'bbox': bbox}
                self.local_data['disturbing_bboxes'].append(disturbing_bbox)
                
        logger.debug("Visible objects: %s" % self.local_data['visible_objects'])

    def _get_edge(self, obj):
        pos = obj.position
        print('object: {}, position: {}'.format(obj, pos))
        pos = self.blender_cam.world_to_camera * pos
        x_values = []
        y_values = []
        positions = []
        for mesh in obj.meshes:
            for material in mesh.materials:
                for i in range(mesh.getVertexArrayLength(material.material_index)):
                    proxy = mesh.getVertex(material.material_index, i)
                    vertex = self.blender_cam.world_to_camera * proxy.XYZ
                    x_values.append(int(vertex.x * 1000))
                    y_values.append(int(vertex.y * 1000))
                    positions.append(vertex)
        x_min = min(x_values)
        x_max = max(x_values)
        y_min = min(y_values)
        y_max = max(y_values)

        x_max_list = []
        x_min_list = []
        y_min_list = []
        y_max_list = []
        results = []
        for position in positions:
            position.x = int(position.x * 1000)
            position.y = int(position.y * 1000)
            if position.x == x_min:
                x_min_list.append(position.y)
            if position.x == x_max:
                x_max_list.append(position.y)
            if position.y == y_min:
                y_min_list.append(position.x)
            if position.y == y_max:
                y_max_list.append(position.x)
        results.append(Vector([float(x_min/1000), float(min(x_min_list)/1000), pos.z]))
        results.append(Vector([float(x_min/1000), float(max(x_min_list)/1000), pos.z]))
        results.append(Vector([float(x_max/1000), float(min(x_max_list)/1000), pos.z]))
        results.append(Vector([float(x_max/1000), float(max(x_max_list)/1000), pos.z]))
        results.append(Vector([float(y_min/1000), float(min(y_min_list)/1000), pos.z]))
        results.append(Vector([float(y_min/1000), float(max(y_min_list)/1000), pos.z]))
        results.append(Vector([float(y_max/1000), float(min(y_max_list)/1000), pos.z]))
        results.append(Vector([float(y_max/1000), float(max(y_max_list)/1000), pos.z]))
        results.append(pos)
        final_results = []
        #print('results in cmera coord: {}'.format(results))
        for position in results:
            new_position = self.blender_cam.camera_to_world * position
            final_results.append(new_position)
        #print('final_results in world coord: {}'.format(final_results))
        return final_results

    def _check_occlusion(self, obj):
        """Check how much occluded an object is"""
        points = self._get_edge(obj)
        #print(points)
        pos = obj.position
        points.append(pos)
        noocclusion_count = 0
        point_count = 0
        for point in points:
            closest_obj = self.bge_object.rayCastTo(point)
            point_count += 1
            if closest_obj is None or closest_obj in [obj] + list(obj.children):
                noocclusion_count += 1
        return 1-(noocclusion_count / point_count)

    def _check_distance(self, obj):
        """ Check if an object is to far away from camera"""
        dist = self.bge_object.getDistanceTo(obj)
        return dist < 4

    def _check_visible(self, obj, bb, inside_frustum=True):
        """ Check if an object lies inside of the camera frustum. 
        
        The behaviour of this method is impacted by the sensor's 
        property 'noocclusion': if true, only checks the object is in the
        frustum. Does not check it is actually visible (ie, not hidden
        away by another object).
        """
        # TrackedObjects was filled at initialization
        #  with the object's bounding boxes
        pos = obj.position
        bbox = [[bb_corner[i] + pos[i] for i in range(3)] for bb_corner in bb]

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("\n--- NEW TEST ---")
            logger.debug("OBJECT '{0}' AT {1}".format(obj, pos))
            logger.debug("CAMERA '{0}' AT {1}".format(
                                    self.blender_cam, self.blender_cam.position))
            logger.debug("BBOX: >{0}<".format(bbox))
            logger.debug("BBOX: {0}".format(bb))

        # Translate the bounding box to the current object position
        #  and check if it is in the frustum
        box_inside_frustum = self.blender_cam.boxInsideFrustum(bbox)
        if not inside_frustum:
            return box_inside_frustum != self.blender_cam.OUTSIDE
            # closest_obj = self.bge_object.rayCastTo(obj)
            # if closest_obj in [obj] + list(obj.children):
            #     return box_inside_frustum != self.blender_cam.OUTSIDE
        if box_inside_frustum == self.blender_cam.INSIDE:

            if not self.noocclusion:
                # Check that there are no other objects between the camera
                # and the selected object
                # NOTE: This is a very simple test. Hiding only the 'center'
                # of an object will make it invisible, even if the rest is
                # still seen from the camera
                closest_obj = self.bge_object.rayCastTo(obj)
                if closest_obj in [obj] + list(obj.children):
                    return True
            else:
                return True

            #return True

        return False
