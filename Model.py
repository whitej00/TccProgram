import os
import sys
import pandas as pd
import numpy as np


class ModelFrame:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            # PyInstaller로 빌드된 실행 파일일 경우
            base_path = sys._MEIPASS
        else:
            # 로컬에서 직접 실행할 경우 (예: App.py)
            base_path = os.path.dirname(os.path.abspath(__file__))

        excel_path = os.path.join(base_path, "test.xlsx")
        self.df = pd.read_excel(excel_path, engine="openpyxl").dropna()
        self.preprocessing()

    def get_dataframe(self):
        return self.df

    def preprocessing(self):
        for idx in self.df.index:
            data = self.df.loc[idx]    
            data['x1'] = list(map(float, data['x1'].split(',')))
            data['y1'] = list(map(float, data['y1'].split(',')))
            data['x2'] = list(map(float, data['x2'].split(',')))
            data['y2'] = list(map(float, data['y2'].split(',')))
            if (data['x1'][0] > data['x1'][1]):  
                data['x1'].reverse()
                data['y1'].reverse()
            if (data['x2'][0] > data['x2'][1]):
                data['x2'].reverse()
                data['y2'].reverse()

class ModelPipeline(ModelFrame):
    def setNFuseModel(self, nmodel, nmodelNumber):
        self.nmodel = nmodel
        self.nmodelNumber = nmodelNumber

    def getModelCoord(self, model, modelNumber):
        fuse = self.df[(self.df['model'] == model) &
                            (self.df['modelnumber'] == modelNumber)]
        return fuse['x1'].tolist()[0], fuse['y1'].tolist()[0], \
                fuse['x2'].tolist()[0], fuse['y2'].tolist()[0]

    def getModel(self, model):
        return self.df[(self.df['model'] == model)]
    
    def getModelList(self):
        return self.df[self.df['device'] == 'FUSE']['model'].unique()

    def getNModelList(self):
        return self.df[self.df['device'] == 'NFUSE']['model'].unique()

    def getBONList(self):
        return self.df[self.df['model'] == 'BON']['modelnumber'].unique()

    def getSTPList(self):
        return self.df[self.df['model'] == 'STP']['modelnumber'].unique()

    def getCLList(self):
        return self.df[self.df['model'] == 'CL']['modelnumber'].unique()
