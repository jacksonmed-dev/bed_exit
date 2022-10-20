import pandas as pd

from os.path import *
import sys

#from body.body import Patient
from braden_score import BradenScore


def patient_history_feature_extraction_df():
    #patient_data = Patient.get_body()
    patient_data = {
        "first_name": " Ben",
        "last_name": "Dover",
        "age": 36,
        "height": 72,
        "weight": 190
    }

    #history = Patient.get_patient_history()
    history = {
        "gender": 'male',
        "BMI": 19,
        "ulcer_history": ['arm', 'leg'],
        "ICU_days": 5,
        "temperature": 101.2,
        "diabetes": 'type_1',
        "systolic_blood_pressure": 125,
        "diastolic_blood_pressure": 77
    }

    history_df = pd.DataFrame(0, index=['data'], columns=['age','age_cat','sex','BMI', 'BMI_cat', 'ulcer_head',
                                                          'ulcer_arm', 'ulcer_shoulder', 'ulcer_buttocks',
                                                          'ulcer_leg', 'ulcer_heel',
                                                          'ICU_stay', 'temp',
                                                          'fever', 'diabetes_typeI', 'diabetes_typeII', 'sys_pressure',
                                                          'dia_pressure',
                                                          'blood_pressure_cat'])

    # This is all encoded with assumption all these factors can be collected
    age = int(patient_data.get('age'))
    gender = history.get('gender')
    BMI = float(history.get('BMI'))
    ulcer = history.get('ulcer_history')
    ICU = int(history.get('ICU_days'))
    temp = float(history.get('temperature'))
    diabetes = history.get('diabetes')
    sys = history.get('systolic_blood_pressure')
    dia = history.get('diastolic_blood_pressure')

    history_df.at['data','age'] = age

    if age < 70:
        history_df.at['data','age_cat'] = 0
    elif age >= 70:
        history_df.at['data', 'age_cat'] = 1

    if gender == 'female':
        history_df.at['data','sex'] = 0
    elif gender == 'male':
        history_df.at['data', 'sex'] = 1

    history_df.at['data', 'BMI'] = BMI

    # categorizing based on BMI according to CDC
    if BMI < 18.5:
        history_df.at['data', 'BMI_cat'] = 1
    elif 18.5 <= BMI <= 24.9:
        history_df.at['data', 'BMI_cat'] = 2
    elif 25 <= BMI <= 29.9:
        history_df.at['data', 'BMI_cat'] = 3
    elif 30 <= BMI <= 34.9:
        history_df.at['data', 'BMI_cat'] = 4
    elif 35 <= BMI <= 40:
        history_df.at['data', 'BMI_cat'] = 5
    elif BMI > 40:
        history_df.at['data', 'BMI_cat'] = 6

    history_df.at['data', 'ulcer_head'] = ulcer.count('head')
    history_df.at['data', 'ulcer_arm'] = ulcer.count('arm')
    history_df.at['data', 'ulcer_shoulder'] = ulcer.count('shoulder')
    history_df.at['data', 'ulcer_buttocks'] = ulcer.count('buttocks')
    history_df.at['data', 'ulcer_leg'] = ulcer.count('leg')
    history_df.at['data', 'ulcer_heel'] = ulcer.count('heel')

    history_df.at['data', 'ICU_stay'] = int(ICU)

    history_df.at['data', 'temp'] = float(temp)

    # hypothermia can be added
    if temp > 100.4:
        history_df.at['data', 'fever'] = 1
    else:
        history_df.at['data', 'fever'] = 0

    # test what happens if null is entered
    if diabetes == 'type_1':
        history_df.at['data', 'diabetes_typeI'] = 1
    else:
        history_df.at['data', 'diabetes_typeI'] = 0

    if diabetes == 'type_2':
        history_df.at['data', 'diabetes_typeII'] = 1
    else:
        history_df.at['data', 'diabetes_typeII'] = 0

    history_df.at['data', 'sys_pressure'] = float(sys)

    history_df.at['data', 'dia_pressure'] = float(dia)

    # based on CDC categorization
    if sys < 90 and dia < 60:
        history_df.at['data', 'blood_pressure_cat'] = 1
    elif 90 <= sys < 120 and 60 <= dia < 80:
        history_df.at['data', 'blood_pressure_cat'] = 2
    elif 120 <= sys <= 139 and 80 <= dia <= 89:
        history_df.at['data', 'blood_pressure_cat'] = 3
    elif 140 <= sys and 90 <= dia:
        history_df.at['data', 'blood_pressure_cat'] = 4

    #print(history_df)
    #print(history_df.dtypes)

    return history_df

def combine_features_df():
    history_df = patient_history_feature_extraction_df()
    braden_df = BradenScore().get_braden_df()
    braden_df.index = ['data']
    combined = pd.concat([history_df,braden_df], axis=1)
    return combined