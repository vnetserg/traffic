#!/usr/bin/python3.4
# -*- coding: utf-8 -*-

import argparse

import pandas as ps
import numpy as np
from sklearn.metrics import classification_report
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder, scale
from sklearn.cross_validation import KFold
from sklearn.metrics import classification_report

generalized_apps = {
    "HTTP.text": "HTML.text/image",
    "HTTP.image": "HTML.text/image",
    "DNS": "DNS",
    "BitTorrent": "BitTorrent",
    "HTTP.audio": "HTML.multimedia",
    "HTTP.video": "HTML.multimedia",
    "Quic.multimedia": "Quic",
    "Skype.realtime": "Skype",
}

def preprocess(data, seed=None):
    '''
    n_samples = min(len(data[data["class"] == clsval])
        for clsval in data["class"].unique())
    data = data.iloc[np.random.permutation(len(data))]
    new_data = None
    for clsval in data["class"].unique():
        if new_data is None:
            new_data = data[data["class"] == clsval][:n_samples]
        else:
            new_data = ps.concat([new_data,
                data[data["class"] == clsval][:n_samples]])
    '''

    X = scale(data.drop(["class"], axis=1))
    le = LabelEncoder()
    y = le.fit_transform(data["class"])
    return X, y, le

def do_crossval(data, seed=None):
    X, y, label_encoder = preprocess(data)
    model = SVC(C=0.05, kernel='poly', degree=7, random_state=seed)
    for train_index, test_index in KFold(len(X), 2, shuffle=True, random_state=seed):
        X_train, y_train = X[train_index], y[train_index]
        X_test, y_test = X[test_index], y[test_index]
        model.fit(X_train, y_train)
        y_predicted = model.predict(X_test)
        report = classification_report(label_encoder.inverse_transform(y_test),
            label_encoder.inverse_transform(y_predicted))
        print(report, "\n")

def do_test(data, seed=None):
    pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--crossval", help="do cross-validation", metavar="FILE")
    parser.add_argument("-t", "--test", help="test different models", metavar="FILE")
    parser.add_argument("-a", "--apps", help="classify applications", action="store_true")
    parser.add_argument("-r", "--random", help="random number fenerator seed", metavar="SEED", type=int)
    args = parser.parse_args()
    if not args.crossval and not args.test:
        return print("No switch provided (-c or -t)")
    data = ps.read_csv(args.crossval or args.test)
    if args.apps:
        data["class"] = [generalized_apps[row["app"]]
                           for _, row in data.iterrows()]
    data = data.drop(["app", "name"], axis=1)
    if args.crossval:
        do_crossval(data, args.random)
    elif args.test:
        do_test(data, args.random)

if __name__ == "__main__":
    main()