# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:4-python3.8-appservice
FROM mcr.microsoft.com/azure-functions/python:4-python3.8

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true


COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY azure_search_documents-11.4.0b4-py3-none-any.whl /
RUN pip install  /azure_search_documents-11.4.0b4-py3-none-any.whl

COPY . /home/site/wwwroot