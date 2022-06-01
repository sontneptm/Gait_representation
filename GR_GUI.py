import time
import sys
from PyQt5.QtCore import QDate, QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import *
from PyQt5 import uic
from multiprocessing import Process, Queue
from threading import Thread

# Main to GUI command
CONN_STATUS = 3000
SHOW_DATA = 3001
SAVE_DATA = 3002
PLOT_DATA = 3003

# GUI to Main command
REQUEST_CONN = 2000
REQUEST_DISCONN = 2001
REQUEST_DISPLAY = 2002
REQUEST_SAVE = 2003
REQUEST_PLOT = 2004
REQUEST_EXIT = 2010

form_class = uic.loadUiType('.\gait_representation.ui')[0]


class SignalManager(QObject):
    stat_update_signal = pyqtSignal()
    sys_msg_update_signal = pyqtSignal()

    def run(self):
        self.stat_update_signal.emit()
        self.sys_msg_update_signal.emit()

class MsdlWindow(QDialog, form_class):
    def __init__(self, m2g_queue=Queue(), g2m_queue=Queue()):
        super().__init__()
        self.setupUi(self)
        self.is_closed = False
        self.m2g_queue = m2g_queue
        self.g2m_queue = g2m_queue
        self.device_cursor=-1
        self.sensor_cursor=-1
        self.save_data_size = 100
        # if you change save_data_size
        # you should change save_data_size in GR_main.py too
        self.sys_msg = ['none' for _ in range(7)]
        self.status = ['idle' for _ in range(7)]
        self.red_btn_img = QPixmap("./red_button.png")
        self.yellow_btn_img = QPixmap("./yellow_button.png")
        self.green_btn_img = QPixmap("./green_button.png")
        self.init_device_radio_buttons()
        self.init_sensor_radio_buttons()
        self.init_menu_buttons()
        today = QDate.currentDate()
        self.dateEdit.setDate(today)

        self.IPC_handler = Thread(target=self.handle_m2g_queue, args=())
        self.IPC_handler.start()

    def handle_m2g_queue(self):
        sig_manager = SignalManager()
        sig_manager.stat_update_signal.connect(self.update_status_detail)
        sig_manager.sys_msg_update_signal.connect(self.update_sys_msg)

        while not self.is_closed:
            if not self.m2g_queue.empty():
                m2g_msg = self.m2g_queue.get()
                
                if m2g_msg[0] == CONN_STATUS:
                    self.set_conn_status(m2g_msg[1], m2g_msg[2])

                elif m2g_msg[0] == SHOW_DATA:
                    sys_msg = self.data_list_to_sys_msg(m2g_msg[1], m2g_msg[2])
                    self.set_sys_msg(m2g_msg[1], sys_msg)
            else:
                time.sleep(0.01)
                    
            sig_manager.run()
                    
    def init_device_radio_buttons(self):
        for i in range(1,7):
            exec("self.rb_imu" +str(i)+ ".clicked.connect(self.handle_device_rb)")
        self.rb_all.clicked.connect(self.handle_device_rb)

    def init_sensor_radio_buttons(self):
        self.rb_accX.clicked.connect(self.handle_sensor_rb)
        self.rb_accY.clicked.connect(self.handle_sensor_rb)
        self.rb_accZ.clicked.connect(self.handle_sensor_rb)

    def init_menu_buttons(self):
        self.bt_conn.clicked.connect(self.handle_conn_bt)
        self.bt_disconn.clicked.connect(self.handle_disconn_bt)
        self.bt_save.clicked.connect(self.handle_save_bt)
        self.bt_display.clicked.connect(self.handle_display_btn)

    def set_conn_status(self, id, success:bool):
        if success:
            self.set_imu_color(id, 'green')
            self.set_status_msg(id, 'connected') 
        elif not success:
            self.set_imu_color(id, 'red')
            self.set_status_msg(id, 'idle')
            self.set_sys_msg(id, 'BT disconnected with Dev id : '+str(id))

    @pyqtSlot()
    def handle_device_rb(self):
        for i in range(1,7):
            exec("if self.rb_imu" +str(i)+ ".isChecked(): self.device_cursor=" +str(i))
        if self.rb_all.isChecked() : self.device_cursor = 10
        print("device -> ", self.device_cursor, sep='')

    @pyqtSlot()
    def handle_sensor_rb(self):
        if self.rb_accX.isChecked(): self.sensor_cursor=1
        elif self.rb_accY.isChecked(): self.sensor_cursor=2
        elif self.rb_accZ.isChecked(): self.sensor_cursor=3
        elif self.rb_all_sensor.isChecked(): self.sensor_cursor=7
        print("sensor -> ", self.sensor_cursor, sep='')

    @pyqtSlot()
    def handle_conn_bt(self):
        # BT connect function or register BT connect on proc queue
        id = self.device_cursor
        if id == -1:
            return
        elif id == 10:
            for i in range(1,6):
                self.set_imu_color(i, "yellow")
                self.set_status_msg(i,'connecting...')
                g2m_msg = (REQUEST_CONN, i)
                self.g2m_queue.put(g2m_msg)
                time.sleep(1e-1)
            return                
        self.set_imu_color(id, "yellow")
        self.set_status_msg(id,'connecting...')
        g2m_msg = (REQUEST_CONN, id)
        self.g2m_queue.put(g2m_msg)

    @pyqtSlot()
    def handle_disconn_bt(self):
        if self.device_cursor == -1 :
            return
        elif self.device_cursor == 10:
            for i in range(7):
                msg = (REQUEST_DISCONN, i)
                self.g2m_queue.put(msg)
                time.sleep(1e-2)
            return

        msg = (REQUEST_DISCONN, self.device_cursor)
        self.g2m_queue.put(msg)

    @pyqtSlot()
    def handle_display_btn(self):
        msg = (REQUEST_DISPLAY,)
        self.g2m_queue.put(msg)

        self.bt_display.setDisabled(True)
        self.bt_save.setEnabled(True)
        self.bt_plot.setEnabled(True)

    @pyqtSlot()
    def handle_save_bt(self):
        date = self.dateEdit.date()
        year = str(date.year())
        month = str(date.month())
        day = str(date.day())
        date_str = year+ '_' + month+ '_' + day + '_'

        subject_name = self.le_subject_name.text()

        file_name = date_str + subject_name

        msg = (REQUEST_SAVE, file_name)
        self.g2m_queue.put(msg)

        self.bt_display.setEnabled(True)
        self.bt_save.setDisabled(True)
        self.bt_plot.setEnabled(True)

    @pyqtSlot()
    def update_status_detail(self):
        if self.device_cursor == -1:
            return
        elif self.device_cursor == 10:
            status_str = ''
            for i in range(7):
                status_str += self.status[i]
                status_str += '\n'
            
            self.lb_status_detail.setText(status_str)
            return

        status_str = self.status[self.device_cursor-1]
        self.lb_status_detail.setText(status_str)

    @pyqtSlot()
    def update_sys_msg(self):
        if self.device_cursor == -1:
            return
        elif self.device_cursor == 10:
            sys_msg = ''
            for i in range(7):
                if '\n' in self.sys_msg[i]:
                    sys_msg += self.sys_msg[i][:self.sys_msg[i].index('\n')]
                else :
                    sys_msg += self.sys_msg[i]
                sys_msg += '\n'
            
            self.te_msg_detail.setPlainText(sys_msg)
            return
        sys_msg = self.sys_msg[self.device_cursor-1]
        #self.te_msg_detail.clear()
        self.te_msg_detail.setPlainText(sys_msg)

    def set_sys_msg(self, id, msg:str):
        self.sys_msg[id-1] = str(msg)

    def set_status_msg(self, id, msg:str):
        self.status[id-1] = str(msg)

    def set_imu_color(self, id, color):
        exec("self.img_imu" + str(id) + ".setPixmap(self."+ str(color)+"_btn_img)")

    def data_list_to_sys_msg(self, id, list):
        start = list[0]
        s_time = start[:start.index('/')]
        end = list[self.save_data_size-1]
        e_time = end[:end.index('/')]

        s_time = s_time.split(':')
        e_time = e_time.split(':')

        h_diff = (int(e_time[0]) - int(s_time[0]))*24*60*1000
        m_diff = (int(e_time[1]) - int(s_time[1]))*60*1000
        s_diff = (int(e_time[2]) - int(s_time[2]))*1000
        ms_diff = int(e_time[3]) - int(s_time[3])

        total_ms_diff = h_diff + m_diff + s_diff+ ms_diff

        sampling_rate = int(self.save_data_size / (total_ms_diff/1000))

        rtn_str = 'IMU'+str(id)+' sampling rate : ' + str(sampling_rate) +  'Hz \n'

        for d in list:
            rtn_str += 'IMU' + str(id) + ' -> ' + d + '\n'
        return rtn_str

    def closeEvent(self, event):
        self.is_closed = True
        self.IPC_handler.join()
        msg = (REQUEST_EXIT,)
        self.g2m_queue.put(msg)

# end of MsdlWindow class
def init_func(q1, q2):
    app = QApplication(sys.argv)
    mWindow = MsdlWindow(q1, q2)
    mWindow.show()
    app.exec_()

def gui_init(q1,q2):
    Process(target=init_func, args=(q1,q2)).start()

if __name__ == '__main__':
    m2g_queue = Queue()
    g2m_queue = Queue()
    gui_init(m2g_queue, g2m_queue)
