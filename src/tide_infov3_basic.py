#!/usr/bin/env python3

import requests
import datetime
import pytz
import tide  # You need to import the tide module to use tide.Reading
# You might need to adjust the path to indicatorbase.py and tidedatagetterbase.py
# if they are not in the same directory or accessible via PYTHONPATH
from tidedatagetterbase import TideDataGetterBase


class MyCustomTideGetter(TideDataGetterBase):

    @staticmethod
    # IMPORTANT: Remove @abstractmethod from here! (This comment is for initial setup, keep it for context)
    # --- START: Add 'durationDays' and 'seaportId' parameters to method signature ---
    def getTideData(logging=None, urlTimeoutInSeconds=20, durationDays=7, seaportId="0536"):
    # --- END: Add 'durationDays' and 'seaportId' parameters to method signature ---
        if logging:
            logging.info("MyCustomTideGetter.getTideData called.")

        # Set the API endpoint URL with placeholders for station and duration
        from tidedatagetterbase import TideDataGetterBase
import config


class MyCustomTideGetter(TideDataGetterBase):

    @staticmethod
    # IMPORTANT: Remove @abstractmethod from here! (This comment is for initial setup, keep it for context)
    # --- START: Add 'durationDays' and 'seaportId' parameters to method signature ---
    def getTideData(logging=None, urlTimeoutInSeconds=20, durationDays=7, seaportId="0536"):
    # --- END: Add 'durationDays' and 'seaportId' parameters to method signature ---
        if logging:
            logging.info("MyCustomTideGetter.getTideData called.")

        # Set the API endpoint URL with placeholders for station and duration
        station_details_endpoint_url = "https://admiraltyapi.azure-api.net/uktidalapi/api/V1/Stations/{station}"
        events_endpoint_url = "https://admiraltyapi.azure-api.net/uktidalapi/api/V1/Stations/{station}/TidalEvents?duration={duration}"

        # Set the API key and headers
        # CONSIDER: Moving API keys out of directly accessible code (e.g., environment variable)
        api_key = config.API_KEY
        headers = {"Ocp-Apim-Subscription-Key": api_key}

        # Set the station parameter from the seaportId passed from the indicator
        station = seaportId
        
        # --- START: Use the durationDays passed from indicator-tide ---
        # The API expects duration as a string, so convert the integer durationDays
        duration = str(durationDays)
        # --- END: Use the durationDays passed from indicator-tide ---

        if logging:
            logging.info(f"API Call Parameters: station='{station}', duration='{duration}' (from GUI preference)") # Debugging line to check duration

        tidalReadings = [] # This will store the tide.Reading objects
        location = "Unknown" # Default location

        try:
            # First, get the station name
            station_details_url = station_details_endpoint_url.format(station=station)
            station_response = requests.get(station_details_url, headers=headers, timeout=urlTimeoutInSeconds)
            station_response.raise_for_status()
            station_data = station_response.json()
            location = station_data.get("properties", {}).get("Name", "Unknown")

            # Build the API request URL for events
            api_url = events_endpoint_url.format(station=station, duration=duration)

            # Send the API request and fetch the response data
            response = requests.get(api_url, headers=headers, timeout=urlTimeoutInSeconds)
            response.raise_for_status() # Raise an exception for HTTP errors (e.g., 400, 401, 404, 500)
            response_data = response.json()

            if logging:
                # Log the full response data for debugging (can be very verbose for large responses)
                pass
                #logging.info(f"Full Raw API response data: {response_data}")
                #logging.info(f"Number of events in raw API response: {len(response_data)}")

            # Set up timezone awareness
            utc_timezone = pytz.utc
            local_timezone = pytz.timezone('Europe/London')  # Handles BST (British Summer Time) automatically

            # Get the current time in local timezone
            now_utc = datetime.datetime.now(datetime.UTC).astimezone(utc_timezone)
            now_local = now_utc.astimezone(local_timezone)

            # --- START: Corrected filtering logic for displaying all requested days ---
            # Calculate the start date (today) and end date (today + duration days) for filtering
            start_date = now_local.date()
            # Ensure duration is an integer for timedelta calculation
            end_date = start_date + datetime.timedelta(days=int(duration))

            # Iterate through each event in the API response
            for event in response_data:
                event_type = event["EventType"]
                tidal_height = event["Height"]
                tidal_time_str = event["DateTime"]

                # Convert the API's UTC time string to a timezone-aware local datetime object
                # The timestamp may contain fractional seconds, which are ignored.
                tidal_time_utc = datetime.datetime.strptime(tidal_time_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                tidal_time_local = utc_timezone.localize(tidal_time_utc).astimezone(local_timezone)
                event_date = tidal_time_local.date()

                # Filter events to include only those within the requested duration (e.g., 7 days)
                # This condition checks if the event date is from 'start_date' (inclusive)
                # up to 'end_date' (exclusive).
                if start_date <= event_date < end_date:
                    is_high = (event_type == "HighWater")
                    date_str = tidal_time_local.strftime("%A %B %d") # e.g., "Tuesday August 3rd"
                    time_str = tidal_time_local.strftime("%I:%M %p") # e.g., "4:07 AM"
                    level = f"{round(tidal_height, 2)}m" # Format height as string with 'm'
                    source_url = api_url # Or a more specific URL if the API provides it

                    tidalReadings.append(
                        tide.Reading(date_str, time_str, location, is_high, level, source_url)
                    )
            # --- END: Corrected filtering logic for displaying all requested days ---

        except requests.exceptions.RequestException as e:
            if logging:
                logging.error(f"Error fetching tide data: {e}")
            # In case of API errors, you might want to return an empty list or
            # a list with an error message to display in the indicator.
        except Exception as e:
            if logging:
                logging.error(f"An unexpected error occurred during data processing: {e}")

        # Sort the readings by time before returning
        # This ensures the events are displayed in chronological order
        # The key extracts the date and time string from the tide.Reading object,
        # combines them, and converts to a datetime object for proper sorting.
        tidalReadings.sort(key=lambda reading: datetime.datetime.strptime(f"{reading.getDate()} {reading.getTime()}", "%A %B %d %I:%M %p"))

        return tidalReadings

# The __main__ block is good for testing your script independently.
# When indicator-tide runs your script, it will call MyCustomTideGetter.getTideData directly
# and this __main__ block will not be executed by the indicator itself.
if __name__ == "__main__":
    import logging
    # Set up a basic logger for testing in the terminal
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    test_readings = MyCustomTideGetter.getTideData(logging=logging.getLogger(), durationDays=7) # Pass a test duration
    if test_readings:
        for reading in test_readings:
            print(reading)
    else:
        print("No tidal readings found or an error occurred. Check logs for details if running with indicator-tide.")
