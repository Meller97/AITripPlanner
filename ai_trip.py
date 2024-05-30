import openai
import pandas as pd
from datetime import datetime
from serpapi.google_search import GoogleSearch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import re
import json
import os
import unicodedata


# Load the CSV file
df = pd.read_csv('airports-code@public.csv', on_bad_lines='skip', delimiter=';',usecols=["Airport Code", "Airport Name", "City Name"])

#file in json format
json_file_path = 'airports-code@public.json'

#openAPI client
CLIENT = openai.OpenAI(
        api_key="sk-proj-31rvOvyTM13BSWMXnqMhT3BlbkFJ0fIRnpFuUIVvGLSVm6sH"
    )

#serpapi API key
serpapi_api_key = "95701e8c9048de5c246a437cce8c642234778be246c8cff722575e60800fc8d8"

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

def normalize_name(str: str) -> str:
    return unicodedata.normalize('NFKD', str).encode('ascii', 'ignore').decode('utf-8')  # nopep8

def get_month_from_date(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%B")

# Function to find airport code by city name
def get_airport_code_by_city(city_name, country_name):
    with open(json_file_path, 'r') as file:
        airport_codes = json.load(file)
    
    city_normalized = city_name.lower().strip()
    country_normalized = country_name.lower().strip()

    for airport in airport_codes:
        airport_city = airport['city_name'].lower().strip()
        airport_country = airport['country_name'].lower().strip()
        airport_name = airport['airport_name'].lower().strip()
        airport_country_code = airport['country_code'].lower().strip()
        
        if ((city_normalized in airport_city or airport_city in city_normalized or city_normalized in airport_name) and
            (country_normalized in airport_country or airport_country in country_normalized or country_normalized in airport_country_code or airport_country_code in country_normalized)):
            return airport['column_1']
    return ''

def upload_file_to_open_ai(file_path: str) -> str:
    response = CLIENT.files.create(file=open(file_path, 'rb'), purpose='assistants')
    return response.id

def get_promt(prompt, role):
    try:
        completion = CLIENT.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Return the completion result
        return completion.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_possible_destinations_fake(trip_type, month):
    response =  "New York, John F Kennedy Intl, JFK\nNegril, Negril, NEG\nPatong Beach, Patong Beach, PBS\nPompano Beach, Pompano Beach, PPM\nMyrtle Beach, Myrtle Beach Afb, MYR"
    destinations_dict = {}
    for line in response.split('\n'):
        travel_destination, closest_airport_name, closest_airport_code = line.split(', ')
        destinations_dict[travel_destination] = closest_airport_code
    
    return destinations_dict


def get_possible_destinations(trip_type, month):
    prompt = f"""Suggest a list of 10 possible travel destinations in the world for a
        {trip_type} trip in {month} month. 
        For each destination, i want you to give me the destination, the closest city with airport and the country of the city
        you have to return the response in the following structure and not includ any addition data:"
        "<possible travel destination>,<nearest city with airport>,<country>\n"
        "<possible travel destination>,<nearest city with airport>,<country>\n"
        "<possible travel destination>,<nearest city with airport>,<country>\n"
        "<possible travel destination>,<nearest city with airport>,<country>\n"
        "<possible travel destination>,<nearest city with airport>,<country>\n"
        "example for one line: Herzeliya, Tel Aviv, Israel"""

    file_id = upload_file_to_open_ai(json_file_path)

    prompt += f"""\nHere is the file ID for the airport codes of cities worldwide: {file_id}.
    Utilize this file to accurately identify the nearest city with an airport for each destination.
    Ensure that you do not provide a city and country combination that lacks an airport or does not exist in the file.
    Additionally, use this file to verify and provide the correct country name for each destination.
    if you can't use file do not mention that in at all i just want you to give me the list, use my tamplate exectly(without any numbers of line)"""

    role = "You are an experienced worldwide vacation planner. Additionally you are familiar with airports around the world."
    response = get_promt(prompt, role)
    
    # Split the response into lines and create a dictionary
    destinations_dict = {}
    for line in response.split('\n'):
        travel_destination, nearest_city_with_airport, country = line.split(',')
        destinations_dict[travel_destination] = get_airport_code_by_city(normalize_name(nearest_city_with_airport), normalize_name(country))
    
    return destinations_dict

def search_flights(destination, origin, start_date, end_date):
    params = {
  "engine": "google_flights",
  "departure_id": origin,
  "arrival_id": destination,
  "outbound_date": start_date,
  "return_date": end_date,
  "currency": "USD",
  "hl": "en",
  "api_key": "95701e8c9048de5c246a437cce8c642234778be246c8cff722575e60800fc8d8"
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
        price = hotel.get("total_rate", {}).get("extracted_lowest")
        if price == None:
            continue
        hotels.append({
            "name": hotel.get("name"),
            "description": hotel.get("description"),
            "address": hotel.get("gps_coordinates"),
            "rating": hotel.get("overall_rating"),
            "price": price,
            "check_in_time": hotel.get("check_in_time"),
            "check_out_time": hotel.get("check_out_time"),
            "amenities": hotel.get("amenities"),
            "link": hotel.get("serpapi_property_details_link"),
        })
    return hotels

def find_best_hotel(destination, check_in_date, check_out_date, left_budget):
    hotels = fetch_hotels(destination, check_in_date, check_out_date)
    if hotels == None:
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

def generate_daily_plan(destination, trip_type, start_date_str, end_date_str):
    # Parse the dates
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    # Calculate the number of days for the trip
    num_days = (end_date - start_date).days + 1

    # Create a prompt for the OpenAI API to generate a daily plan for the entire trip
    prompt = f"""Create a detailed daily plan for a{trip_type} trip to {destination} from {start_date_str} to {end_date_str}.
      Include activities, sightseeing spots, and meal recommendations for each day, considering the typical weather and season for that month.
      your answer must start with the daily plan without intro
      and the structur have to be as follow:
      Day 1:
      <list of day 1 activities here>
      
      Day 2:
      <list of day 1 activities here>
      .
      .
      .
      Day N:
      <list of day N activities here>

      summery list of 4 best activity of the trip:
      <activity>
      <activity>
      <activity>
      <activity>
      """
    role = "You are an experienced worldwide vacation planner. Knows every attraction in every city around the world."
    # Call the OpenAI API to get the plan for the entire trip
    return get_promt(prompt, role)

def extract_best_activities(plan_string):
    # Split the plan string into lines
    lines = plan_string.split('\n')
    
    # Find the start of the summary list
    start_index = None
    for i, line in enumerate(lines):
        if "summary list of 4 best activities of the trip:" in line.lower():
            start_index = i + 1
            break
    
    # If start index is found, extract the next 4 lines
    if start_index is not None:
        best_activities = []
        for j in range(start_index, len(lines)):
            line = lines[j].strip()
            if line:
                best_activities.append(line)
            if len(best_activities) == 4:
                break
        return best_activities
    else:
        return []

#creates 4 different images that will show the user how his trip will look like
def create_trip_images(plan_prompt):
    
    # Create a detailed prompt for DALL-E using the daily plan
    dalle_prompt = f"""Create image that visualize the following trip activity: 
    {plan_prompt}.
    make it look realistic, i want to feel like i am there when u see the image"""
    
    try:
        # Call the OpenAI DALL-E API to generate images (assuming older version endpoint)
        response = CLIENT.images.generate(
            model="dall-e-3",
            prompt=dalle_prompt,
            quality="standard",
            n=1,
            size="1024x1024"
        )

        images = []
        for i, image in enumerate(response.data):
            url = image.url
            if url:
                 images.append(url)
            else:
                images.append('')
        return images
    
    except Exception as e:
        print(f"An error occurred while generating images: {e}")

def get_destinations_info(start_date: str, end_date: str, budget: int, trip_type: str):
    #dict to hokd all the details for every destenation
    destinations_info = {}
    #get user input
    month = get_month_from_date(start_date)
    #return dictonary contain for each contry the airport code
    destination_airport_dict = get_possible_destinations(trip_type, month)
    #iterate over each destenation and get the cheapest flight
    for dest in destination_airport_dict:
        if destination_airport_dict[dest] != "City not found":
            departures_flight_data, arrival_flight_data = find_flights_two_directions(destination_airport_dict[dest],start_date, end_date)
            if departures_flight_data == None or arrival_flight_data == None:
                print("no flight for this")
                continue
            if "error" in departures_flight_data:
                print(f"Error fetching hotels: {departures_flight_data['error']}")
                continue
            if "error" in arrival_flight_data:
                print(f"Error fetching hotels: {arrival_flight_data['error']}")
                continue
            cheapest_departure = get_cheapest_flight(departures_flight_data)
            cheapest_arrival = get_cheapest_flight(arrival_flight_data)
            flights_coast = cheapest_arrival["price"] + cheapest_departure["price"]
            if flights_coast >= budget:
                print("Not enough mony for this trip")
                continue
            best_hotel = find_best_hotel(dest, start_date, end_date, budget - flights_coast)
            if best_hotel == "no hotel found":
                print("no hotel found")
                continue
            elif best_hotel == None:
                print("not enough budget")
                continue
            destinations_info[dest] = {
                "departures flight" : cheapest_departure["flights"],
                "arrival flight" : cheapest_arrival["flights"],
                "flights coast" : flights_coast,
                "hotel" : best_hotel,
                "hotel coast" : best_hotel["price"],
                "total coast" : flights_coast +best_hotel["price"]
            }
        else:
            print("not good")
    
    return destinations_info
    #chosen_destination, chosen_destination_info = display_and_choose_destinations(destinations_info)

def dest_info_to_string(destination_info):
    pass

def get_plan_and_images(destination, trip_type, start_date, end_date):
    daily_plan = generate_daily_plan(destination, trip_type, start_date, end_date)
    best_activities = extract_best_activities(daily_plan)
    images = []
    for activity in best_activities:
        images.append(create_trip_images(activity))
    return {"plan": daily_plan, "images": images}


# FastAPI setup
app = FastAPI()
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    # Allows all methods, including GET, POST, PUT, DELETE, etc.
    allow_methods=["*"],
    allow_headers=["*"],  # Allows all headers
)

# FastAPI routes
@app.get("/top-5-options")
def get_destinations_info_route(start_date: str, end_date: str, budget: int, trip_type: str):
    try:
        return get_destinations_info(start_date, end_date, budget, trip_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/daily-plan-and-images")
def get_plan_and_images_route(destination: str, trip_type: str, start_date: str, end_date: str):
    try:
        return get_plan_and_images(destination, trip_type, start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

    #hotels = fetch_hotels("New York", "2024-07-21", "2024-07-27")
    #print("Hotels in Ney York:")
    #for hotel in hotels:
    #    print(json.dumps(hotel, indent=2))
    #print("\n")
    pass
    #print(get_destinations_info("2024-07-21", "2024-07-27", 10000, "beach"))
