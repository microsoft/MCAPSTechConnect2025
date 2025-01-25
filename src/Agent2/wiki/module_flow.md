# Module Flow: TechLabs Employee Registration API

This document outlines the flow of the **TechLabs Employee Registration API** that returns employee data based on the first name provided in the query parameter.

## Overview

The function receives an HTTP request with a query parameter `firstName`. It checks the provided `firstName` against a mock database of employee records and returns the corresponding employee details. If no matching employee is found, it returns a `404 Not Found` response.

## Flow Steps

1. **API Endpoint**:
   - URL: `https://<your-function-url>/api/your-function-name`
   - Method: `GET`
   - Query Parameter: `firstName` (Required)

2. **Request Flow**:
   - The function expects a `firstName` query parameter in the HTTP request.
   - If the `firstName` is not provided, the function will return an error message prompting the user to provide a valid first name.
   - If the `firstName` is provided:
     - The function checks the first name against the mock employee data.
     - If a matching employee is found, it returns the employee's data in JSON format.
     - If no employee matches the given first name, it returns a `404 Not Found` message.

3. **Mock Employee Data**:
   - The mock employee data contains 10 employee records, each with the following attributes:
     - `firstName`
     - `lastName`
     - `email`
     - `phone`
     - `company`
     - `eventId`
     - `eventName`
     - `skills`
     - `attendance`
     - `registrationTimestamp`
   - Example of an employee's data:
     ```json
     {
       "firstName": "Alice",
       "lastName": "Smith",
       "email": "alice.smith@example.com",
       "phone": "+1234567891",
       "company": "TechCorp",
       "eventId": "TL-2025-01",
       "eventName": "TechLabs Workshop on Cloud Computing",
       "skills": ["Python", "Machine Learning", "Data Science"],
       "attendance": "Yes",
       "registrationTimestamp": "2025-01-24T08:00:00Z"
     }
     ```

4. **Error Handling**:
   - If the `firstName` parameter is missing, the function returns a `400 Bad Request` response with the message:
     - `"Please provide a valid first name."`
   - If the employee is not found, the function returns a `404 Not Found` response with the message:
     - `"Employee with first name '<firstName>' not found."`
   - Any unexpected errors are caught and logged, and the function returns a `500 Internal Server Error` with the message:
     - `"Internal server error."`

5. **Response Flow**:
   - **Successful Response** (Employee Found):
     - Status Code: `200 OK`
     - Body:
       ```json
       {
         "status": "success",
         "data": {
           "firstName": "Alice",
           "lastName": "Smith",
           "email": "alice.smith@example.com",
           "phone": "+1234567891",
           "company": "TechCorp",
           "eventId": "TL-2025-01",
           "eventName": "TechLabs Workshop on Cloud Computing",
           "skills": ["Python", "Machine Learning", "Data Science"],
           "attendance": "Yes",
           "registrationTimestamp": "2025-01-24T08:00:00Z"
         }
       }
       ```
   - **Error Response** (Employee Not Found):
     - Status Code: `404 Not Found`
     - Body:
       ```json
       {
         "status": "error",
         "message": "Employee with first name 'NonExistent' not found."
       }
       ```
   - **Error Response** (Missing `firstName`):
     - Status Code: `400 Bad Request`
     - Body:
       ```json
       {
         "status": "error",
         "message": "Please provide a valid first name."
       }
       ```
   - **Internal Server Error**:
     - Status Code: `500 Internal Server Error`
     - Body:
       ```json
       {
         "status": "error",
         "message": "Internal server error."
       }
       ```

## Sample Requests

### Request 1: Fetch Employee with First Name "Alice"
```http
GET https://<your-function-url>/api/your-function-name?firstName=Alice
