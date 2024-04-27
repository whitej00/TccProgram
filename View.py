import numpy as np
import math

from Model import ModelFrame
from scipy import interpolate


class Pipeline:
    def __init__(self):
        self.model = ModelFrame()
        self.df = self.model.get_dataframe()

    def set_inrush_damage_load(self, value_dict):
        self.current = (value_dict['Capacity'] / value_dict['Voltage'])
        self.maxFaultCurrent = (self.current / value_dict['Impedence']) * 100 

        self.Inrush_x = [x*self.current for x in [25,12,8,6,3.9,3]]
        self.Inrush_y = [0.01, 0.1, 0.4, 1, 3.5, 10]
        self.Damage_x = [x*self.current for x in [40,35,25,10,5]]
        
        self.Damage_y = [0.78, 1.02, 2.0, 12.50, 50]
        self.Load_x = [x*self.current for x in [1.56, 1.56]]
        self.Load_y = [1000,0.01]

    def get_base_data(self, value_dict):
        self.set_inrush_damage_load(value_dict)

        values = {
            'current':self.current,'maxFaultCurrent':self.maxFaultCurrent,
            'Inrush_x':self.Inrush_x,'Inrush_y':self.Inrush_y,
            'Damage_x':self.Damage_x,'Damage_y':self.Damage_y,
            'Load_x':self.Load_x,'Load_y':self.Load_y,
            }
        return values
    
    # def get_manual_data(self):
    #     values = (
    #         self.df[self.df['device'] == 'FUSE']['model'].unique(),
    #         self.df[self.df['device'] == 'NFUSE']['model'].unique(),
    #         self.df[self.df['model'] == 'STP']['modelnumber'].unique(),
    #         self.df[self.df['model'] == 'BON']['modelnumber'].unique(),
    #         self.df[self.df['model'] == 'CL']['modelnumber'].unique(),
    #     )
    #     return values

    def get_manual_data(self):
        FUSE_list = self.df[self.df['device'] == 'FUSE']['model'].unique()
        NFUSE_list = self.df[self.df['device'] == 'NFUSE']['model'].unique()
        values = {
            'FUSE_list': FUSE_list,
            'NFUSE_list': NFUSE_list,
        }
        for fuse in FUSE_list:
            values[f'{fuse}'] = self.df[self.df['model'] == f'{fuse}']['modelnumber'].unique(),
        for nfuse in NFUSE_list:
            values[f'{nfuse}'] = self.df[self.df['model'] == f'{nfuse}']['modelnumber'].unique(),
        return values
    
    def get_auto_data(self, value_dict):
        self.set_inrush_damage_load(value_dict)

        return self.get_satisfied_model()
    
    def get_model_coord(self, model, modelnumber):
        fuse = self.df[(self.df['model'] == model) &
                            (self.df['modelnumber'] == modelnumber)]
        values = {
            'x1':fuse['x1'].tolist()[0],'y1':fuse['y1'].tolist()[0],
            'x2':fuse['x2'].tolist()[0],'y2':fuse['y2'].tolist()[0],
            'Damage_x':self.Damage_x,'Damage_y':self.Damage_y,
            'Load_x':self.Load_x,'Load_y':self.Load_y,
            }
        return values

    def get_device(self, device):
        return self.df[(self.df['device'] == device)]


    # 조건 충족 model(BON, STP)의 modelnumber 반환
    def get_satisfied_model(self):
        satisfied_model_dict = {}
        nfuse_list = self.get_device('NFUSE')
        fuse_list = self.get_device('FUSE')
        for i in fuse_list.index:         
            for j in nfuse_list.index:
                fuse = fuse_list.loc[i]
                nfuse = nfuse_list.loc[j] 

                is_eveloped = self.evelope_validator(
                        self.Inrush_x, self.Inrush_y, self.Damage_x, self.Damage_y, 
                        fuse['x1'], fuse['y1'], fuse['x2'], fuse['y2']
                        )
                is_crossovered = self.crossdot_validator(
                        nfuse['x1'], nfuse['y1'], fuse['x2'], fuse['y2']
                        )
                if (is_eveloped and is_crossovered):
                    satisfied_model_dict[f"{fuse['modelnumber']} & {nfuse['modelnumber']}"] = {
                        'model': fuse['model'], 'modelnumber' : fuse['modelnumber'],
                        'nmodel': nfuse['model'], 'nmodelnumber' : nfuse['modelnumber'],
                        }
        return satisfied_model_dict

    # Damage와 Inrush 사이에 있는지 확인
    def evelope_validator(self, Inrush_x, Inrush_y, Damage_x, Damage_y, fuse_x_1, fuse_y_1, fuse_x_2, fuse_y_2):
        flag = True
        if self.is_overed(Damage_x, Damage_y, fuse_x_1, fuse_y_1, "up") or \
            self.is_overed(Damage_x, Damage_y, fuse_x_2, fuse_y_2, "up"):
            # print("Damage : above")
            flag = False
            return flag
        if self.is_overed(Inrush_x, Inrush_y, fuse_x_1, fuse_y_1, "down") or \
            self.is_overed(Inrush_x, Inrush_y, fuse_x_2, fuse_y_2, "down"):
            # print("Inrush : under")
            flag = False
            return flag

        return flag

    # 좌표 로그화 및 선형보간법 적용
    def is_overed(self, curve_x, curve_y, fuse_x, fuse_y, clock):
        log_fuse_x = [ ]
        log_fuse_y = [ ]
        log_curve_x = [ ]
        log_curve_y = [ ]
        for idx in range(0, len(fuse_x)-1):
            tmpx = np.logspace(math.log10(fuse_x[idx]), math.log10(fuse_x[idx+1]), 100)
            log_fuse_x.extend(tmpx)
            tmpy = np.logspace(math.log10(fuse_y[idx]), math.log10(fuse_y[idx+1]), 100)
            log_fuse_y.extend(tmpy)
        for idx in range(0, len(curve_x)-1):
            tmpx = np.logspace(math.log10(curve_x[idx]), math.log10(curve_x[idx+1]), 100)
            log_curve_x.extend(tmpx)
            tmpy = np.logspace(math.log10(curve_y[idx]), math.log10(curve_y[idx+1]), 100)
            log_curve_y.extend(tmpy)
        
        func = interpolate.interp1d(log_fuse_x, log_fuse_y, fill_value="extrapolate")
        tmpy = func(log_curve_x)
        
        if (clock=="up"):
            if(np.any(tmpy > log_curve_y)):
                return True
        elif (clock=="down"):
            if(np.any(tmpy < log_curve_y)):
                return True
        return False

    def get_crosspt(self, x11,y11, x12,y12, x21,y21, x22,y22):
        if x12==x11 or x22==x21:
            if x12==x11:
                cx = x12
                return cx
            if x22==x21:
                cx = x22
                return cx

        m1 = (y12 - y11) / (x12 - x11)
        m2 = (y22 - y21) / (x22 - x21)
        if m1==m2:
            return None

        cx = (x11 * m1 - y11 - x21 * m2 + y21) / (m1 - m2)
        return cx


    def crossdot_validator(self, cl_x_1, cl_y_1, fuse_x_2, fuse_y_2):  
        # tmpx = np.logspace(math.log10(x1), math.log10(x2), 10000)
        # tmpy = np.logspace(math.log10(y1), math.log10(y2), 10000)
        for i in range(0, len(cl_x_1)-1):
            for j in range(0, len(fuse_x_2)-1):   
                x1, x2 = 0, 0
                if (cl_x_1[i] < fuse_x_2[j]): x1 = fuse_x_2[j]
                else: x1 = cl_x_1[i]
                if (cl_x_1[i+1] < fuse_x_2[j+1]): x2 = cl_x_1[i+1]
                else: x2 = fuse_x_2[j+1]

                cx = self.get_crosspt(cl_x_1[i], cl_y_1[i], cl_x_1[i+1], cl_y_1[i+1], \
                                        fuse_x_2[j], fuse_y_2[j], fuse_x_2[j+1], fuse_y_2[j+1])
                if (cx and cx >= x1 and cx <= x2):
                    if (cx > self.maxFaultCurrent):
                        # print("crossDot o")
                        return True
                    else:
                        # print("crossDot x")
                        return False
        
        return False