import openai
import pandas as pd
from datetime import datetime
from serpapi.google_search import GoogleSearch
import re
import json
import os


# Load the CSV file
df = pd.read_csv('airports-code@public.csv', on_bad_lines='skip', delimiter=';',usecols=["Airport Code", "Airport Name", "City Name"])

serpapi_api_key = "4855a30cc64d8fac37a10cb9c506083dfc5c07d4b4e62f4af01158fe61336ac9"

def read_csv_and_select_columns():
    # Convert the selected columns DataFrame to a string (for prompt)
    selected_lines = df.to_string(index=False)
    
    return selected_lines

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
def get_airport_code_by_city(airport_name):
    result = df[df['Airport Name'].str.contains(airport_name, case=False, na=False)]['Airport Code']
    if not result.empty:
        return result.values[0]
    else:
        return "City not found"

def get_promt(prompt):
    client = openai.OpenAI(
        api_key="sk-proj-31rvOvyTM13BSWMXnqMhT3BlbkFJ0fIRnpFuUIVvGLSVm6sH"
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an experienced worldwide vacation planner. Additionally you are familiar with airports around the world."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Return the completion result
        return completion.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_promt_fake(promt):
    return "Maldives, Male\nBora Bora, Tahiti\nSeychelles, Mahe\nPhuket, Phuket\nMaui, Maui"

    return completion.choices[0].message['content']

def get_possible_destinations(trip_type, month):
    selected_lines = read_csv_and_select_columns()
    prompt = (
    f"The following is a list of places and their corresponding airports from the CSV file:\n\n{selected_lines}\n\n"
        "Based on this information, suggest 5 possible travel destinations in the world for a "
        f"{trip_type} trip in {month}. For each destination, you have to return the response in the following structure "
        "(all the letters have to be English letters without any special characters):\n"
        "<possible travel destination>,<closest airport name>\n"
        "<possible travel destination>,<closest airport name>\n"
        "<possible travel destination>,<closest airport name>\n"
        "<possible travel destination>,<closest airport name>\n"
        "<possible travel destination>,<closest airport name>"
)
    response = get_promt(prompt)
    
    # Split the response into lines and create a dictionary
    destinations_dict = {}
    for line in response.split('\n'):
        travel_destination, closest_airport = line.split(', ')
        destinations_dict[travel_destination] = get_airport_code_by_city(closest_airport)
    
    return destinations_dict

def search_flights(destination, origin, start_date, end_date):
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

def find_flights_two_directions(destination, start_date, end_date):
    departure = search_flights(destination, "TLV", start_date, end_date)
    back = search_flights("TLV", destination, start_date, end_date)

    return departure, back

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

# Function to fetch hotels for a given destination
def fetch_hotels(destination, check_in_date, check_out_date):
    params = {
        "engine": "google_hotels",
        "q": f"hotels in {destination}",
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "location": destination,
        "api_key": serpapi_api_key
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if "error" in results:
        print(f"Error fetching hotels: {results['error']}")
        return []
    
    # Extract hotel information from the results
    hotels = []
    for hotel in results.get("properties", []):
        hotels.append({
            "name": hotel.get("name"),
            "description": hotel.get("description"),
            "address": hotel.get("gps_coordinates"),
            "rating": hotel.get("overall_rating"),
            "price": hotel.get("total_rate", {}).get("extracted_lowest"),
            "check_in_time": hotel.get("check_in_time"),
            "check_out_time": hotel.get("check_out_time"),
            "amenities": hotel.get("amenities"),
            "link": hotel.get("serpapi_property_details_link"),
        })
    return hotels

def find_best_hotel(destination, check_in_date, check_out_date, left_budget):
    hotels = fetch_hotels(destination, check_in_date, check_out_date)
    if hotel == None:
        return "no hotel found"
    return max((hotel for hotel in hotels if hotel["price"] < left_budget), key=lambda x: x["price"], default=None)

#display destinations and let user choose
def display_and_choose_destinations(destinations):
    # Display the 5 options
    print("destinations:")
    for i, (destination, info) in enumerate(destinations.items(), 1):
        print(f"{i}. {destination}:")
        for key, value in info.items():
            print(f"   {key}: {value}")
        print()

    # Get user choice
    choice = int(input("Choose a destination by entering the number: ")) - 1
    if 0 <= choice < len(destinations):
        chosen_destination = list(destinations.items())[choice][0]
        return chosen_destination, destinations[chosen_destination]
    else:
        print("Invalid choice.")
        return None



def print_for_each_flight():
    #dict to hokd all the details for every destenation
    destinations_info = {}
    #get user input
    start_date, end_date, budget, trip_type = get_user_input()
    month = get_month_from_date(start_date)
    
    #return dictonary contain for each contry the airport code
    destination_airport_dict = get_possible_destinations(trip_type, month)
    #iterate over each destenation and get the cheapest flight
    for dest in destination_airport_dict:
        if destination_airport_dict[dest] != "City not found":
            departures_flight_data = search_flights(destination_airport_dict[dest],start_date, end_date)
            arrival_flight_data = search_flights(destination_airport_dict[dest],start_date, end_date)
            cheapest_departure = get_cheapest_flight(departures_flight_data)
            cheapest_arrival = get_cheapest_flight(arrival_flight_data)
            flights_coast = cheapest_arrival["price"] + cheapest_departure["price"]
            if flights_coast >= budget:
                return "Not enough mony for this trip"
            best_hotel = find_best_hotel(dest, start_date, end_date, budget - flights_coast)
            if best_hotel == "no hotel found":
                return "no hotel found"
            elif best_hotel == None:
                return "not enough budget"
            destinations_info[dest] = {
                "departures flight" : departures_flight_data,
                "arrival flight" : arrival_flight_data,
                "flights coast" : flights_coast,
                "hotel" : best_hotel,
                "hotel coast" : best_hotel["price"],
                "total coast" : flights_coast +best_hotel["price"]
            }
        else:
            print("not good")
    

if __name__ == "__main__":
    #result = print_for_each_flight()
    #result = search_flights("d", "2024-07-21", "2024-07-27")
    # Ensure the file path is in the current directory
    
    #current_directory = os.getcwd()
    #file_path = os.path.join(current_directory, "flight_results.json")
        
    # Write the response data to the file
    #with open(file_path, 'w') as file:
    #    json.dump(result, file, indent=4)
    #print(df.columns)

    hotels = fetch_hotels("New York", "2024-07-21", "2024-07-27")
    print("Hotels in Ney York:")
    for hotel in hotels:
        print(json.dumps(hotel, indent=2))
    print("\n")
