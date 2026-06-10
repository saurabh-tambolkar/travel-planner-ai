from dotenv import load_dotenv
load_dotenv()
import os
import requests

api_key = os.getenv("AVIATIONSTACK_API_KEY")


def search_flight(query: str) -> str:
    url = 'https://api.aviationstack.com/v1/flights'
    params = {
        'access_key': api_key,
        "limit": 5,
    }
    response = requests.get(url, params=params)
    data = response.json()
    

    flights = []

    if "data" in data:
        for flight in data["data"]:
            airline = flight.get("airline",{}).get("name", "N/A")
            departure_airport = flight.get("departure",{}).get("airport", "N/A")
            arrival_airport = flight.get("arrival",{}).get("airport", "N/A")
            status = flight.get("flight_status", "N/A")
            flights.append(f"Airline: {airline}, Departure: {departure_airport}, Arrival: {arrival_airport}, Status: {status}")
    return "\n".join(flights)