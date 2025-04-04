import requests

robot_name = "arri-122"

class GrafanaRunner:
    def __init__(self):
        self.robot_name = robot_name
        # self.grafana_url = f"https://dexory.grafana.net/d/11350/cnv?orgId=1&from=now-10m&to=now&timezone=Europe%2FLondon&var-robot={robot_name}"
        self.grafana_pdf_url = f"https://dexory.grafana.net/api/reports/render/pdfs?orientation=landscape&layout=grid&scaleFactor=100&dashboards=%5B%7B%22dashboard%22:%7B%22uid%22:%2211350%22%7D,%22reportVariables%22:%7B%22robot%22:%5B%22{self.robot_name}%22%5D%7D,%22timeRange%22:%7B%22from%22:%22now-10m%22,%22to%22:%22now%22%7D%7D%5D"
        self.api_key = "YOUR_API_KEY"  # Replace with your Grafana API key

    # def display_url(self):
    #     print(self.grafana_url)

    def export_dashboard_as_pdf(self):
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        response = requests.get(self.grafana_pdf_url, headers=headers)
        if response.status_code == 200:
            with open(f"{self.robot_name}_last_mission.pdf", "wb") as f:
                f.write(response.content)
            print(f"Dashboard exported as '{self.robot_name}_last_mission.pdf'")
        else:
            print(f"Failed to export dashboard as PDF: {response.status_code} - {response.text}")

gr = GrafanaRunner()
gr.export_dashboard_as_pdf()