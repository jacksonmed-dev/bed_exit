import pandas as pd
from flask import Blueprint, Flask, current_app, request
import json
import pathlib
from configuration import config

config_blue = config['BLUETOOTHCONNECTION']
config_paths = config['PATHS']

path = pathlib.Path().resolve()
server_endpoints = Blueprint("server_endpoints", __name__)


def get_bed():
    bed = current_app.config["bed"]
    if bed is None:
        return None
    return bed


def get_bluetooth():
    bluetooth = current_app.config["bluetooth"]
    if bluetooth is None:
        return None
    return bluetooth


# Currently a dummy function that returns dummy data.
@server_endpoints.route('/patient/max_pressure', methods=["GET"])
def get_patient_pressure():
    bed = get_bed()
    patient = bed.get_patient()
    df = pd.read_csv(str(path) + "/../tests/test_files/body_stats_df.csv", index_col=0)
    patient.set_body_stats_df(df)
    return patient.get_body_stats_df()['max_pressure'].to_json()
    # return patient.get_body_stats_df_json()


@server_endpoints.route('/patient/info', methods=["GET"])
def get_patient_info():
    bed = get_bed()
    patient = bed.get_patient()
    return patient.get_patient_info_json()


# There needs to be checks in place here. Is there already a thread???
@server_endpoints.route('/massage/start', methods=["GET"])
def start_message():
    bed = get_bed()
    massage = bed.get_massage()
    if massage.isAlive():
        massage.set_massage_status(False)
        massage.join()

    bed.set_new_massage()
    massage = bed.get_massage()
    massage.start()
    return json.dumps({"status": "massage started"})


@server_endpoints.route('/massage/stop', methods=["GET"])
def stop_message():
    massage = get_bed().get_massage()
    massage.set_massage_status(False)
    massage.join()
    if massage.isAlive():
        return json.dumps({"status": "Thread Still Running..."})
    return json.dumps({"status": "massage stopped"})


# Endpoint should read like this: http://localhost:5000/massage?type=1
@server_endpoints.route('/massage', methods=["GET"])
def choose_massage():
    massage = get_bed().get_massage()
    massage_type = int(request.args.get('type'))
    try:
        massage.set_massage_status(massage_type)
        return json.dumps({"status": "Massage type updated successfully"})
    except ValueError as e:
        return json.dumps({"status": e})


@server_endpoints.route('/bed/status', methods=["GET"])
def bed_status():
    bed = get_bed()
    return bed.generate_bed_status_json()


@server_endpoints.route('/bluetooth/send', methods=["GET"])
def test_bluetooth():
    data_set = {"key1": [1, 2, 3], "key2": [4, 5, 6]}
    json_dump = json.dumps(data_set)
    bluetooth = get_bluetooth()
    bluetooth.send_data(json_dump)


def create_server(bed, bluetooth):
    app = Flask(__name__)
    app.register_blueprint(server_endpoints)
    app.config["bed"] = bed
    app.config["bluetooth"] = bluetooth

    return app
