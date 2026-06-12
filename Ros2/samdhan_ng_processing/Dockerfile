FROM ros:humble-ros-base

SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble
ENV ROS_DOMAIN_ID=0
ENV ROS_LOCALHOST_ONLY=0
ENV RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ENV FASTDDS_BUILTIN_TRANSPORTS=UDPv4

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3-colcon-common-extensions \
        python3-numpy \
        python3-opencv \
        ros-humble-rmw-fastrtps-cpp \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ros2_ws

COPY src/chlorophyll_node/ src/chlorophyll_node/

RUN source /opt/ros/humble/setup.bash \
    && colcon build \
        --packages-select chlorophyll_node \
        --merge-install \
        --cmake-args -DCMAKE_BUILD_TYPE=Release

RUN mkdir -p /data/input /data/output

COPY docker/ros_entrypoint.sh /ros_entrypoint.sh
RUN chmod +x /ros_entrypoint.sh

VOLUME ["/data/input", "/data/output"]

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["ros2", "launch", "chlorophyll_node", "chlorophyll_node.launch.py", "output_directory:=/data/output"]
