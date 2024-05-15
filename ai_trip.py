import openai
from datetime import datetime
from serpapi import GoogleSearch

# Set your OpenAI API key
openai.api_key = 'your-openai-api-key'

def get_user_input():
    start_date = input("Enter the start date of your trip (YYYY-MM-DD):")
    end_date = input("Enter the end date of your trip (YYYY-MM-DD):")
    budget = float(input("Enter your total budget in USD:"))
    trip_type = input("Enter the type of trip (ski/beach/city):").lower()
    return start_date, end_date, budget, trip_type

def get_month_from_date(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%B")

def get_possible_destinations(trip_type, month):
    prompt = f"Suggest 5 possible travel destinations in the world for a {trip_type} trip in {month}."
    response = openai.Completion.create(
        model="text-davinci-003",  # Use "gpt-4" if you have access to it
        prompt=prompt,
        max_tokens=150  # Adjust this value based on desired response length
    )
    destinations = response.choices[0].text.strip().split('\n')
    return destinations