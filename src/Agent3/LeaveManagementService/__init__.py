import logging
import json
import azure.functions as func
from datetime import datetime

# Mock leave data
LEAVE_TYPES = ["Sick Leave", "Casual Leave", "Earned Leave", "Maternity Leave"]
LEAVE_BALANCE = {
    "Sick Leave": 5,
    "Casual Leave": 8,
    "Earned Leave": 15,
    "Maternity Leave": 90
}

# Mock function to apply leave
def apply_leave(employee_id: str, leave_type: str, start_date: str, end_date: str):
    if leave_type not in LEAVE_TYPES:
        return {"error": f"Invalid leave type: {leave_type}"}
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    days_requested = (end - start).days + 1
    
    if LEAVE_BALANCE.get(leave_type, 0) < days_requested:
        return {"error": f"Insufficient leave balance for {leave_type}"}
    
    # Deduct leave balance (mock operation)
    LEAVE_BALANCE[leave_type] -= days_requested
    return {"status": "success", "message": f"{leave_type} approved for {days_requested} days."}

# Azure Function Entry Point
def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        logging.info(f"Request body: {req_body}")
        action = req_body.get("QueryType")
        
        if action == "apply_leave":
            required_fields = ["EmployeeId", "LeaveType", "StartDate", "EndDate"]
            for field in required_fields:
                if field not in req_body:
                    return func.HttpResponse(
                        json.dumps({"error": f"Missing required field: '{field}'."}),
                        status_code=400,
                        mimetype="application/json"
                    )
            
            employee_id = req_body.get("EmployeeId")
            leave_type = req_body.get("LeaveType")
            start_date = req_body.get("StartDate")
            end_date = req_body.get("EndDate")
            
            response = apply_leave(employee_id, leave_type, start_date, end_date)
            return func.HttpResponse(json.dumps(response), status_code=200, mimetype="application/json")
        
        elif action == "view_leave_types":
            return func.HttpResponse(
                json.dumps({"status": "success", "leaveTypes": LEAVE_TYPES}),
                status_code=200,
                mimetype="application/json"
            )
        
        elif action == "view_leave_balance":
            return func.HttpResponse(
                json.dumps({"status": "success", "leaveBalance": LEAVE_BALANCE}),
                status_code=200,
                mimetype="application/json"
            )
        
        else:
            return func.HttpResponse(
                json.dumps({"error": "Invalid action specified."}),
                status_code=400,
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
