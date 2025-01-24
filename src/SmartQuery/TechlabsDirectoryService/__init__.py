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
        },
        "Emp6": {
            "firstName": "Frank",
            "lastName": "Miller",
            "email": "frank.miller@org.com",
            "phone": "+1234567896",
            "company": "CyberTech",
            "eventId": "TL-2025-03",
            "eventName": "TechLabs Workshop on Cybersecurity",
            "skills": ["Penetration Testing", "Firewalls", "Network Security"],
            "attendance": "No",
            "registrationTimestamp": "2025-01-25T12:00:00Z"
        },
        "Emp7": {
            "firstName": "Grace",
            "lastName": "Wilson",
            "email": "grace.wilson@org.com",
            "phone": "+1234567897",
            "company": "TechDynamos",
            "eventId": "TL-2025-01",
            "eventName": "TechLabs Workshop on Cloud Computing",
            "skills": ["Google Cloud", "Kubernetes", "Terraform"],
            "attendance": "Yes",
            "registrationTimestamp": "2025-01-19T14:00:00Z"
        },
        "Emp8": {
            "firstName": "Henry",
            "lastName": "Moore",
            "email": "henry.moore@org.com",
            "phone": "+1234567898",
            "company": "InnoTech",
            "eventId": "TL-2025-02",
            "eventName": "TechLabs Workshop on AI Development",
            "skills": ["Machine Learning", "AI", "Data Engineering"],
            "attendance": "Yes",
            "registrationTimestamp": "2025-01-18T16:00:00Z"
        },
        "Emp9": {
            "firstName": "Ivy",
            "lastName": "Taylor",
            "email": "ivy.taylor@org.com",
            "phone": "+1234567899",
            "company": "FutureTech",
            "eventId": "TL-2025-03",
            "eventName": "TechLabs Workshop on Cybersecurity",
            "skills": ["Cloud Security", "Network Monitoring", "Cryptography"],
            "attendance": "No",
            "registrationTimestamp": "2025-01-17T17:00:00Z"
        },
        "Emp10": {
            "firstName": "Jack",
            "lastName": "Anderson",
            "email": "jack.anderson@org.com",
            "phone": "+1234567800",
            "company": "TechFuture",
            "eventId": "TL-2025-01",
            "eventName": "TechLabs Workshop on Cloud Computing",
            "skills": ["Cloud Storage", "Big Data", "DevOps"],
            "attendance": "Yes",
            "registrationTimestamp": "2025-01-16T19:00:00Z"
        }
    }
    
    # Search for the employee by first name
    result = {}
    for emp_id, emp_data in employees.items():
        if emp_data["firstName"].lower() == first_name.lower():
            result = emp_data
            break

    return result if result else None

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Get firstName from the query parameter
        first_name = req.params.get('firstName')
        
        if not first_name:
            return func.HttpResponse(
                "Please provide a valid first name.",
                status_code=400
            )
        
        # Fetch employee data based on the first name
        employee_data = get_employee_data_by_first_name(first_name)
        
        if not employee_data:
            return func.HttpResponse(
                f"Employee with first name '{first_name}' not found.",
                status_code=404
            )

        # Return employee details as JSON
        return func.HttpResponse(
            json.dumps({"status": "success", "data": employee_data}),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error fetching employee data: {str(e)}")
        return func.HttpResponse(
            "Internal server error.",
            status_code=500
        )
