import logging
import json
import azure.functions as func
from datetime import datetime


def get_available_flights(departure_city: str, arrival_city: str, departure_date: str, return_date: str = None):
    # Mock flight data (you could replace this with a call to a flight API)
    flights = [
        {
            "flightNumber": "AI2025",
            "departureCity": "New York",
            "arrivalCity": "Los Angeles",
            "departureDate": "2025-03-10T08:00:00Z",
            "returnDate": "2025-03-17T16:00:00Z",
            "price": "$350"
        },
        {
            "flightNumber": "UA4010",
            "departureCity": "New York",
            "arrivalCity": "Los Angeles",
            "departureDate": "2025-03-10T10:00:00Z",
            "returnDate": "2025-03-17T18:00:00Z",
            "price": "$400"
        },
        {
            "flightNumber": "DL3032",
            "departureCity": "Chicago",
            "arrivalCity": "San Francisco",
            "departureDate": "2025-03-12T06:30:00Z",
            "returnDate": "2025-03-19T14:30:00Z",
            "price": "$420"
        },
        {
            "flightNumber": "AA1505",
            "departureCity": "Miami",
            "arrivalCity": "Dallas",
            "departureDate": "2025-03-14T09:00:00Z",
            "returnDate": "2025-03-21T17:00:00Z",
            "price": "$320"
        },
        {
            "flightNumber": "SW9873",
            "departureCity": "Austin",
            "arrivalCity": "Houston",
            "departureDate": "2025-03-11T13:00:00Z",
            "returnDate": "2025-03-18T12:00:00Z",
            "price": "$180"
        },
        {
            "flightNumber": "BA8472",
            "departureCity": "London",
            "arrivalCity": "New York",
            "departureDate": "2025-03-10T07:45:00Z",
            "returnDate": "2025-03-17T15:15:00Z",
            "price": "$800"
        },
        {
            "flightNumber": "QF1021",
            "departureCity": "Sydney",
            "arrivalCity": "Los Angeles",
            "departureDate": "2025-03-09T22:00:00Z",
            "returnDate": "2025-03-16T10:30:00Z",
            "price": "$1200"
        },
        {
            "flightNumber": "AF5483",
            "departureCity": "Paris",
            "arrivalCity": "New York",
            "departureDate": "2025-03-13T15:30:00Z",
            "returnDate": "2025-03-20T19:00:00Z",
            "price": "$950"
        },
        {
            "flightNumber": "LH7590",
            "departureCity": "Frankfurt",
            "arrivalCity": "Chicago",
            "departureDate": "2025-03-15T06:00:00Z",
            "returnDate": "2025-03-22T17:45:00Z",
            "price": "$750"
        },
        {
            "flightNumber": "EK2020",
            "departureCity": "Dubai",
            "arrivalCity": "Los Angeles",
            "departureDate": "2025-03-08T03:30:00Z",
            "returnDate": "2025-03-15T08:00:00Z",
            "price": "$1000"
        }
    ]


    available_flights = []
    for flight in flights:
        # Check if the flight matches the provided cities and dates
        if (flight["departureCity"].lower() == departure_city.lower() and
            flight["arrivalCity"].lower() == arrival_city.lower() and
            datetime.strptime(flight["departureDate"], "%Y-%m-%dT%H:%M:%SZ") >= datetime.strptime(departure_date, "%Y-%m-%d")):
            # If return date is provided, filter by return date
            if return_date:
                if datetime.strptime(flight["returnDate"], "%Y-%m-%dT%H:%M:%SZ") >= datetime.strptime(return_date, "%Y-%m-%d"):
                    available_flights.append(flight)
            else:
                available_flights.append(flight)

    return available_flights


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Parse JSON payload
        req_body = req.get_json()

        # Validate required fields in the payload
        required_fields = ["DepartureCity", "ArrivalCity", "DepartureDate"]
        for field in required_fields:
            if field not in req_body:
                return func.HttpResponse(
                    json.dumps({"error": f"Missing required field: '{field}'."}),
                    status_code=400,
                    mimetype="application/json"
                )

        # Extract flight details from the payload
        departure_city = req_body.get("DepartureCity")
        arrival_city = req_body.get("ArrivalCity")
        departure_date = req_body.get("DepartureDate")
        return_date = req_body.get("ReturnDate", None)  # Optional field

        # Fetch available flights
        available_flights = get_available_flights(departure_city, arrival_city, departure_date, return_date)
        if not available_flights:
            return func.HttpResponse(
                json.dumps({"error": f"No flights available for the specified route and dates."}),
                status_code=404,
                mimetype="application/json"
            )

        # Return success response with flight data
        return func.HttpResponse(
            json.dumps({"status": "success", "flights": available_flights}),
            status_code=200,
            mimetype="application/json"
        )

    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON payload."}),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error."}),
            status_code=500,
            mimetype="application/json"
        )
