from dotenv import load_dotenv
import os
import requests

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
API_USERNAME = os.getenv("API_USERNAME")
API_PASSWORD = os.getenv("API_PASSWORD")

TOKEN_URL = f"{API_BASE_URL}/token"
SERVICES_URL = f"{API_BASE_URL}/servicios-clinica"


def get_token():
    response = requests.post(
        TOKEN_URL,
        data={"username": API_USERNAME, "password": API_PASSWORD}
    )

    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Error fetching token: {response.status_code} - {response.text}")


def get_services(token):
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(SERVICES_URL, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Cannot get services: {response.status_code} - {response.text}")

