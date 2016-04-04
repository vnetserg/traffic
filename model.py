#!/usr/bin/python3.4
# -*- coding: utf-8 -*-

import argparse, pickle

import pandas as ps
import numpy as np
from sklearn.metrics import classification_report
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cross_validation import KFold
from sklearn.metrics import classification_report, precision_recall_fscore_support

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

def get_data(file, apps=False, seed=None, drop_classes=False):
    data = ps.read_csv(file)
    if apps:
        data["class"] = data["app"]
    data = data.drop(["app", "name"] + (["class"] if drop_classes and "class" in data.columns else []), axis=1)
    if seed:
        np.random.seed(seed)
        data = data.iloc[np.random.permutation(len(data))]
    return data

def preprocess(data):
    scaler = StandardScaler()
    X = scaler.fit_transform(data.drop(["class"], axis=1))
    labeler = LabelEncoder()
    y = labeler.fit_transform(data["class"])
    return X, y, scaler, labeler

def fair_folds(data, n_folds, seed=None):
    class_indexes = {cls: data[data["class"] == cls].index.to_series() for cls in data["class"].unique()}
    folds = []
    for i in range(n_folds):
        fold_index = ps.Series()
        for cls, cls_index in class_indexes.items():
            cls_fold = cls_index.sample(frac=1/(n_folds-i), random_state=seed)
            class_indexes[cls] = cls_index[~cls_index.isin(cls_fold)]
            fold_index = ps.concat([fold_index, cls_fold])
        folds.append(fold_index)
    array = ps.Series(range(len(data)))
    for test_fold in folds:
        train_fold = array[~array.isin(test_fold)].as_matrix()
        test_fold = test_fold.as_matrix()
        yield train_fold, test_fold

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
    X, y, scaler, labeler = preprocess(data)

    #model = SVC(C=1.1, kernel='linear', random_state=seed)
    #model = KNeighborsClassifier(1, "uniform")
    model = RandomForestClassifier(42, "entropy", 6, random_state=seed)

    for train_index, test_index in fair_folds(data, 3, seed):
        X_train, y_train = X[train_index], y[train_index]
        X_test, y_test = X[test_index], y[test_index]
        model.fit(X_train, y_train)
        y_predicted = model.predict(X_test)
        true_labels = labeler.inverse_transform(y_test)
        predicted_labels = labeler.inverse_transform(y_predicted)
        report = classification_report(true_labels, predicted_labels)
        cross_report = cross_class_report(true_labels, predicted_labels)
        print("\n----- FOLD STATS -----")
        print(report, "\n", cross_report)

    cols = data.drop(["class"], axis=1).columns.to_series()
    imps = model.feature_importances_
    assert len(cols) == len(imps)
    print("\nFEATURE IMPORTANCES:")
    for imp, col in sorted(zip(imps, cols), reverse=True):
        print("{}: {}".format(col, imp))

def do_eval(data, seed=None):
    X, y, label_encoder = preprocess(data)
    models = all_models()
    for mdl in models:
        f1 = []
        for train_index, test_index in fair_folds(data, 3, seed):
            X_train, y_train = X[train_index], y[train_index]
            X_test, y_test = X[test_index], y[test_index]
            mdl["model"].fit(X_train, y_train)
            y_predicted = mdl["model"].predict(X_test)
            f1.append(precision_recall_fscore_support(y_test, y_predicted, average='macro')[2])
        mdl["f1"] = sum(f1)/len(f1)
        print("{}: {:.4f}".format(mdl["txt"], mdl["f1"]))

    best = max(models, key=lambda x: x["f1"])
    print("The best model is {} ({})".format(best["txt"], best["f1"]))

def train_model(data, seed=None):
    X, y, scaler, labeler = preprocess(data)
    model = RandomForestClassifier(42, "entropy", 6, random_state=seed)
    model.fit(X, y)
    return model, scaler, labeler

def do_prediction(data, model, scaler, labeler):
    X = scaler.transform(data)
    return labeler.inverse_transform(model.predict(X))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--train", help="train model on a specified file", metavar="FILE")
    parser.add_argument("-s", "--save", help="save trained model in a file", metavar="FILE")
    parser.add_argument("-l", "--load", help="load trained model from a file", metavar="FILE")
    parser.add_argument("-p", "--predict", help="predict classes for a file", nargs=2, metavar=("TESTFILE", "OUTFILE"))
    parser.add_argument("-c", "--crossval", help="do cross-validation", metavar="FILE")
    parser.add_argument("-e", "--evaluate", help="evaluate different models", metavar="FILE")
    parser.add_argument("-a", "--apps", help="classify applications", action="store_true")
    parser.add_argument("-r", "--random", help="random number generator seed", metavar="SEED", type=int)
    args = parser.parse_args()

    if args.crossval:
        return do_crossval(get_data(args.crossval, args.apps, args.random), args.random)
    elif args.evaluate:
        return do_eval(get_data(args.evaluate, args.apps, args.random), args.random)
    
    if args.train:
        data = get_data(args.train, args.apps, args.random)
        model, scaler, labeler = train_model(data, args.random)
    elif args.load:
        model, scaler, labeler = pickle.load(open(args.load, "rb"))
    else:
        return print("No action specified.")

    if args.save:
        pickle.dump((model, scaler, labeler), open(args.save, "wb"))

    if args.predict:
        testfile, outfile = args.predict
        test_data = get_data(testfile, args.apps, drop_classes=True)
        classes = do_prediction(test_data, model, scaler, labeler)
        new_data = ps.concat([test_data, ps.DataFrame({"class": classes})], axis=1)
        new_data.to_csv(outfile, index=None)

if __name__ == "__main__":
    main()