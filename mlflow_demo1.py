import warnings
import argparse
import logging
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import ElasticNet
import mlflow
import mlflow.sklearn
from urllib.parse import urlparse
import os

os.environ["MLFLOW_TRACKING_URI"]=""
os.environ["MLFLOW_TRACKING_USERNAME"]=""
os.environ["MLFLOW_TRACKING_PASSWORD"]=""


logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)

#get arguments from command
parser = argparse.ArgumentParser()
parser.add_argument("--alpha", type=float, required=False, default=0.65)
parser.add_argument("--l1_ratio", type=float, required=False, default=0.7)
args = parser.parse_args()

#evaluation function
def eval_metrics(actual, pred):
    rmse = np.sqrt(mean_squared_error(actual, pred))
    mae = mean_absolute_error(actual, pred)
    r2 = r2_score(actual, pred)
    return rmse, mae, r2


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    np.random.seed(40)

    # Read the wine-quality csv file from local
    data = pd.read_csv("red-wine-quality.csv")
    data.to_csv("data/red-wine-quality.csv", index=False)

    # Split the data into training and test sets. (0.75, 0.25) split.
    train, test = train_test_split(data)

    # The predicted column is "quality" which is a scalar from [3, 9]
    train_x = train.drop(["quality"], axis=1)
    test_x = test.drop(["quality"], axis=1)
    train_y = train[["quality"]]
    test_y = test[["quality"]]

    alpha = args.alpha
    l1_ratio = args.l1_ratio

    # # For remote server only (Dagshub)
    remote_server_uri = "https://dagshub.com/vinreena15/mlflow-dagshub-demo.mlflow"
    mlflow.set_tracking_uri(remote_server_uri)
    #exp = mlflow.set_experiment(experiment_name='exp_for_remote_uri_demo')

    #mlflow.set_tracking_uri(uri="./mytracks")
    #exp = mlflow.set_experiment(experiment_name='exp_for_uri_demo')

    tracking_url_type_store = urlparse(mlflow.get_tracking_uri()).scheme

    with mlflow.start_run():
            
        lr = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=42)
        lr.fit(train_x, train_y)

        predicted_qualities = lr.predict(test_x)

        (rmse, mae, r2) = eval_metrics(test_y, predicted_qualities)

        print("Elasticnet model (alpha={:f}, l1_ratio={:f}):".format(alpha, l1_ratio))
        print("  RMSE: %s" % rmse)
        print("  MAE: %s" % mae)
        print("  R2: %s" % r2)

        mlflow.log_param('alpha',alpha)
        mlflow.log_param('l1_ratio',l1_ratio)
        mlflow.log_metric('rmse',rmse)
        mlflow.log_metric('r2',r2)
        mlflow.log_metric('mae',mae)

        # Model registry does not work with file store
        if tracking_url_type_store != "file":
            # Register the model
            # There are other ways to use the Model Registry, which depends on the use case,
            # please refer to the doc for more information:
            # https://mlflow.org/docs/latest/model-registry.html#api-workflow
            mlflow.sklearn.log_model(
                lr, "model", registered_model_name="ElasticnetWineModel")
        else:
            #mlflow.sklearn.log_model(lr, "model")
            mlflow.sklearn.log_model(lr,'mymodel')


        
