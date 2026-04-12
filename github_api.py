# github_api.py
import requests

def get_latest_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "version": data["tag_name"],
            "assets": data["assets"],
            "html_url": data["html_url"]
        }
    return None