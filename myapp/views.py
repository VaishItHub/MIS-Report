import os
import gspread
import pandas as pd
import matplotlib.pyplot as plt
from oauth2client.service_account import ServiceAccountCredentials
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
from django.shortcuts import render
from django.http import HttpResponse
from .forms import GenerateReportForm

# Function to generate the report and upload it to Google Drive
def generate_mis_report():
    # Authenticate with Google Sheets API
    service_account_file = r"C:\Users\Sai\Desktop\domain\try.json"  # Replace with your credentials path
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(service_account_file, scopes=scope)
    gc = gspread.authorize(credentials)

    # Fetch data from Google Sheets
    sheet_url = "https://docs.google.com/spreadsheets/d/13NCzVUGcIWJBQt-JTOBIF7kVybBs-y1s9CmcJwJgSs4/edit?usp=sharing"
    spreadsheet = gc.open_by_url(sheet_url)
    main_sheet = spreadsheet.sheet1
    main_data = main_sheet.get_all_records()
    main_df = pd.DataFrame(main_data)

    # Sum all numerical columns
    sum_of_columns = main_df.sum(numeric_only=True)

    # Create a sum row for the columns
    sum_row = pd.DataFrame(sum_of_columns).T
    sum_row['Column Name'] = 'Total'  # Assuming 'Column Name' is a label column, adjust as necessary.

    # Concatenate the sum row at the bottom of the dataframe
    main_df = pd.concat([main_df, sum_row], ignore_index=True)

    # Generate Pie Chart from Sum Row
    def generate_pie_chart(data, output_path):
        # Convert the sum row to a 1D list (ignoring the 'Column Name')
        data_values = data.values.flatten()  # Flatten the data to get a 1D array of sum values
        
        # Labels for the pie chart will be the column names
        labels = data.columns

        # Ensure that both 'data_values' and 'labels' have the same length
        if len(data_values) != len(labels):
            raise ValueError(f"Data values length ({len(data_values)}) and labels length ({len(labels)}) must match.")
        
        # Generate the pie chart
        plt.figure(figsize=(4, 4))
        plt.pie(data_values, labels=labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
        plt.title("Distribution of Column Totals")
        plt.savefig(output_path)
        plt.close()

    # Save Pie Chart for the sum row (optional)
    pie_chart_path_main = "main_sheet_pie_chart.png"
    generate_pie_chart(sum_row.drop(columns='Column Name'), pie_chart_path_main)

    # Create Combined Excel File
    output_file_path = "Combined_Workbook_with_Graphs.xlsx"
    with pd.ExcelWriter(output_file_path, engine="openpyxl") as writer:
        main_df.to_excel(writer, index=False, sheet_name="Main Sheet")

    # Embed Pie Chart in Excel (optional)
    wb = load_workbook(output_file_path)
    if not main_df.empty:
        ws_main = wb["Main Sheet"]
        img_main = Image(pie_chart_path_main)
        ws_main.add_image(img_main, "H1")  # Position image in cell H1
    wb.save(output_file_path)

    # Upload to Google Drive
    gauth = GoogleAuth()
    gauth.credentials = credentials
    drive = GoogleDrive(gauth)
    upload_file = drive.CreateFile({"title": "Combined_Workbook_with_Graphs.xlsx"})
    upload_file.SetContentFile(output_file_path)
    upload_file.Upload()

    # Make the file publicly accessible
    upload_file.InsertPermission({
        "type": "anyone",
        "value": "anyone",
        "role": "reader"
    })

    # Return the shareable URL
    return upload_file['alternateLink']

# View to handle the form and show the URL
def generate_report(request):
    form = GenerateReportForm(request.POST or None)
    shareable_url = None

    if form.is_valid():
        # Call the function to generate the MIS report
        shareable_url = generate_mis_report()

    return render(request, 'generate_report.html', {'form': form, 'shareable_url': shareable_url})
