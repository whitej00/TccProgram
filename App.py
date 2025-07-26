import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf 
import os, sys, time

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from View import Pipeline


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Fuse Validation")
        self.geometry("1000x900+0+0")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.custom_exit)

        self.container_left=tk.Frame(self, width=350, height=900)
        self.container_left.pack(side="left", fill="both", expand=True)
        
        self.container_right=tk.Frame(self, width=650, height=900)
        self.container_right.pack(side="right", fill="both", expand=False)

        self.input_pad = InputFrame(self.container_left)
        self.input_pad.place(x=100, y=100)

    def custom_exit(self):
        plt.close()
        self.destroy()

    def setSelectorFrame(self):
        self.mode_select_pad = ModeSelectFrame(self.container_left)
        self.mode_select_pad.place(x=100, y=330)

        self.pdf_pad = PdfFrame(self.container_left)
        self.pdf_pad.place(x=100, y=480)

    def setErrorFrame(self, voltage):
        # 오류 메시지 Frame 생성
        self.error_frame = tk.Frame(self.container_left, width=200, height=200, relief="raised", bd=4)
        self.error_frame.place(x=100, y=330)

        error_text = f"Rated voltage\n less than\n 13.2 KV available!!\n\nYour Voltage {voltage:.1f} kV"

        tk.Label(
            self.error_frame,
            font=('Arial', 10),
            text=error_text,
            foreground='red',
            justify="center",
            padx=36, pady=20
        ).pack()

# capacity, voltage, impedence, phase 입력
class InputFrame(tk.Frame):
    def __init__(self, container):
        super().__init__(container)
        self.configure(width=200, height=200, relief="raised", bd=4)
        self.input_block_dict = {}

        name_list = ['Capacity', 'Voltage', 'Impedence']
        value_list = [75.0, 22.9, 4.0]
        # value_list = [500.0, 12.2, 4.0]
        for name, value in zip(name_list, value_list):
            input_block = self.create_text_input_frame(name, value)
            input_block.pack()
            self.input_block_dict[name] = input_block

        input_block = self.create_option_menu_frame()
        self.input_block_dict['Phase'] = input_block

    def create_text_input_frame(self, name, value):
        input_block=tk.Frame(self, relief="solid", padx=5, pady=5)

        if name == "Capacity":
            name += " (Kva)"
        if name == "Voltage":
            name += " (Kv)\n(Line To Line)"
        if name == "Impedence":
            name += " (%)"
        label=tk.Label(input_block, text=name, width=13, height=2, fg="red", relief="sunken", border=3)
        label.pack(side="left")

        text=tk.Text(input_block, width=12, height=2, relief="sunken", border=3)
        text.insert(tk.END, value)
        text.pack(side="left")

        def on_text_change(event):
            text.edit_modified(False)
            try:
                float(text.get(1.0, "end").strip())  # 숫자 변환 확인
                self.create_bottom_select_frame(None)
            except ValueError:
                pass  # 숫자가 아닐 때는 무시

        text.bind("<<Modified>>", on_text_change)

        return input_block
    
    def create_option_menu_frame(self):
        phase_list = ["1 Phase", "3 Phase Y", "3 Phase Delta"]
        input_block=tk.Frame(self, relief="solid", width=10, height=2, padx=5, pady=5)

        model_option = tk.StringVar(input_block)
        model_option.set(phase_list[0])
        model_option.trace(
            "w", 
            lambda name, index, mode : 
            self.create_bottom_select_frame(model_option)
        )

        model_option_menu = tk.OptionMenu(input_block, model_option, *phase_list)
        model_option_menu.pack(side="left")

        input_block.pack()
        return model_option
    
    def create_bottom_select_frame(self, model_option):
        if hasattr(app, 'mode_select_pad') and app.mode_select_pad.winfo_exists():
            app.mode_select_pad.destroy()

        if hasattr(app, 'pdf_pad') and app.pdf_pad.winfo_exists():
            app.pdf_pad.destroy()

        if hasattr(app, 'error_frame') and app.error_frame.winfo_exists():
            app.error_frame.destroy()

        value_dict = self.get_inputframe_data_dict()

        if(value_dict['Voltage'] > 13.2):
            app.setErrorFrame(value_dict['Voltage'])
        else:
            app.setSelectorFrame()

    def inputframe_data_preprocessing(self, inputFrame_data_dict):
        phase = inputFrame_data_dict["Phase"]
        inputFrame_data_dict["OriginCapacity"] = inputFrame_data_dict["Capacity"]
        
        if phase == "1 Phase":
            inputFrame_data_dict["Current"] = inputFrame_data_dict["Capacity"] / inputFrame_data_dict["Voltage"]   
        elif phase == "3 Phase Y":
            inputFrame_data_dict["Current"] = inputFrame_data_dict["Capacity"] / inputFrame_data_dict["Voltage"] / 3
            inputFrame_data_dict["Voltage"] /= (3 ** (1.0/2.0))
        elif phase == "3 Phase Delta":
            inputFrame_data_dict["Current"] = inputFrame_data_dict["Capacity"] / inputFrame_data_dict["Voltage"] / (3 ** (1.0/2.0))
            pass
        
        return inputFrame_data_dict

    def get_inputframe_data_dict(self):
        name_list = ['Capacity', 'Voltage', 'Impedence']
        inputFrame_data_dict = {}
        for name in name_list:
            input_block_text = self.input_block_dict[name].winfo_children()[1]
            inputFrame_data_dict[name] = float(input_block_text.get(1.0, 1.9))

        phase_block_text = self.input_block_dict['Phase']
        inputFrame_data_dict['Phase'] = phase_block_text.get()

        inputFrame_data_dict = self.inputframe_data_preprocessing(inputFrame_data_dict)
        return inputFrame_data_dict


# top frame - mode(manual, auto)를 선택하는 button 두 개
# bottom frame - mode에 따라 출력 되는 optionmenu
class ModeSelectFrame(tk.Frame):
    def __init__(self, container):
        super().__init__(container)
        self.configure(width=200, height=200, relief="raised", bd=4, padx=4, pady=4)

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side='top')
        self.model_list_frame = tk.Frame(self)
        self.model_list_frame.pack(side='bottom')

        self.create_select_button('MANUAL')
        self.create_select_button('AUTO')

    # mode(manual, auto)를 선택하면 mode별로 매치되는 show_menu() 호출
    def show_option_menu_by_mode(self, mode):
        if (mode == 'MANUAL'):
            select_container = ManualModelSelectContainer(self.model_list_frame)
            select_container.show_menu()
        elif (mode == 'AUTO'):
            select_container = AutoModelSelectContainer(self.model_list_frame)
            select_container.show_menu()
    
    # mode(manual, auto)를 선택하는 button을 만드는 함수.
    def create_select_button(self, name):
        button = tk.Button(
                        self.button_frame, text=name, 
                        width=12, height=1, fg="red", relief="raised", overrelief = "sunken", border=3, 
                        command = lambda: self.show_option_menu_by_mode(name), 
                        repeatdelay=500, repeatinterval=100
                        )
        button.pack(side='left')
    

# manual mode 를 선택 시, 생성되는 클래스 (model을 직접 선택)
class ManualModelSelectContainer():
    def __init__(self, parent):
        self.parent = parent
        ## 이전에 생성된 모델옵션메뉴를 제거
        child_list = self.parent.winfo_children()
        for child in child_list:
            child.destroy()

    # optionmenu 초기 함수
    def show_menu(self):
        self.manual_data_dict = pipeline.get_manual_data()

        self.model_frame=tk.Frame(self.parent, relief="solid", padx=4, pady=4)
        self.model_frame.pack(side='top')
        self.showModelList(self.model_frame, self.manual_data_dict['FUSE_list'], 'model')

        self.nmodel_frame=tk.Frame(self.parent, relief="solid", padx=4, pady=4)
        self.nmodel_frame.pack(side='bottom')
        self.showModelList(self.nmodel_frame, self.manual_data_dict['NFUSE_list'], 'nmodel')
    
    # model종류(model, nmodel)에 대응되는 optionmenu 생성
    def showModelList(self, parent_frame, model_list, device):
        model_option = tk.StringVar(parent_frame)
        model_option.set(model_list[0])
        model_option.trace(
            "w", 
            lambda name, index, mode : 
            self.show_modelnumber_list(parent_frame, model_option, device)
        )

        model_option_menu = tk.OptionMenu(parent_frame, model_option, *model_list)
        model_option_menu.pack(side="left")

        if(device=='model'):
            self.model_instance= model_option
        elif(device=='nmodel'):
            self.nmodel_instance= model_option

        self.show_modelnumber_list(parent_frame, model_option, device)

    # 선택된 model(model - STP, BON.. / nmode - CL)에 대응되는 modelnumber(TR012..) 선택 optionmenu
    def show_modelnumber_list(self, parent_frame, model_option, device, *args):
        child_list = parent_frame.winfo_children()
        if (len(child_list) > 1):
            child_list[1].destroy()

        fuse_model = model_option.get()
        fuse_modelnumber_list = self.manual_data_dict[fuse_model][0]
        
        modelnumber_option = tk.StringVar(parent_frame)
        modelnumber_option.set(fuse_modelnumber_list[0])
        modelnumber_option.trace('w', self.draw_matplotlib)

        modelnumber_option_menu = tk.OptionMenu(parent_frame, modelnumber_option, *fuse_modelnumber_list)
        modelnumber_option_menu.pack(side='left')

        if(device=='model'):
            self.modelnumber_instance= modelnumber_option
        elif(device=='nmodel'):
            self.nmodelnumber_instance= modelnumber_option

    # 입력된 데이터와, 선택한 model에 따라 matplotlib 실행
    def draw_matplotlib(self, *args):
        frameChildL = app.container_right.winfo_children()
        if len(frameChildL):
            frameChildL[0].destroy()

        value_dict = app.input_pad.get_inputframe_data_dict()
        modelname = self.model_instance.get()
        modelnumber = self.modelnumber_instance.get()
        nmodelname = self.nmodel_instance.get()
        nmodelnumber = self.nmodelnumber_instance.get()

        base_data = pipeline.get_base_data(value_dict)
        fuse_data = pipeline.get_model_coord(modelname, modelnumber)
        nfuse_data = pipeline.get_model_coord(nmodelname, nmodelnumber)

        mat.drawing(value_dict, modelnumber, nmodelnumber, base_data, fuse_data, nfuse_data)

        canvas = FigureCanvasTkAgg(mat.fig, master=app.container_right)
        canvas.draw()
        canvas.get_tk_widget().pack()
        

# auto mode 를 선택 시, 생성되는 클래스 
# TCC 조건 - 
# (TCC 조건을 충족하는 model 선별하여 출력)      
class AutoModelSelectContainer():
    def __init__(self, parent):
        self.parent = parent
        child_list = self.parent.winfo_children()
        for child in child_list:
            child.destroy()

    # optionmenu 초기함수
    def show_menu(self):
        self.value_dict = app.input_pad.get_inputframe_data_dict()
        self.FUSE_NFUSE_dict = pipeline.get_auto_data(self.value_dict)

        self.model_frame=tk.Frame(self.parent, relief="solid", padx=4, pady=4)
        self.model_frame.pack(side='top')
        self.show_modelnumber_list(self.model_frame)

    # TCC조건 충족하는 modenumber optionmenu 생성
    def show_modelnumber_list(self, parent_frame):
        child_list = app.container_right.winfo_children()
        for child in child_list:
            child.destroy()

        if (self.FUSE_NFUSE_dict):
            fuse_nfuse_dict_key_list = list(self.FUSE_NFUSE_dict.keys())
            self.modelnumber_option = tk.StringVar(parent_frame)
            self.modelnumber_option.set(fuse_nfuse_dict_key_list[0])
            self.modelnumber_option.trace('w', self.draw_matplotlib)
            self.modelnumber_option_menu = tk.OptionMenu(parent_frame, self.modelnumber_option, *fuse_nfuse_dict_key_list)
            self.modelnumber_option_menu.pack(side='left')
            self.draw_matplotlib()
        else:
            tk.Label(app.container_right, 
                     font=('Arial', 17),
                     text="No suitable protection was found",
                     foreground='red',
                     padx=300, pady=500
                     ).pack()

    # 입력된 데이터와, 선택한 model에 따라 matplotlib 실행
    def draw_matplotlib(self, *args):
        frameChildL = app.container_right.winfo_children()
        for child in frameChildL:
            child.destroy()
        
        fuse_nfuse_dict = self.FUSE_NFUSE_dict[self.modelnumber_option.get()]

        value_dict = app.input_pad.get_inputframe_data_dict()
        modelname = fuse_nfuse_dict['model']
        modelnumber = fuse_nfuse_dict['modelnumber']
        nmodelname = fuse_nfuse_dict['nmodel']
        nmodelnumber = fuse_nfuse_dict['nmodelnumber']

        base_data = pipeline.get_base_data(value_dict)
        fuse_data = pipeline.get_model_coord(modelname, modelnumber)
        nfuse_data = pipeline.get_model_coord(nmodelname, nmodelnumber)

        # print(f'{modelname} -> {modelnumber}')
        # print(f'{nmodelname} -> {nmodelnumber}')

        mat.drawing(value_dict, modelnumber, nmodelnumber, base_data, fuse_data, nfuse_data)

        canvas = FigureCanvasTkAgg(mat.fig, master=app.container_right)
        canvas.draw()
        canvas.get_tk_widget().pack()


# matplotlib pdf를 출력
class PdfFrame(tk.Frame):
    def __init__(self, container):
        super().__init__(container)
        self.configure(width=200, height=200)

        pdf_frame=tk.Frame(self, relief="raised", bd=4)
        button_pdf = tk.Button(
                                pdf_frame, text="GET PDF!!", 
                                width=27, height=2, fg="red", relief="raised", overrelief = "sunken", border=3, 
                                command=mat.save_as_pdf, repeatdelay=500, repeatinterval=100
                                )
        button_pdf.pack(side="left")
        pdf_frame.pack()


# matplotlib class
class MatplotlibClass:
    def drawing(self, value_dict, modelnumber, nmodelnumber, base_data, fuse_data, nfuse_data):
        plt.close()
        self.fig = plt.figure(figsize=(6,10))
        ax = self.fig.add_subplot(1,1,1)
        ax.set(xlim=[1,10000], ylim=[0.01, 1000], xscale="log", yscale="log")
        ax.tick_params(labelsize=7)
        ax.plot(base_data['Inrush_x'], base_data['Inrush_y'], color="red", linewidth=1)
        ax.plot(base_data['Damage_x'], base_data['Damage_y'], '-',color="red", linewidth=1)
        ax.plot(fuse_data['x1'], fuse_data['y1'], '-',color="black", linewidth=1)
        ax.plot(fuse_data['x2'], fuse_data['y2'],'-',color="black", linewidth=1)
        ax.plot(nfuse_data['x1'], nfuse_data['y1'], '--', color="dodgerblue", linewidth=1)
        ax.plot(nfuse_data['x2'], nfuse_data['y2'], '--', color="yellowgreen", linewidth=1)
        ax.axvline(base_data['maxFaultCurrent'], 0, 1, color="gold", linewidth=1)
        ax.grid(True, which="both")
        self.ax = ax

        self.title = f"{value_dict['OriginCapacity']:.1f}kVA {value_dict['Voltage']:.1f}kV {value_dict['Phase']} TCC Curve"
        ax.set(title=self.title)

        capacityText = f"Capacity : {value_dict['OriginCapacity']:.1f}kVA"
        voltageText = f"Voltage : {value_dict['Voltage']:.1f}kV"
        impedenceText = f"Z% : {value_dict['Impedence']:.1f}%"
        self.footTitle = f"{capacityText:40}{modelnumber:<30}{impedenceText:<20}\n{voltageText:<40}{nmodelnumber:<30}"

        plt.xlabel(self.footTitle , horizontalalignment='left', x = 0)

        plt.annotate(f"{modelnumber} \n MIN MELT CURVE", size=6,
                    xy=(fuse_data['x1'][1], fuse_data['y1'][1]),
                    xytext=(1, fuse_data['y1'][1] * 1.5),
                    arrowprops=dict(arrowstyle=']->', color='gray', connectionstyle='arc, angleA=0, angleB=0, armA=80, armB=0, rad=0'),
                    backgroundcolor="khaki"
                    )
        plt.annotate(f"{modelnumber} \n TOTAL CLEAR CURVE", size=6,
                    xy=(fuse_data['x2'][2], fuse_data['y2'][2]),
                    xytext=(1, fuse_data['y2'][2] * 1.5),
                    arrowprops=dict(arrowstyle=']->', color='gray', connectionstyle='arc, angleA=0, angleB=0, armA=80, armB=0, rad=0'),
                    backgroundcolor="lightyellow"
                    )
        plt.annotate(f"{nmodelnumber} \n MIN MELT CURVE", size=6,
                    xy=(nfuse_data['x1'][1], nfuse_data['y1'][1]),
                    xytext=(nfuse_data['x1'][1] * 3, nfuse_data['y1'][1] * 1.5),
                    arrowprops=dict(arrowstyle=']->', color='gray', connectionstyle='arc, angleA=180, angleB=0, armA=70, armB=0, rad=0'),
                    backgroundcolor="bisque",
                    )
        plt.annotate(f"{nmodelnumber} \n TOTAL CLEAR CURVE", size=6,
                    xy=(nfuse_data['x2'][1], nfuse_data['y2'][1]),
                    xytext=(nfuse_data['x2'][1] * 3, nfuse_data['y2'][1] * 0.5),
                    arrowprops=dict(arrowstyle=']->', color='gray', connectionstyle='arc, angleA=180, angleB=0, armA=70, armB=0, rad=0'),
                    backgroundcolor="goldenrod",
                    )
        plt.annotate('COLDLOAD & \n INRUSH CURRENT CURVE', size=6,
                    xy=(base_data['Inrush_x'][-1], base_data['Inrush_y'][-1]),
                    xytext=(1.0, base_data['Inrush_x'][-1] * 1.5),
                    arrowprops=dict(arrowstyle=']->', color='gray', connectionstyle='arc, angleA=0, angleB=0, armA=80, armB=0, rad=0'),
                    backgroundcolor="honeydew",
                    )
        plt.annotate('DAMAGE CURVE', size=6,
                    xy=(base_data['Damage_x'][-1], base_data['Damage_y'][-1]),
                    xytext=(base_data['Damage_x'][-1] * 3, base_data['Damage_y'][-1] / 2),
                    arrowprops=dict(arrowstyle=']->', color='gray', connectionstyle='arc, angleA=180, angleB=0, armA=50, armB=0, rad=0'),
                    backgroundcolor="honeydew",
                    )
        plt.annotate('MAX SECOND FAULT CURRENT', size=6,
                    xy=(base_data['maxFaultCurrent'], 100),
                    xytext=(base_data['maxFaultCurrent'] * 3, 100),
                    arrowprops=dict(arrowstyle=']->', color='gray', connectionstyle='arc, angleA=180, angleB=0, armA=30, armB=0, rad=0'),
                    backgroundcolor="honeydew",
                    )
        return ax

    def save_as_pdf(self):
        dir =  os.path.dirname(sys.argv[0])
        plt.savefig(f"{dir}/{self.title}.pdf")



if __name__ == "__main__":
    pipeline = Pipeline()
    mat = MatplotlibClass()

    app = App()
    app.mainloop()