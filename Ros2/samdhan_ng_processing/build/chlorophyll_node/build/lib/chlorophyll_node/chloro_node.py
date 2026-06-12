#!/usr/bin/env python3

import math
from pathlib import Path
from typing import Optional

import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node
from std_msgs.msg import String

from chlorophyll_node import image_processing


class ChlorophyllNode(Node):
    """Request plant images and publish their calculated chlorophyll index."""

    def __init__(self) -> None:
        super().__init__("chlorophyll_node")

        default_config_dir = (
            Path(get_package_share_directory("chlorophyll_node")) / "config"
        )
        default_output_dir = Path.home() / ".ros" / "chlorophyll_node"

        self.declare_parameter("distance_cutoff_cm", 20.0)
        self.declare_parameter("use_gnss_trigger", True)
        self.declare_parameter("config_directory", str(default_config_dir))
        self.declare_parameter("output_directory", str(default_output_dir))

        self.distance_cutoff_cm = (
            self.get_parameter("distance_cutoff_cm")
            .get_parameter_value()
            .double_value
        )
        self.use_gnss_trigger = (
            self.get_parameter("use_gnss_trigger")
            .get_parameter_value()
            .bool_value
        )
        self.config_directory = Path(
            self.get_parameter("config_directory")
            .get_parameter_value()
            .string_value
        ).expanduser()
        self.output_directory = Path(
            self.get_parameter("output_directory")
            .get_parameter_value()
            .string_value
        ).expanduser()
        self.output_directory.mkdir(parents=True, exist_ok=True)

        self.check_on_off = "chStop"
        self.previous_latitude: Optional[float] = None
        self.previous_longitude: Optional[float] = None

        self.ch_result_publisher = self.create_publisher(String, "chResult", 10)
        self.camera_request_publisher = self.create_publisher(
            String, "/sensor/camera/goPro", 10
        )

        self.start_stop_subscription = self.create_subscription(
            String, "chStartStop", self.callback_on_off, 10
        )
        self.image_subscription = self.create_subscription(
            String, "SentImageToChNode", self.callback_image_received, 10
        )
        self.gnss_subscription = None
        if self.use_gnss_trigger:
            self.gnss_subscription = self.create_subscription(
                String, "gnss", self.callback_lat_long_received, 10
            )

        self.get_logger().info(
            f"Chlorophyll node started; configuration: {self.config_directory}"
        )

    @staticmethod
    def calculate_distance_cm(
        previous_latitude: float,
        previous_longitude: float,
        latitude: float,
        longitude: float,
    ) -> float:
        earth_radius_m = 6_371_000.0
        latitude_delta = math.radians(latitude - previous_latitude)
        longitude_delta = math.radians(longitude - previous_longitude)
        haversine = (
            math.sin(latitude_delta / 2.0) ** 2
            + math.cos(math.radians(previous_latitude))
            * math.cos(math.radians(latitude))
            * math.sin(longitude_delta / 2.0) ** 2
        )
        central_angle = 2.0 * math.atan2(
            math.sqrt(haversine), math.sqrt(1.0 - haversine)
        )
        return earth_radius_m * central_angle * 100.0

    @staticmethod
    def publish_text(publisher, text: str) -> None:
        message = String()
        message.data = text
        publisher.publish(message)

    def request_camera_image(self) -> None:
        self.publish_text(self.camera_request_publisher, "RightCam,chNode")
        self.get_logger().info("Requested image from RightCam")

    def callback_on_off(self, message: String) -> None:
        self.check_on_off = message.data
        self.get_logger().info(f"Received state: {self.check_on_off}")
        if not self.use_gnss_trigger and self.check_on_off == "chStart":
            self.request_camera_image()

    def callback_lat_long_received(self, message: String) -> None:
        coordinates = message.data.split()
        if len(coordinates) != 2:
            self.get_logger().error(
                "Invalid GNSS message. Expected: '<latitude> <longitude>'"
            )
            return

        try:
            latitude, longitude = map(float, coordinates)
        except ValueError:
            self.get_logger().error(
                f"Invalid GNSS coordinates received: {message.data!r}"
            )
            return

        if self.previous_latitude is None or self.previous_longitude is None:
            self.previous_latitude = latitude
            self.previous_longitude = longitude
            if self.check_on_off == "chStart":
                self.request_camera_image()
            return

        distance_cm = self.calculate_distance_cm(
            self.previous_latitude,
            self.previous_longitude,
            latitude,
            longitude,
        )
        self.get_logger().info(f"Distance travelled: {distance_cm:.2f} cm")

        if distance_cm > self.distance_cutoff_cm:
            self.previous_latitude = latitude
            self.previous_longitude = longitude
            if self.check_on_off == "chStart":
                self.request_camera_image()

    def callback_image_received(self, message: String) -> None:
        image_path = message.data
        self.get_logger().info(f"Received image: {image_path}")

        try:
            result = image_processing.analysis(
                image_path,
                "ChlorophyllNode",
                self.config_directory,
                self.output_directory,
            )
        except Exception as error:
            self.get_logger().error(f"Image processing failed: {error}")
            result = "Image Processing Error Occurred"

        self.publish_text(self.ch_result_publisher, str(result))

        if self.check_on_off == "chStop":
            self.publish_text(self.ch_result_publisher, " ")

        if not self.use_gnss_trigger and self.check_on_off == "chStart":
            self.request_camera_image()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ChlorophyllNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.destroy_node()
        except KeyboardInterrupt:
            pass
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
