import pandas as pd
import random
for i in range(20):
        features = pd.DataFrame(0,index=range(1200),
                                    columns=['timestamp','braden', 'ulcer_head', 'ulcer_shoulder', 'ulcer_arm', 'ulcer_buttocks', 'ulcer_leg', 'ulcer_heel',
                                             'EMA_head', 'EMA_shoulder', 'EMA_arm', 'EMA_buttocks', 'EMA_leg', 'EMA_heel',
                                             'movement_score_head', 'movement_score_shoulder', 'movement_score_arm', 'movement_score_buttocks', 'movement_score_leg', 'movement_score_heel',
                                             'outcome_head', 'outcome_shoulder', 'outcome_arm', 'outcome_buttocks','outcome_leg', 'outcome_heel'])

        #create time stamps for an hour
        features['timestamp'] = pd.date_range(start="2022-07-20", freq="3S", periods=1200)

        #randomly assign braden score, which stays the same through the time series
        features['braden']= random.randrange(1,24)

        #assign "present" (1) to random sample of 10% of data for each of the preexisting ulcer columns
        features['ulcer_head'] = random.randrange(0,2)
        features['ulcer_shoulder'] = random.randrange(0,2)
        features['ulcer_arm'] = random.randrange(0,2)
        features['ulcer_buttocks'] = random.randrange(0,2)
        features['ulcer_leg'] = random.randrange(0,2)
        features['ulcer_heel'] = random.randrange(0,2)

        #randomly assign pressure values between 0 and 104
        features['EMA_head']= features['EMA_head'].apply(lambda x: random.randrange(0,105))
        features['EMA_shoulder']= features['EMA_head'].apply(lambda x: random.randrange(0,105))
        features['EMA_arm']= features['EMA_head'].apply(lambda x: random.randrange(0,105))
        features['EMA_buttocks']= features['EMA_head'].apply(lambda x: random.randrange(0,105))
        features['EMA_leg']= features['EMA_head'].apply(lambda x: random.randrange(0,105))
        features['EMA_heel']= features['EMA_head'].apply(lambda x: random.randrange(0,105))


        #randomly assign movement scores as floats ranging from 0 to 5
        features['movement_score_head']= features['movement_score_head'].apply(lambda x: random.randrange(0,6))
        features['movement_score_shoulder']= features['movement_score_shoulder'].apply(lambda x: random.randrange(0,6))
        features['movement_score_arm']= features['movement_score_arm'].apply(lambda x: random.randrange(0,6))
        features['movement_score_buttocks']= features['movement_score_buttocks'].apply(lambda x: random.randrange(0,6))
        features['movement_score_leg']= features['movement_score_leg'].apply(lambda x: random.randrange(0,6))
        features['movement_score_heel']= features['movement_score_heel'].apply(lambda x: random.randrange(0,6))

        features['outcome_head']= features['outcome_head'].apply(lambda x: random.randrange(0,181))
        features['outcome_shoulder']= features['outcome_shoulder'].apply(lambda x: random.randrange(0,181))
        features['outcome_arm']= features['outcome_arm'].apply(lambda x: random.randrange(0,181))
        features['outcome_buttocks']= features['outcome_buttocks'].apply(lambda x: random.randrange(0,181))
        features['outcome_leg']= features['outcome_leg'].apply(lambda x: random.randrange(0,181))
        features['outcome_heel']= features['outcome_heel'].apply(lambda x: random.randrange(0,181))

        features = features.astype({'braden': 'int64','ulcer_head': 'int64', 'ulcer_shoulder': 'int64', 'ulcer_arm': 'int64', 'ulcer_buttocks': 'int64', 'ulcer_leg': 'int64', 'ulcer_heel': 'int64',
                                    'movement_score_head': 'int64', 'movement_score_shoulder': 'int64', 'movement_score_arm': 'int64', 'movement_score_buttocks': 'int64', 'movement_score_leg': 'int64', 'movement_score_heel': 'int64'})
        print(features.dtypes)
        print(features.describe())

        features.to_csv('data/features{}.csv'.format(i),index_label=False)