import math
import os
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import train_test_split


class WinnowAlgorithm:
    def __init__(self, X_train, threshold,alpha):
        self.weights = np.ones(X_train.shape[1])
        self.threshold = threshold
        self.alpha = alpha
    
      

    def fit(self, X, y):
         
        for index in range(X.shape[0]):
            row = X.iloc[index]
            prediction = np.dot(row, self.weights) >= self.threshold
            actual = y.iloc[index].item()
            
            for i in range(len(self.weights)):
                if actual == 1 and prediction == False:
                    # Promote the weight if the instance is positive and misclassified
                    self.weights[i] *= self.alpha
                elif actual == 0 and prediction == True:
                    # Demote the weight if the instance is negative and misclassified
                    self.weights[i] /= self.alpha
            print("Weights after fit:", self.weights)
          

    def predict(self, X):
        predictions = []
        print("Weights at start of predict:", self.weights)
        for index in range(X.shape[0]):
         row = X.iloc[index]
         '''''
         print("Row shape:", row.shape, "Weights shape:", self.weights.shape)  # Check shapes
         print("Row values:", row.values)  # Inspect row values
         print("Weights:", self.weights)  # Inspect weight values
         dot_product = np.dot(row, self.weights)
         print("result of row * weight is:", dot_product)
         '''''
         if np.dot(row, self.weights) >= self.threshold: 
                prediction = 1
         else:
                prediction = 0
         predictions.append(prediction)
        return predictions


def winnow (data_x, data_y):
    clf = RandomForestClassifier(random_state=42)
    clf.fit(data_x, data_y.values.ravel())

    importances = clf.feature_importances_
    k = 5  # Number of top features to select
    selector = SelectKBest(score_func=f_classif, k=k)
    X_new = selector.fit_transform(data_x, data_y.values.ravel())


    plt.figure(figsize=(10, 6))
    plt.bar(data_x.columns, importances)
    plt.xlabel('Features')
    plt.ylabel('Importance')
    plt.title('Feature Importances')
    plot_path=os.path.join('static', 'feature_importances.png')
    plt.savefig(plot_path)

    count_0= data_y.sum()
    count_1= len(data_y)-count_0

    X_train, X_test, y_train, y_test = train_test_split(data_x, data_y, test_size=0.2, random_state=42)

    winnow = WinnowAlgorithm( X_train, threshold=1.8,alpha=2)

    winnow.fit(X_train, y_train)
    predictions = winnow.predict(X_test)
    count_1_predictions = sum(predictions)
    count_0_predictions = len(predictions) - count_1_predictions
    print("count of 1s in the predictions: ", count_1_predictions)
    print("count of 0s in the predictions: ", count_0_predictions)
    predictions_np = np.array(predictions)
    correct_predictions = sum(predictions_np == y_test.to_numpy().flatten())
    total_predictions = len(y_test)
    accuracy = (correct_predictions / total_predictions)*100
    return count_0, count_1,count_0_predictions,count_1_predictions, accuracy,plot_path