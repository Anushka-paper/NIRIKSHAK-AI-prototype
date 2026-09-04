import pandas as pd
from prophet import Prophet
import joblib
import os

class ExpenditureForecaster:
    def __init__(self):
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=0.05
        )

    def prepare_data(self, df: pd.DataFrame, date_col: str, amount_col: str) -> pd.DataFrame:
        """Aggregates data monthly for Prophet (requires 'ds' and 'y' columns)"""
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        monthly_df = df.resample('M', on=date_col)[amount_col].sum().reset_index()
        monthly_df.columns = ['ds', 'y']
        return monthly_df

    def train(self, df: pd.DataFrame):
        """Train the Prophet model"""
        print("Training Prophet forecasting model...")
        self.model.fit(df)

    def forecast(self, periods: int = 6) -> pd.DataFrame:
        """Forecast future expenditure for the specified number of months"""
        future = self.model.make_future_dataframe(periods=periods, freq='M')
        forecast = self.model.predict(future)
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    def save(self, filepath: str):
        """Save the model using joblib"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)
        print(f"Forecasting model saved to {filepath}")

    @classmethod
    def load(cls, filepath: str):
        """Load the model using joblib"""
        return joblib.load(filepath)
