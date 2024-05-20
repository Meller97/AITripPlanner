import openai
import pandas as pd
from datetime import datetime
from serpapi.google_search import GoogleSearch
import re
import json
import os


# Load the CSV file
df = pd.read_csv('airports-code@public.csv', on_bad_lines='skip', delimiter=';')

serpapi_api_key = "4855a30cc64d8fac37a10cb9c506083dfc5c07d4b4e62f4af01158fe61336ac9"

def get_user_input():
    start_date = input("Enter the start date of your trip (YYYY-MM-DD):")
    end_date = input("Enter the end date of your trip (YYYY-MM-DD):")
    budget = float(input("Enter your total budget in USD:"))
    trip_type = input("Enter the type of trip (ski/beach/city):").lower()
    return start_date, end_date, budget, trip_type

def get_month_from_date(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%B")

# Function to find airport code by city name
def get_airport_code_by_city(city_name):
    result = df[df['City Name'].str.contains(city_name, case=False, na=False)]['Airport Code']
    if not result.empty:
        return result.values[0]
    else:
        return "City not found"

def get_promt(prompt):
    client = openai.OpenAI(
        api_key="sk-proj-31rvOvyTM13BSWMXnqMhT3BlbkFJ0fIRnpFuUIVvGLSVm6sH"
    )

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an experienced worldwide vacation planner. Additionally you are familiar with airports around the world."},
            {"role": "user", "content": prompt}
        ]
    )

def get_promt_fake(promt):
    return "Maldives, Male\nBora Bora, Tahiti\nSeychelles, Mahe\nPhuket, Phuket\nMaui, Maui"

    return completion.choices[0].message['content']

def get_possible_destinations(trip_type, month):
    prompt = (
    f"Suggest 5 possible travel destinations in the world for a {trip_type} trip in {month}, "
    "for each destination you have to return respond in the following structure "
    "(all the letters have to be English letters without any special characters):\n"
    "<possible travel destination>,<closest destination with airport>\n"
    "<possible travel destination>,<closest destination with airport>\n"
    "<possible travel destination>,<closest destination with airport>\n"
    "<possible travel destination>,<closest destination with airport>\n"
    "<possible travel destination>,<closest destination with airport>"
)
    response = get_promt_fake(prompt)
    
    # Split the response into lines and create a dictionary
    destinations_dict = {}
    for line in response.split('\n'):
        travel_destination, closest_airport = line.split(', ')
        destinations_dict[travel_destination] = get_airport_code_by_city(closest_airport)
    
    return destinations_dict

def search_flights(destination, start_date, end_date):
    params = {
  "engine": "google_flights",
  "departure_id": "TLV",
  "arrival_id": "AUS",
  "outbound_date": start_date,
  "return_date": end_date,
  "currency": "USD",
  "hl": "en",
  "api_key": "4855a30cc64d8fac37a10cb9c506083dfc5c07d4b4e62f4af01158fe61336ac9"
}

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        # Print the raw response for debugging
        #print("API Response:", results)

        return results
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_cheapest_flight(flights_data):
    best_flights = flights_data.get("best_flights", [])
    other_flights = flights_data.get("other_flights", [])
    
    all_flights = best_flights + other_flights
    
    if not all_flights:
        return None
    
    cheapest_flight = min(all_flights, key=lambda x: x["price"])
    
    return cheapest_flight

def print_ceapests_flight(flight):
    if not flight:
        print("No flight results found.")
        return
    print(f"Title: {flight['title']}")

def print_for_each_flight():
    start_date, end_date, budget, trip_type = get_user_input()
    month = get_month_from_date(start_date)
    destination_airport_dict = get_possible_destinations(trip_type, month)
    for dest in destination_airport_dict:
        if(destination_airport_dict[dest] != "City not found"):
            flight_data = search_flights(destination_airport_dict[dest],start_date, end_date)
            cheapest = get_cheapest_flight(flight_data)
            print(cheapest)
        else:
            print("not good")
    #for dest in destination_airport_dict:

if __name__ == "__main__":
    #result = print_for_each_flight()
    result = search_flights("d", "2024-07-21", "2024-07-27")
    # Ensure the file path is in the current directory
    current_directory = os.getcwd()
    file_path = os.path.join(current_directory, "flight_results.json")
        
    # Write the response data to the file
    with open(file_path, 'w') as file:
        json.dump(result, file, indent=4)
    #print(df.columns)