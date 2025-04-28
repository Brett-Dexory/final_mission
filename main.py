import requests
import sys
import argparse
import questionary
from pathlib import Path
import time
import matplotlib as plt
import numpy as np

# robot_name = "arri-115"

# Define colors
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
MAGENTA = "\033[0;35m"
CYAN = "\033[0;36m"
NC = "\033[0m"  # No Color


class MissionHandler:
    def __init__(self, robot_name, aisle):
        self.robot_name = robot_name
        self.aisle = aisle

        self.base_url = f"http://{self.robot_name}.velociraptor-tuna.ts.net/api/v1"

        self.mission_endpoint = f"{self.base_url}/missions"
        self.autonomous_endpoint = f"{self.base_url}/config/autonomous-mode"
        self.deployments_endpoint = f"{self.base_url}/deployments"

        self.mission_names = []
        self.mission_ids = []

        self.mission_list = requests.get(self.mission_endpoint)

    def get_mission_dict(self):
        self.json_response = self.mission_list.json()["items"]
        for mission in self.json_response:
            self.mission_names.append(mission["spec"]["name"])
            self.mission_ids.append(mission["metadata"]["uuid"])

        self.mission_dict = dict(zip(self.mission_names, self.mission_ids))

        self.mission_dict = {
            name: mission_id
            for name, mission_id in self.mission_dict.items()
            if self.aisle in name
        }

        return self.mission_dict

    def query_user(self):
        self.mission_select = questionary.select(
            "Select a mission to queue",
            choices=self.get_mission_dict(),
            qmark=">>",
        ).ask()

        self.disable_autonomous()
        self.queue_mission()

        return self.mission_select

    def get_autonomous(self):
        response = requests.get(self.autonomous_endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def disable_autonomous(self):
        response = requests.put(self.autonomous_endpoint, json={"Autonomous": False})
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def queue_mission(self):
        self.key = self.mission_select

        self.queue_payload = {"mission_id": self.mission_dict.get(self.key)}
        self.queue_response = requests.post(
            self.deployments_endpoint, json=self.queue_payload
        )

        self.monitor_mission()

        return self.queue_response

    def monitor_mission(self):
        print(f"{CYAN}Waiting for mission to complete...{NC}")
        deployment_id = None  # Initialize deployment_id
        while True:
            response = requests.get(f"{self.base_url}/deployments")
            if response.status_code == 200:
                current_deployment = response.json()["items"][0]

                deployment_id = current_deployment.get("metadata")["uuid"]
                if deployment_id is None:
                    print(
                        f"{RED}Deployment ID not found in the response. "
                        f"Please check the mission status API.{NC}"
                    )
                else:
                    print(f"{CYAN}Current mission ID: {deployment_id}{CYAN}")

                if current_deployment.get("spec")["status"] == "complete":
                    print(f"{YELLOW}Mission completed!{NC}")
                    break
            else:
                print(
                    f"{RED}Failed to fetch mission status: {response.status_code}{NC}"
                )
            time.sleep(5)

        self.download_images(deployment_id)
        return deployment_id

    def download_images(self, deployment_id):
        image_handler = ImageHandler(self, deployment_id)
        image_handler.download_mission_data()


# LOOK AT DISABLING AUT0-UPLOAD

# class RecordBag():
#     def __init__(self, robot_name):
#         self.robot_name = robot_name
#         self.rosbags_list = [
#             "/tf",
#             "/tf_static",
#             "/roboteq_diff_driver/left_motor_amps",
#             "/roboteq_diff_driver/right_motor_amps"
#         ]

#         self.bag_path = f"/root/bags/{self.robot_name}-final_mission"

#     def record_rosbag(self, robot_name):
#         self.rosbags = (" ").join(self.rosbags_list)
#         print(self.rosbags)
#         proc = subprocess.run(
#         [
#             "ssh",
#             "-t",
#             f"root@{robot_name}.velociraptor-tuna.ts.net",
#             "balena exec -it $(balena ps -q -f name=ros) bash -ic",
#             f"'tmux new-session \'ros2 bag record {self.rosbags} -o {self.bag_path}\''",
#         ],
#         capture_output=True,
#         text=True,
#         )
#         print(proc)
#         return proc


class ImageHandler:
    """Class to handle mission images"""

    def __init__(self):
        self.robot_name = "arri-125"
        self.deployment_id = "a539dab3-11e0-4957-a8cf-0e9473f4e2a3"

        # self.robot_name = mission_handler.robot_name

        self.base_url = f"http://{self.robot_name}.velociraptor-tuna.ts.net/api/v1"
        # self.deployment_id = deployment_id

        if self.deployment_id:
            self.deployment_path = f"{self.base_url}/deployments/{self.deployment_id}"
        else:
            raise ValueError(
                f"{RED}Deployment ID is None. Ensure the mission was queued successfully.{NC}"
            )

        self.locations_endpoint = f"{self.deployment_path}/locations"  # returns str
        self.markers_endpoint = f"{self.deployment_path}/markers"  # returns str
        self.point_cloud_endpoints = f"{self.deployment_path}/pcd"  # returns x-pcd
        self.voxels_endpoints = f"{self.deployment_path}/voxels"  # returns str
        self.image_endpoint = f"{self.deployment_path}/image"  # returns jpg
        self.location_images_endpoint = (
            f"{self.deployment_path}/location_images"  # returns zip
        )

    def get_image_folder(self, path=None):
        if path is None:
            destination_path = Path(
                f"{self.robot_name}-final-mission-{self.deployment_id}"
            )
        else:
            destination_path = Path(path)

        destination_path.mkdir(parents=True, exist_ok=True)
        return destination_path

    def get_mission_pcd(self, destination_path):
        response = requests.get(self.point_cloud_endpoints)
        if response.status_code == 200:
            compressed_pcd_path = (
                destination_path / f"{self.robot_name}-deployment-pcd.x-pcd"
            )
            with open(compressed_pcd_path, "wb") as f:
                f.write(response.content)

    def download_mission_jsons(self, destination_path):
        response = requests.get(self.locations_endpoint)
        if response.status_code == 200:
            image_path = destination_path / f"{self.robot_name}-locations.json"
            with open(image_path, "wb") as f:
                f.write(response.content)

        response = requests.get(self.markers_endpoint)
        if response.status_code == 200:
            image_path = destination_path / f"{self.robot_name}-markers.json"
            with open(image_path, "wb") as f:
                f.write(response.content)

        response = requests.get(self.voxels_endpoints)
        if response.status_code == 200:
            image_path = destination_path / f"{self.robot_name}-voxels.json"
            with open(image_path, "wb") as f:
                f.write(response.content)
        return image_path

    def download_deployment_image(self, destination_path):
        response = requests.get(self.image_endpoint)
        if response.status_code == 200:
            image_path = destination_path / f"{self.robot_name}-deployment-image.jpg"
            with open(image_path, "wb") as f:
                f.write(response.content)
        return image_path

    def download_zip_file(self, destination_path):
        response = requests.get(self.location_images_endpoint)
        if response.status_code == 200:
            image_path = destination_path / f"{self.robot_name}-location-images.zip"
            with open(image_path, "wb") as f:
                f.write(response.content)
        return image_path

    def download_file_decorator(self, destination_path, image_path):
        print(f"{CYAN}======================={NC}")
        print(f"{YELLOW}Downloading files...{NC}")
        # self.download_deployment_image(destination_path)
        # self.download_zip_file(destination_path)
        # self.download_mission_jsons(destination_path)
        self.get_mission_pcd(destination_path)
        print(f"{CYAN}======================={NC}")
        print(f"{YELLOW}Files downloaded to: \n{image_path}{NC}")


def parse_args():
    """Parse arguments"""
    parser = argparse.ArgumentParser(
        description="This script will run a final mission."
    )

    parser.add_argument("robot_name", nargs="?", help="robot name")
    parser.add_argument("aisle", nargs="?", help="aisle name/number")
    return parser.parse_args()


def main():
    args = parse_args()
    # mission_Handler = MissionHandler(args.robot_name, args.aisle)
    # bag_recorder = RecordBag(args.robot_name)
    try:
        ir = ImageHandler()

        destination_path = ir.get_image_folder()
        image_path = destination_path / f"{ir.robot_name}-final-mission"

        ir.download_file_decorator(destination_path, image_path)

        # bag_recorder.record_rosbag(args.robot_name)

        # mission_Handler.query_user()
    except KeyboardInterrupt:
        questionary.print(" - Interrupted by user!", style="bold fg:ansired")
        sys.exit()
    # except requests.exceptions.RequestException as e:
    #     questionary.print(f" - Error: {e}", style="bold fg:ansired")
    #     sys.exit()
    # except Exception as e:
    #     questionary.print(f" - Unexpected error: {e}", style="bold fg:ansired")
    #     sys.exit()


if __name__ == "__main__":
    main()
