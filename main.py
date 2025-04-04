import requests, sys, subprocess
import argparse
import questionary

# robot_name = "arri-122"

class MissionHandler():
    def __init__(self, robot_name, aisle):
        self.robot_name = robot_name
        self.aisle = aisle

        self.mission_url = f"http://{self.robot_name}.velociraptor-tuna.ts.net/api/v1/missions"
        self.mission_names = []
        self.mission_ids = []
        
        self.mission_list = requests.get(self.mission_url)

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

        print(self.mission_dict)
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
    
    def disable_autonomous(self):
        self.auto_url = f"http://{self.robot_name}.velociraptor-tuna.ts.net/config/autonomous-mode"
        self.auto_payload = {
            "Autonomous": "false",
        }
        print(self.auto_payload)
        print(self.auto_url)
        self.auto_response = requests.put(self.auto_url, json=self.auto_payload)

        return self.auto_response

    def queue_mission(self):
        self.key = self.mission_select

        self.queue_url = f"http://{self.robot_name}.velociraptor-tuna.ts.net/api/v1/deployments"
        print(self.mission_dict.get(self.key))
        self.queue_payload = {
            "mission_id": self.mission_dict.get(self.key)
        }
        self.queue_response = requests.post(self.queue_url, json=self.queue_payload)
        
        return self.queue_response
    
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
    
class Listener():
    """Class to listen in to RM to get robot status - maybe"""
    def __init__(self):
        pass

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
    mission_Handler = MissionHandler(args.robot_name, args.aisle)
    # bag_recorder = RecordBag(args.robot_name)
    try:
        # bag_recorder.record_rosbag(args.robot_name)
        mission_Handler.query_user()
    except KeyboardInterrupt:
        questionary.print(" - Interrupted by user!", style="bold fg:ansired")
        sys.exit()
    except requests.exceptions.RequestException as e:
        questionary.print(f" - Error: {e}", style="bold fg:ansired")
        sys.exit()
    except Exception as e:
        questionary.print(f" - Unexpected error: {e}", style="bold fg:ansired")
        sys.exit()
if __name__ == "__main__":
    main()