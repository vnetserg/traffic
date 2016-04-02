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
from sklearn.metrics import classification_report, precision_recall_fscore_support

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

def all_models(seed = None):
    '''
        Сгенерировать все возможные типы моделей.
        Аргументы:
            seed - семя генератора псевдослучайных чисел
        Возвращает: список моделей (не обученных)
    '''
    models = []
    for pen in ("l1", "l2"):
        for tol in range(1, 31):
            tol *= 0.01
            models.append({"model": LogisticRegression(penalty=pen, tol=tol, random_state=seed),
                "txt": "LogReg (pen: {}, tol: {})".format(pen, tol)})
    for C in range(1, 21):
        C *= 0.1
        for kernel in ('linear', 'poly', 'rbf', 'sigmoid'):
            models.append({"model": SVC(C=C, kernel=kernel, random_state=seed),
                "txt": "SVC (C: {}, kernel: {})".format(C, kernel)})
    for weights in ("uniform", "distance"):
        for n in range(1, 60, 3):
            models.append({"model": KNeighborsClassifier(n, weights),
                "txt": "KNeighbors (n: {}, wieghts: {})".format(n, weights)})
    for n in range(3, 61, 3):
        for depth in tuple(range(1, 8)) + (None,):
            for crit in ("gini", "entropy"):
                models.append({"model": RandomForestClassifier(n, crit, depth, random_state=seed),
                    "txt": "RFC (n: {}, crit: {}, depth: {})".format(
                        n, crit, depth)})
    return models

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

def cross_class_report(y, p):
    classes = np.unique(y)
    res = ps.DataFrame({"y": y, "p": p}, index=None)
    table = ps.DataFrame(index=classes, columns=classes)
    for true_cls in classes:
        tmp = res[res["y"] == true_cls]
        for pred_cls in classes:
            table[pred_cls][true_cls] = len(tmp[tmp["p"] == pred_cls])
    return table

def do_crossval(data, seed=None):
    X, y, label_encoder = preprocess(data, seed)
    model = SVC(C=1.1, kernel='linear', random_state=seed)
    for train_index, test_index in KFold(len(X), 3, shuffle=True, random_state=seed):
        X_train, y_train = X[train_index], y[train_index]
        X_test, y_test = X[test_index], y[test_index]
        model.fit(X_train, y_train)
        y_predicted = model.predict(X_test)
        true_labels = label_encoder.inverse_transform(y_test)
        predicted_labels = label_encoder.inverse_transform(y_predicted)
        report = classification_report(true_labels, predicted_labels)
        cross_report = cross_class_report(true_labels, predicted_labels)
        print("\n----- FOLD STATS -----")
        print(report, "\n", cross_report)

def do_test(data, seed=None):
    X, y, label_encoder = preprocess(data, seed)
    models = all_models()
    for mdl in models:
        f1 = []
        for train_index, test_index in KFold(len(X), 3, shuffle=True, random_state=seed):
            X_train, y_train = X[train_index], y[train_index]
            X_test, y_test = X[test_index], y[test_index]
            mdl["model"].fit(X_train, y_train)
            y_predicted = mdl["model"].predict(X_test)
            f1.append(precision_recall_fscore_support(y_test, y_predicted, average='macro')[2])
        mdl["f1"] = sum(f1)/len(f1)
        print("{}: {:.4f}".format(mdl["txt"], mdl["f1"]))

    best = max(models, key=lambda x: x["f1"])
    print("The best model is {} ({})".format(best["txt"], best["f1"]))

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