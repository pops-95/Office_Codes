#!/usr/bin/env python3

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

import serial


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Store connector Arduino accelerometer data in a CSV file."
    )
    parser.add_argument(
        "--port",
        default="/dev/ttyACM1",
        help="USB serial port used by the connector Arduino.",
    )
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("accelerometer_data.csv"),
    )
    return parser.parse_args()


def parse_sample(line):
    if not line or line.startswith("#"):
        return None

    fields = line.split(",")
    if len(fields) != 3:
        return None

    try:
        return tuple(float(field) for field in fields)
    except ValueError:
        return None


def parse_status(line):
    prefix = "#STATUS,"
    if not line.startswith(prefix):
        return None

    status = line[len(prefix) :]
    if status in {"connected", "disconnected"}:
        return status
    return None


def main():
    args = parse_arguments()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Reading {args.port} at {args.baud} baud")
    print(f"Overwriting {args.output}")

    with serial.Serial(args.port, args.baud, timeout=1) as connection:
        with args.output.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.writer(output_file)
            writer.writerow(
                ("timestamp_utc", "connection_status", "x_g", "y_g", "z_g")
            )
            output_file.flush()
            connection_status = "disconnected"

            while True:
                line = connection.readline().decode("utf-8", errors="ignore").strip()
                timestamp = datetime.now(timezone.utc).isoformat()
                status = parse_status(line)

                if status is not None:
                    connection_status = status
                    writer.writerow((timestamp, connection_status, "", "", ""))
                    output_file.flush()
                    print(f"{timestamp},{connection_status}")
                    continue

                sample = parse_sample(line)
                if sample is None:
                    if line:
                        print(line)
                    continue

                writer.writerow((timestamp, connection_status, *sample))
                output_file.flush()
                print(
                    f"{timestamp},{connection_status},"
                    f"{sample[0]},{sample[1]},{sample[2]}"
                )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped")
