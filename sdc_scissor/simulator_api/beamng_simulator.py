import logging
import math
import time

import numpy as np
from scipy.spatial.transform import Rotation
from beamngpy import BeamNGpy, Scenario, Road, Vehicle
from beamngpy.sensors import Electrics
from shapely.geometry import LineString

from sdc_scissor.simulator_api.abstract_simulator import AbstractSimulator
from sdc_scissor.testing_api.test import Test


def _compute_start_position(road_nodes):
    """
    Compute start position of the car. The car should be on the right lane in the beginning of the road.

    :param road_nodes: Road nodes specifying the road for a BeamNG scenario
    :return: The coordinates of the start position of the car as well the euler angle around the z-axis.
    """
    logging.debug("compute_start_position")
    first_road_point = road_nodes[0]

    center_line = LineString(coordinates=[(x[0], x[1]) for x in road_nodes])
    optimal_trajectory = center_line.parallel_offset(distance=2.5)
    start_point = optimal_trajectory.interpolate(distance=-2.5)
    start_position = (start_point.x, start_point.y, first_road_point[2])

    one_meter_from_start_point = optimal_trajectory.interpolate(distance=-3.5)

    dir_vec = -np.array([one_meter_from_start_point.x - start_point.x, one_meter_from_start_point.y - start_point.y])
    norm_dir_vec = dir_vec / np.linalg.norm(dir_vec)

    base_vec = np.array([0, 1])
    norm_base_vec = np.array(base_vec) / np.linalg.norm(base_vec)

    angle = math.acos(np.inner(norm_base_vec, norm_dir_vec))
    y_component = norm_dir_vec[1]
    if y_component > 0:
        alpha = angle
    elif y_component < 0:
        alpha = 2 * np.pi - angle
    elif y_component == 0:
        alpha = np.pi
    else:
        raise Exception("y_component could not be assessed!")

    return start_position, alpha


class BeamNGSimulator(AbstractSimulator):
    """
    This class implements the interface for the specific BeamNG.tech simulator.
    """

    def __init__(self, beamng: BeamNGpy, rf: float, max_speed: float, fov: int):
        """
        API for enabling inter-process communication with the BeamNG simulator.

        :param host: Hostname of the machine, e.g., 'localhost'
        :param port: The port for communication with the BeamNG process
        :param home: Path to BeamNG installation
        :param user: The user path (path to your license key file)
        :param rf: The risk factor, e.g., 1.5
        :param max_speed: The maximal speed allowed for a vehicle in km/h
        :param fov: The field of view  for a Camera e.g., 120
        """
        super().__init__()
        self.beamng = beamng
        self.home = beamng.home
        self.user = beamng.user
        self.port = beamng.port
        self.host = beamng.host
        self.vehicle = None
        self.car_state = None
        self.scenario = None
        self.rf = rf
        self.max_speed = max_speed
        self.fov = fov

    def open(self):
        """
        Start the BeamNG.tech process
        """
        self.beamng.open()

    def close(self):
        """
        Quit the BeamNG.tech process
        """
        self.beamng.close()

    def create_new_instance(self):
        """
        Restart the BeamNG.tech process
        """
        logging.info("restart simulator")
        try:
            self.beamng.close()
        finally:
            logging.info("creating a new BeamNGpy instance")
            time.sleep(5)
            self.beamng = BeamNGpy(self.host, self.port, home=self.home, user=self.user)

    def stop_scenario(self):
        """ """
        logging.info("stop_scenario")
        self.beamng.stop_scenario()

    def start_scenario(self):
        """ """
        logging.info("start_scenario")
        self.beamng.start_scenario()
        self.vehicle.ai_set_mode("span")
        self.vehicle.ai_drive_in_lane(lane=True)
        self.vehicle.ai_set_aggression(self.rf)
        self.vehicle.set_color(rgba=(0, 0, 1, 0.5))
        self.vehicle.ai_set_speed(self.__kmh_to_ms(self.max_speed))
        self.vehicle.ai_set_waypoint("end_point")

    @staticmethod
    def __kmh_to_ms(kmh):
        """

        :param kmh:
        :return:
        """
        return kmh / 3.6

    def load_scenario(self, test: Test, scenario: Scenario, obstacles: list):
        """

        :param test:
        :param scenario:
        :param obstacles:
        """
        logging.info("load_scenario")
        self.scenario = scenario
        road = Road(material="tig_road_rubber_sticky", rid="flat_road", interpolate=True)

        # Ensure not overriding the test object (copy first the whole list)
        road_nodes = test.road_points.copy()
        for road_node in road_nodes:
            road_node.extend([-28, 10])

        road.nodes.extend(road_nodes)

        self.scenario.add_road(road)

        logging.info("* generate obstacle points")
        for obstacle in obstacles:
            if obstacle.obstacle_type == "static":
                self.scenario.add_object(obstacle.get())
            elif obstacle.obstacle_type == "procedural":
                self.scenario.add_procedural_mesh(obstacle.get())

        self.vehicle = Vehicle(vid="ego_vehicle", model="etk800", licence="Scissor")
        electrics = Electrics()
        self.vehicle.attach_sensor("electrics", electrics)

        start_position, alpha = _compute_start_position(road_nodes)
        logging.info("start: {}".format(start_position))
        self.scenario.add_vehicle(
            vehicle=self.vehicle,
            pos=start_position,
            rot_quat=Rotation.from_euler("zyx", [alpha, 0, 0], degrees=False).as_quat(),
        )

        end_point = road_nodes[-1][:3]

        self.scenario.add_checkpoints(positions=[end_point], scales=[(5, 5, 5)], ids=["end_point"])
        self.scenario.make(self.beamng)
        self.beamng.load_scenario(self.scenario)

    def update_car(self):
        """ """
        logging.info("update_car")
        self.vehicle.update_vehicle()
        _ = self.beamng.poll_sensors(self.vehicle)  # otherwise, the values are not updated (bug of beamngpy)
        self.car_state = self.vehicle.state

    def get_car_position(self):
        """
        Compute the car's position

        :return: x,y,z coordinates of the car
        """
        logging.info("get_car_position")
        x_pos = self.car_state["pos"][0]
        y_pos = self.car_state["pos"][1]
        z_pos = self.car_state["pos"][2]
        return x_pos, y_pos, z_pos
