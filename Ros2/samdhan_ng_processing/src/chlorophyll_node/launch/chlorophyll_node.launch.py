from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    distance_cutoff = LaunchConfiguration("distance_cutoff_cm")
    use_gnss_trigger = LaunchConfiguration("use_gnss_trigger")
    output_directory = LaunchConfiguration("output_directory")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "distance_cutoff_cm",
                default_value="20.0",
                description="Distance in centimetres before requesting an image.",
            ),
            DeclareLaunchArgument(
                "use_gnss_trigger",
                default_value="true",
                description="Use GNSS movement to trigger image capture.",
            ),
            DeclareLaunchArgument(
                "output_directory",
                default_value="~/.ros/chlorophyll_node",
                description="Directory for output images and RGB measurements.",
            ),
            Node(
                package="chlorophyll_node",
                executable="chlorophyll_node",
                name="chlorophyll_node",
                output="screen",
                parameters=[
                    {
                        "distance_cutoff_cm": distance_cutoff,
                        "use_gnss_trigger": use_gnss_trigger,
                        "output_directory": output_directory,
                    }
                ],
            ),
        ]
    )
