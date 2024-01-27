
import requests
import jwt
import time
import os
from github import GithubIntegration
from git import Repo
import pygit2
import subprocess
# Load environment variables
from dotenv import load_dotenv
load_dotenv()
if os.getenv('GITHUB_APP_ID'):
    app_id = int(os.getenv('GITHUB_APP_ID'))
else: 
    print(f"No GITHUB_APP_ID set github helper will not work.")
    
pem_path = "./github.pem"
if os.path.exists(pem_path):
    with open(pem_path, "r") as file:
        private_pem = file.read()
else:
    print(f"'{pem_path}' does not exist. github helper will not work.")
# Function to create a JWT
def create_jwt(app_id, private_pem):
    now = int(time.time())
    payload = {
        "iat": now,
        "exp": now + 60,  # Set expiration time to 1 minute
        "iss": app_id
    }
    return jwt.encode(payload, private_pem, algorithm="RS256")

# Function to get installations
def get_installations():

    

    jwt_token = create_jwt(app_id, private_pem)

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get("https://api.github.com/app/installations", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get installations: {response.content}")
        return None

# Function to get installation access token
def get_installation_access_token(installation_id, app_id, private_pem):
    integration = GithubIntegration(app_id, private_pem)
    return integration.get_access_token(installation_id)

# Function to get repositories
def get_repositories(installation_token):
    headers = {
        "Authorization": f"token {installation_token.token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get("https://api.github.com/installation/repositories", headers=headers)
    if response.status_code == 200:
        return response.json()['repositories']
    else:
        print(f"Failed to get repositories: {response.content}")
        return None



def clone_repo(repo_name, destination="./"):
    installations = get_installations()
    if installations:
        installation_id = installations[0]['id']
        installation_token = get_installation_access_token(installation_id, app_id, private_pem)
        repos = get_repositories(installation_token)
        if repos:
            for repo in repos:
                if repo['name'] == repo_name:
                    clone_url = repo["clone_url"]
                    clone_url = clone_url.replace('https://', f'https://x-access-token:{installation_token.token}@')

                    # Define the callback for pygit2
                    callbacks = pygit2.RemoteCallbacks(pygit2.UserPass(installation_token.token, ''))

                    # Clone directly into the destination directory
                    pygit2.clone_repository(clone_url, destination, callbacks=callbacks)
                    print(f"Cloned repository: {repo_name} into {destination}")
                    return
            print(f"Repository {repo_name} not found.")
        else:
            print("No repositories found.")
    else:
        print("No installations found.")
