import logging
import json
import azure.functions as func


def get_employee_data_by_first_name(first_name: str):
    # Mock employee data
    employees = {
        "Emp1": {
            "firstName": "Alice",
            "lastName": "Smith",
            "email": "alice.smith@org.com",
            "phone": "+1234567891",
            "company": "TechCorp",
            "eventId": "TL-2025-01",
            "eventName": "TechLabs Workshop on Cloud Computing",
            "skills": ["Python", "Machine Learning", "Data Science"],
            "attendance": "Yes",
            "registrationTimestamp": "2025-01-24T08:00:00Z"
        },
        "Emp2": {
            "firstName": "Bob",
            "lastName": "Johnson",
            "email": "bob.johnson@org.com",
            "phone": "+1234567892",
            "company": "InnovateTech",
            "eventId": "TL-2025-02",
            "eventName": "TechLabs Workshop on AI Development",
            "skills": ["AI", "Deep Learning", "TensorFlow"],
            "attendance": "Yes",
            "registrationTimestamp": "2025-01-22T09:00:00Z"
        },
        "Emp3": {
            "firstName": "Charlie",
            "lastName": "Williams",
            "email": "charlie.williams@org.com",
            "phone": "+1234567893",
            "company": "TechHive",
            "eventId": "TL-2025-03",
            "eventName": "TechLabs Workshop on Cybersecurity",
            "skills": ["Networking", "Ethical Hacking", "Firewalls"],
            "attendance": "No",
            "registrationTimestamp": "2025-01-23T07:00:00Z"
        },
        "Emp4": {
            "firstName": "David",
            "lastName": "Brown",
            "email": "david.brown@org.com",
            "phone": "+1234567894",
            "company": "DevWorks",
            "eventId": "TL-2025-01",
            "eventName": "TechLabs Workshop on Cloud Computing",
            "skills": ["AWS", "Azure", "Docker"],
            "attendance": "Yes",
            "registrationTimestamp": "2025-01-20T11:00:00Z"
        },
        "Emp5": {
            "firstName": "Eva",
            "lastName": "Davis",
            "email": "eva.davis@org.com",
            "phone": "+1234567895",
            "company": "CloudX",
            "eventId": "TL-2025-02",
            "eventName": "TechLabs Workshop on AI Development",
            "skills": ["AI", "Neural Networks", "Python"],
            "attendance": "Yes",
            "registrationTimestamp": "2025-01-21T10:00:00Z"
        }
    }

    # Find the employee data by first name
    for emp_data in employees.values():
        if emp_data["firstName"].lower() == first_name.lower():
            return emp_data
    return None


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Parse JSON payload
        req_body = req.get_json()
        
        # Validate required fields in the payload
        required_fields = ["QueryType", "FirstName", "Language"]
        for field in required_fields:
            if field not in req_body:
                return func.HttpResponse(
                    json.dumps({"error": f"Missing required field: '{field}'."}),
                    status_code=400,
                    mimetype="application/json"
                )

        # Extract the first name from the payload
        first_name = req_body.get("FirstName")
        
        # Fetch employee details
        employee_data = get_employee_data_by_first_name(first_name)
        if not employee_data:
            return func.HttpResponse(
                json.dumps({"error": f"No employee found with first name '{first_name}'."}),
                status_code=404,
                mimetype="application/json"
            )

        # Return success response with employee data
        return func.HttpResponse(
            json.dumps({"status": "success", "data": employee_data}),
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
