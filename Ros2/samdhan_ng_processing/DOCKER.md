# Chlorophyll Node Docker Usage

The container uses ROS 2 Humble, Python 3.10, OpenCV, NumPy, and Fast DDS.
Host networking is used so ROS 2 multicast discovery and DDS topic traffic can
pass between the container, the host, and other machines on the same network.

## Build and start

```bash
cd /path/to/samdhan_ng_processing
docker compose build
docker compose up
```

Without Docker Compose:

```bash
docker build -t chlorophyll-node:humble .

docker run --rm \
  --name chlorophyll-node \
  --network host \
  --ipc host \
  -e ROS_DOMAIN_ID=0 \
  -e ROS_LOCALHOST_ONLY=0 \
  -v "$(pwd)/docker-data/input:/data/input:ro" \
  -v "$(pwd)/docker-data/output:/data/output" \
  chlorophyll-node:humble
```

Run in the background:

```bash
docker compose up -d
docker compose logs -f
```

Stop the node:

```bash
docker compose down
```

## ROS domain

Every ROS 2 participant must use the same domain ID. The default is `0`.

```bash
cp .env.example .env
```

Change `ROS_DOMAIN_ID` in `.env` if required. On an external ROS 2 machine:

```bash
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0
source /opt/ros/humble/setup.bash
```

The host, container, and external machines must all use the same value.

## Test from the host or another ROS 2 machine

Monitor outputs:

```bash
ros2 topic echo /sensor/camera/goPro
ros2 topic echo /chResult
```

Start processing:

```bash
ros2 topic pub --once /chStartStop std_msgs/msg/String "{data: 'chStart'}"
```

Send GNSS data:

```bash
ros2 topic pub --once /gnss std_msgs/msg/String \
  "{data: '22.572600 88.363900'}"
```

## Send an image

Place the image in the host directory:

```text
docker-data/input/plant.jpg
```

Publish its path as seen inside the container:

```bash
ros2 topic pub --once /SentImageToChNode std_msgs/msg/String \
  "{data: '/data/input/plant.jpg'}"
```

Generated files are available on the host under:

```text
docker-data/output/
```

An image path published to the node must exist inside the container. Add
another bind mount in `compose.yaml` when images are stored elsewhere. You can
also set `IMAGE_INPUT_DIR` in `.env` to the host directory written by the
camera process. It is always mounted inside the container as `/data/input`.

## Run ROS commands inside the container

```bash
docker compose exec chlorophyll-node ros2 node info /chlorophyll_node
docker compose exec chlorophyll-node ros2 topic list
```

## Networking notes

- Linux: `network_mode: host` provides the most reliable ROS 2 DDS behavior.
- Docker Desktop: enable host networking in Docker Desktop settings when the
  platform supports it.
- The image supports CPU architectures offered by the upstream
  `ros:humble-ros-base` image; build it on the target architecture or use
  Docker Buildx.
- Host firewalls must permit DDS UDP multicast and traffic between ROS hosts.
- All machines must use compatible ROS 2 middleware and the same domain ID.
- Machines on routed networks without multicast require a DDS discovery-server
  or VPN configuration; ordinary Docker `ports` mappings are not sufficient.
