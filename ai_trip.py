import openai
import pandas as pd
from datetime import datetime
from serpapi import GoogleSearch
import re

# Load the CSV file
df = pd.read_csv('airports-code@public.csv', on_bad_lines='skip', delimiter=';')

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
        "q": f"flights from TLV to {destination} {start_date} to {end_date}",
        "api_key": "348ca3e38bcedb80fcc8b2d30f28d34ec560dbebb131ba1961ef1213e555e55c"
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    return results

def get_cheapest_flight(flights_data):
    flights_results = flights_data.get("flights_results", [])
    
    if not flights_results:
        return None

    cheapest_flight = None
    lowest_price = float('inf')

    for flight in flights_results:
        # Extract the numeric value from the price string (e.g., "$350" -> 350)
        price_str = flight.get("price", "")
        price = float(re.sub(r'[^\d.]', '', price_str))
        
        if price < lowest_price:
            lowest_price = price
            cheapest_flight = flight

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
        if(destination_airport_dict[dest] is not "City not found")       
            flight_data = search_flights(destination_airport_dict[dest],start_date, end_date)
            cheapest = get_cheapest_flight(flight_data)
            print(cheapest)
        else:
            print("not good")
    #for dest in destination_airport_dict:

if __name__ == "__main__":
    print_for_each_flight()
    #print(df.columns)