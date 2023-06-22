import binascii
import csv
import hashlib
import json
import os
import time
import uuid
from datetime import datetime
#import pyautogui
from flask import Flask, render_template, request, redirect, url_for, app
import requests

app = Flask(__name__, template_folder='templates', static_folder='css')

APIUsername = ""
APIKey = ""


@app.route('/')
def home():
    return render_template("index.html", PageTitle="Login")


def inputData1():
    requestURL = request.form["username"]
    return requestURL


def inputData2():
    requestURL = request.form["secret_key"]
    return requestURL


@app.route('/blog')
def blog():
    return render_template("blog.html", PageTitle="Fetch Processing Rules")


@app.route('/next_button', methods=['POST'])
def next_button():
    global APIUsername, APIKey, user_report_suites
    APIUsername = inputData1()
    APIKey = inputData2()
    url = 'https://api.omniture.com/admin/1.4/rest/?method=Company.GetReportSuites'
    payload = {}
    nonce = str(uuid.uuid4())
    base64nonce = binascii.b2a_base64(binascii.a2b_qp(nonce))
    created_date = datetime.utcnow().isoformat() + 'Z'
    sha = nonce + created_date + APIKey
    sha_object = hashlib.sha256(sha.encode())
    password_64 = binascii.b2a_base64(sha_object.digest())
    properties = {
        "Username": APIUsername,
        "PasswordDigest": password_64.decode().strip(),
        "Nonce": base64nonce.decode().strip(),
        "Created": created_date,
        "Algorithm": 'SHA256'
    }
    temp_header = ['{key}="{value}"'.format(key=k, value=v) for k, v in properties.items()]
    header = 'UsernameToken ' + ', '.join(temp_header)
    headers = {
        'X-WSSE': header,
        'Cookie': 'sc_locale=en_US; sc_locale_numbers=en_US'
    }
    print(str(headers))
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    print(response.text)
    res_json_data = json.loads(response.text)
    print(type(res_json_data))
    if response.status_code == 200:
        user_report_suites = res_json_data["report_suites"]
        return render_template('blog.html', result=user_report_suites)
    elif response.status_code == 400:
        return render_template('index.html', result=res_json_data["error_description"])
    else:
        return render_template('index.html', result="unknown error occurred")


@app.route('/download_button', methods=['POST'])
def download_button():
    report_suites_list = request.json['data']
    print(report_suites_list)

    url = 'https://api.omniture.com/admin/1.4/rest/?method=ReportSuite.ViewProcessingRules'

    temp_payload = {"rsid_list": report_suites_list}
    print(temp_payload)

    payload = json.dumps(temp_payload)
    print(payload)

    nonce = str(uuid.uuid4())
    base64nonce = binascii.b2a_base64(binascii.a2b_qp(nonce))
    created_date = datetime.utcnow().isoformat() + 'Z'
    sha = nonce + created_date + APIKey
    sha_object = hashlib.sha256(sha.encode())
    password_64 = binascii.b2a_base64(sha_object.digest())
    properties = {
        "Username": APIUsername,
        "PasswordDigest": password_64.decode().strip(),
        "Nonce": base64nonce.decode().strip(),
        "Created": created_date,
        "Algorithm": 'SHA256'
    }
    temp_header = ['{key}="{value}"'.format(key=k, value=v) for k, v in properties.items()]
    header = 'UsernameToken ' + ', '.join(temp_header)
    headers = {
        'X-WSSE': header,
        'Cookie': 'sc_locale=en_US; sc_locale_numbers=en_US'
    }
    print(str(headers))
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    print(response.text)
    res_json_data = json.loads(response.text)
    print(type(res_json_data))
    if response.status_code == 200:
        if os.name == "nt":
            DOWNLOAD_FILE = f"{os.getenv('USERPROFILE')}\\Downloads\\processing_rules_" + time.strftime(
                "%Y%m%d-%H%M%S") + ".csv"
        else:  # PORT: For *Nix systems
            DOWNLOAD_FILE = f"{os.getenv('HOME')}/Downloads/processing_rules_" + time.strftime("%Y%m%d-%H%M%S") + ".csv"

        # now we will open a file for writing
        data_file = open(DOWNLOAD_FILE, 'w', newline='')

        # create the csv writer object
        csv_writer = csv.writer(data_file)

        # Counter variable used for writing
        # headers to the CSV file
        count = 0

        try:
            for x in range(len(res_json_data)):
                print(x)
                processing_rules_data = res_json_data[x]['processing_rules']
                print(res_json_data[x]['processing_rules'])

                for data in processing_rules_data:
                    items = list(data.items())
                    items.insert(0, ('Report Suite ID', res_json_data[x]['rsid']))
                    updated_data = dict(items)

                    if count == 0:
                        # Writing headers of CSV file
                        print(type(data))
                        file_header_row = updated_data.keys()
                        csv_writer.writerow(file_header_row)
                        count += 1

                    # Writing data of CSV file
                    csv_writer.writerow(updated_data.values())

            if count == 0:
                csv_writer.writerow({'No Processing rules defined for the selected report suite(s)'})

            data_file.close()
            #return pyautogui.alert('Processing Rules extract available in Downloads folder',
                                   #"Download Successful")  # always returns "OK"

        except:
            print("Hello")
            #return pyautogui.alert('An error occurred',
                                   #"Error")  # always returns "OK"

    elif response.status_code == 400:
        return render_template('index.html', result=res_json_data["error_description"])
    else:
        return render_template('index.html', result="unknown error occurred")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
