import pandas as pd
import numpy as np

try:
    df = pd.read_csv("./rowdata/customer_chat_raw.csv")
except FileNotFoundError:
    print("文件不存在，跳过读取")


class AutoDataCleaner():
    def __init__(self, df):
        self.df = df
        self.col_missing_drop_threshold = 0.5
        self.iqr_scale = 1.5

    def handle_missing_value(self):
        cols_to_drop = []
        num_cols = []
        text_cols = []
        missing_rate = self.df.isnull().mean()
        for col, rate in missing_rate.item():
            if rate > self.col_missing_drop_threshold:
                print(f"{col:>15}{rate:>10}待删除")
                cols_to_drop.append(col)
            elif pd.api.types.is_numeric_dtype(df[col]):
                print(f"{col:>15}{rate:>10}用该列中位数填充")
                num_cols.append(col)
            else:
                print(f"{col:>15}{rate:>10}用‘未知/未填写’填充")
                text_cols.append(col)
        self.df = self.df.drop(columns=cols_to_drop)
        self.df[num_cols] = self.df[num_cols].fillna(df[num_cols].median())
        self.df[text_cols] = self.df[text_cols].fillna('未知/未填写')
        '''
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
        else:
            df[col] = df[col].fillna('未知/未填写')
        '''
        return self.df

    def handle_outlier(self, mode="clip"):
        num_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        for col in num_cols:
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            low = Q1 - self.iqr_scale * IQR
            high = Q3 + self.iqr_scale * IQR
            if mode == "clip":
                self.df[col] = self.df[col].clip(lower=low, upper=high)
            elif mode == "drop":
                self.df = self.df[(self.df[col] >= low) & (self.df[col] <= high)]




    def run_full_clean(self, ouotlier_mode="clip"):
        pass

