import requests, sys, subprocess
import argparse
import questionary
import os
import json
from pathlib import Path
import time

# robot_name = "arri-115"

class MissionHandler():
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

        # print(self.mission_dict)
        return self.mission_dict

    def query_user(self):
        self.mission_select = questionary.select(
            "Select a mission to queue",
            choices=self.get_mission_dict(),
            qmark = ">>",
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

        print(self.mission_dict.get(self.key))
        self.queue_payload = {
            "mission_id": self.mission_dict.get(self.key)
        }
        self.queue_response = requests.post(self.deployments_endpoint, json=self.queue_payload)
        
        self.monitor_mission()

        return self.queue_response
    
    def monitor_mission(self):
        print("Waiting for mission to complete...")
        deployment_id = None  # Initialize deployment_id
        while True:
            response = requests.get(
                f"{self.base_url}/deployments"
            )
            # print(response.json()["items"][0])
            if response.status_code == 200:
                current_deployment = response.json()["items"][0]

                deployment_id = current_deployment.get("metadata")["uuid"] # Extract the "ID"
                if deployment_id is None:
                    print("Deployment ID not found in the response. Please check the mission status API.")
                else:
                    print(f"Current mission ID: {deployment_id}")

                if current_deployment.get("spec")["status"] == "complete":
                    print("Mission completed!")
                    break
            else:
                print(f"Failed to fetch mission status: {response.status_code}")
            time.sleep(5)

        self.download_images(deployment_id)
        return deployment_id

    def download_images(self, deployment_id):
        image_handler = ImageHandler(self, deployment_id)
        image_handler.download_mission_data()

class ImageHandler():
    """Class to handle mission images"""
    def __init__(self):
        self.robot_name = "arri-115"
        self.deployment_id = "2d684e3b-6d03-45c2-bfed-93983ead05f0"
        # self.robot_name = mission_handler.robot_name

        self.base_url = f"http://{self.robot_name}.velociraptor-tuna.ts.net/api/v1"
        # self.deployment_id = deployment_id
        print(f"Current dpeloyment: {self.deployment_id}")
        if self.deployment_id:
            self.deployment_path = f"{self.base_url}/deployments/{self.deployment_id}"
            print(self.deployment_path)
        else:
            raise ValueError("Deployment ID is None. Ensure the mission was queued successfully.")

        self.ENDPOINTS = [
            f"{self.deployment_path}/image",
            f"{self.deployment_path}/locations",
            f"{self.deployment_path}/markers",
            f"{self.deployment_path}/location-images",
        ]

        self.image_endpoint = f"{self.deployment_path}/image" #returns jpg
        self.locations_endpoint = f"{self.deployment_path}/locations" #returns str
        self.markers_endpoint = f"{self.deployment_path}/markers" #returns str
        self.location_images_endpoint = f"{self.deployment_path}/location-images"


        print(self.image_endpoint)
    def get_image_folder(self, path=None):
        if path is None:
            destination_path = Path(f"{self.robot_name}-final-mission-{self.deployment_id}")
            print(destination_path)
        else:
            destination_path = Path(path)

        destination_path.mkdir(parents=True, exist_ok=True)
        return destination_path
    
    def download_deployment_image(self):
        response = requests.get(self.image_endpoint)
        if response.status_code == 200:
            with open("image.jpg", 'wb') as f:
                f.write(response.content)
        
    def download_mission_data(self):
        pass
        # for endpoint in self.ENDPOINTS:
        #     response = requests.get(endpoint)
        #     if response.status_code == 200:
        #         data = response.json()
        #         filename = os.path.join(self.get_image_folder(), f"{endpoint.split('/')[-1]}.json")
        #         with open(filename, 'w') as f:
        #             json.dump(data, f)
        #         print(f"Data saved to {filename}")
        #     else:
        #         print(f"Failed to download data from {endpoint}: {response.status_code}")

    def save_to_folder(folder_path):
        # Ensure the folder exists
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Define the source file and destination
        source_file = __file__
        destination_file = os.path.join(folder_path, os.path.basename(source_file))

        # Copy the file to the folder
        
        print(f"File saved to {destination_file}")


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
    

class Plotjuggler():
    """Class to open and manipulate Plotjuggler"""

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
        ir.download_mission_data()
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