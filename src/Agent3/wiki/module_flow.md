# Module Flow: Leave Management API

This document outlines the flow of the **Leave Management API**, which allows employees to apply for leave, check leave status, and retrieve leave history.

## Overview

The API enables employees to submit leave requests, view their leave status, and fetch their leave history. It validates input data, processes leave applications based on company policies, and returns appropriate responses.

## Flow Steps

1. **API Endpoints**:
   - **Apply for Leave**:
     - URL: `https://<your-function-url>/api/apply-leave`
     - Method: `POST`
     - Body Parameters (JSON):
       - `employeeId` (Required)
       - `leaveType` (Required) - (e.g., "Sick Leave", "Casual Leave", "Paid Leave")
       - `startDate` (Required) - Leave start date in `YYYY-MM-DD` format
       - `endDate` (Required) - Leave end date in `YYYY-MM-DD` format
       - `reason` (Optional) - Reason for leave

   - **Check Leave Status**:
     - URL: `https://<your-function-url>/api/leave-status`
     - Method: `GET`
     - Query Parameter: `employeeId` (Required)

   - **Fetch Leave History**:
     - URL: `https://<your-function-url>/api/leave-history`
     - Method: `GET`
     - Query Parameter: `employeeId` (Required)

2. **Request Flow**:
   - **Applying for Leave**:
     - The API validates the request body for required fields.
     - Checks leave balance for the requested leave type.
     - If eligible, the leave request is saved and assigned a status (`Pending`, `Approved`, or `Rejected`).
     - Returns a confirmation response with the leave request details.
   
   - **Checking Leave Status**:
     - The API fetches the current leave requests for the given `employeeId`.
     - Returns the list of pending and approved leaves.
   
   - **Fetching Leave History**:
     - The API retrieves past leave records for the given `employeeId`.
     - Returns a list of all approved, rejected, and pending leave requests.

3. **Mock Leave Data**:
   - The mock leave data contains employee leave records with the following attributes:
     - `employeeId`
     - `leaveType`
     - `startDate`
     - `endDate`
     - `status` (Pending, Approved, Rejected)
     - `reason`
     - `requestTimestamp`
   - Example leave record:
     ```json
     {
       "employeeId": "E12345",
       "leaveType": "Sick Leave",
       "startDate": "2025-02-10",
       "endDate": "2025-02-12",
       "status": "Approved",
       "reason": "Flu",
       "requestTimestamp": "2025-02-08T10:00:00Z"
     }
     ```

4. **Error Handling**:
   - If required parameters are missing, the API returns a `400 Bad Request` response:
     ```json
     {
       "status": "error",
       "message": "Missing required fields: employeeId, leaveType, startDate, endDate."
     }
     ```
   - If leave balance is insufficient, the API returns a `403 Forbidden` response:
     ```json
     {
       "status": "error",
       "message": "Insufficient leave balance."
     }
     ```
   - If the employee ID is not found, the API returns a `404 Not Found` response:
     ```json
     {
       "status": "error",
       "message": "Employee ID not found."
     }
     ```
   - Unexpected errors return a `500 Internal Server Error`:
     ```json
     {
       "status": "error",
       "message": "Internal server error."
     }
     ```

5. **Response Flow**:
   - **Successful Leave Application**:
     - Status Code: `200 OK`
     - Response Body:
       ```json
       {
         "status": "success",
         "message": "Leave request submitted successfully.",
         "leaveRequest": {
           "employeeId": "E12345",
           "leaveType": "Sick Leave",
           "startDate": "2025-02-10",
           "endDate": "2025-02-12",
           "status": "Pending",
           "requestTimestamp": "2025-02-08T10:00:00Z"
         }
       }
       ```
   
   - **Leave Status Response**:
     - Status Code: `200 OK`
     - Response Body:
       ```json
       {
         "status": "success",
         "pendingLeaves": [
           {
             "leaveType": "Paid Leave",
             "startDate": "2025-03-01",
             "endDate": "2025-03-05",
             "status": "Pending"
           }
         ],
         "approvedLeaves": [
           {
             "leaveType": "Sick Leave",
             "startDate": "2025-02-10",
             "endDate": "2025-02-12",
             "status": "Approved"
           }
         ]
       }
       ```
   
   - **Leave History Response**:
     - Status Code: `200 OK`
     - Response Body:
       ```json
       {
         "status": "success",
         "leaveHistory": [
           {
             "leaveType": "Sick Leave",
             "startDate": "2025-02-10",
             "endDate": "2025-02-12",
             "status": "Approved"
           },
           {
             "leaveType": "Casual Leave",
             "startDate": "2024-12-15",
             "endDate": "2024-12-16",
             "status": "Rejected"
           }
         ]
       }
       ```

## Sample Requests

### Request 1: Apply for Leave
```http
POST https://<your-function-url>/api/apply-leave
Content-Type: application/json

{
  "employeeId": "E12345",
  "leaveType": "Sick Leave",
  "startDate": "2025-02-10",
  "endDate": "2025-02-12",
  "reason": "Flu"
}
```

### Request 2: Check Leave Status
```http
GET https://<your-function-url>/api/leave-status?employeeId=E12345
```

### Request 3: Fetch Leave History
```http
GET https://<your-function-url>/api/leave-history?employeeId=E12345
```

