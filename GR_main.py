from GR_GUI import *
from GR_blutooth_classic import *
#from GR_pose_detection import CameraManager
from multiprocessing import Process, Queue
import datetime as dt
from datetime import datetime
import numpy as np

class TimeStandard():
    def __init__(self, abs_time, rel_time) -> None:
        self.abs_time = abs_time
        self.rel_time = int(rel_time)

    def convert_rel_to_abs(self, rel_time)-> datetime.time:
        if type(rel_time) != int:
            rel_time = int(rel_time)

        diff = int(np.abs(self.rel_time - rel_time))

        rtn_time = self.abs_time + dt.timedelta(milliseconds=diff)

        return rtn_time

class MainModule():
    def __init__(self) -> None:
        self.bluetooth_queue = Queue()
        self.g2m_queue = Queue()
        self.m2g_queue = Queue()

        self.mWindow = gui_init(self.m2g_queue, self.g2m_queue)
        self.bm = BluetoothManager(self.bluetooth_queue)
        #self.cm = CameraManager()

        self.data_save_status = SHOW_DATA
        self.g2m_msg = None
        self.m2g_msg = None
        self.ble_msg = None

        #self.save_dir = 'Z:\[2] 연구활동\[2-3] 공동 프로젝트\[지역우수과학자] 보행실험 데이터/'
        self.save_dir = './DATA/'
        
        self.one_msg = ["" for _ in range(7)]
        self.standard_time_list = [None for _ in range(7)]
        self.msg_list = [[] for _ in range(7)]
        self.rest = [None for _ in range(7)]
        self.is_first_data = [True for _ in range(7)]
        self.save_data_size = 100
        # if you change save_data_size
        # you should change save_data_size in GR_GUI.py too

        self.base_name = None

        self.file_name = [None for _ in range(7)]
        self.file = [None for _ in range(7)]

        self.main()

    def close_all_file(self):
        for d in self.file:
            if d != None:
                d.close()

        self.file=[None for _ in range(7)]

    def make_time_msg(self, time):
        hour = time.hour
        min = time.minute
        sec = time.second
        ms = int(time.microsecond/1000)

        return (str(hour)+':'+str(min)+':'+str(sec)+':'+str(ms) +'/')


    def handle_data(self, id, msg):
        index = id-1
        self.one_msg[index] += str(msg)

        while '\r' in self.one_msg[index] :
            if self.is_first_data[index]:
                self.is_first_data[index] = False
                return []

            self.rest[index] = self.one_msg[index][self.one_msg[index].index('\r')+1:]
            self.one_msg[index] = self.one_msg[index][:self.one_msg[index].index('\r')] 
            self.one_msg[index] = self.one_msg[index].replace("\n","")

            msg_as_list = self.one_msg[index].split(",")

            if(len(msg_as_list)==7): # rel_time, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z
                rel_time= msg_as_list[0]
            elif(len(msg_as_list)<7 or len(msg_as_list)>7):
                self.one_msg[index] = '' + self.rest[index]
                continue

            if self.standard_time_list[index] is None:
                now = datetime.now()
                time_msg = self.make_time_msg(now)
                self.standard_time_list[index] = TimeStandard(abs_time=now, rel_time=rel_time)

            elif self.standard_time_list[index] is not None:
                now = self.standard_time_list[index].convert_rel_to_abs(rel_time)
                time_msg = self.make_time_msg(now)

            self.one_msg[index] = self.one_msg[index][self.one_msg[index].index(',')+1:]
                    
            self.one_msg[index] = time_msg + self.one_msg[index]
            self.msg_list[index].append(self.one_msg[index])
            self.one_msg[index] = '' + self.rest[index]

        if len(self.msg_list[index]) >= self.save_data_size:
            rtn = self.msg_list[index]
            self.msg_list[index] = []
            return rtn

        return []

    def handle_insole_data(self, id, msg):
        index = id-1
        msg_str = msg.hex(',')
        msg_str = msg_str.replace('0a', '\n')
        msg_str = msg_str.split(',')
        tmp_str = ''
        for d in msg_str:
            if d != '\n':
                tmp_str += (str(int(d, base=16)) + ',')
            elif d == '\n':
                tmp_str += '\n'
        msg_str = tmp_str

        self.one_msg[index] += msg_str

        if '\n' in msg_str :
            if self.is_first_data[index]:
                self.is_first_data[index] = False
                return []

            self.rest[index] = self.one_msg[index][self.one_msg[index].index('\n')+1:]
            self.one_msg[index] = self.one_msg[index][1:self.one_msg[index].index('\n')] # start with colon

            now = time.localtime()
            hour = now.tm_hour
            min = now.tm_min
            sec = now.tm_sec
            ms = int(datetime.now().microsecond/1000)
            self.one_msg[index] = str(hour)+':'+str(min)+':'+str(sec)+':'+str(ms) +'/'+ self.one_msg[index]
            self.msg_list[index].append(self.one_msg[index])
            self.one_msg[index] = '' + self.rest[index]

        if len(self.msg_list[index]) >= self.save_data_size:
            rtn = self.msg_list[index]
            self.msg_list[index] = []
            return rtn

        return []

    def main(self):
        while True:
            if not self.bluetooth_queue.empty():
                self.ble_msg = self.bluetooth_queue.get()

                if self.ble_msg[0] == CONN_SUCCESS:
                    self.m2g_msg = (CONN_STATUS, self.ble_msg[1], True)
                    self.m2g_queue.put(self.m2g_msg)

                elif self.ble_msg[0] == CONN_FAIL or self.ble_msg[0] == CONN_CLOSED:
                    self.m2g_msg = (CONN_STATUS, self.ble_msg[1], False)
                    self.m2g_queue.put(self.m2g_msg)

                elif self.ble_msg[0] == READ_DATA:
                    if self.data_save_status == SHOW_DATA:
                        id = self.ble_msg[1]
                        data = self.ble_msg[2]

                        if id <= 5:
                            msg_list = self.handle_data(id, data)
                        elif id>= 6:
                            msg_list = self.handle_insole_data(id, data)

                        if len(msg_list) > 0:
                            self.m2g_msg = (SHOW_DATA, id, msg_list)
                            self.m2g_queue.put(self.m2g_msg)

                    elif self.data_save_status == SAVE_DATA:
                        id = self.ble_msg[1]
                        data = self.ble_msg[2]

                        msg_list = self.handle_data(id, data)

                        if len(msg_list) > 0:
                            self.m2g_msg = (SAVE_DATA, id)
                            self.m2g_queue.put(self.m2g_msg)

                            self.prev_name = self.file_name[id-1]
                            if not os.path.exists(self.save_dir + self.base_name +'/'):
                                os.makedirs(self.save_dir + self.base_name +'/')

                            self.file_name[id-1] = self.save_dir + self.base_name +'/IMU'+ str(id)+'.csv'

                            if self.file[id-1] == None or self.file_name[id-1] != self.prev_name:
                                if self.file[id-1] != None:
                                    self.file[id-1].close()
                                    self.file[id-1] = None

                                self.file[id-1] = open(self.file_name[id-1], 'a')

                            for d in msg_list:
                                d = d.replace('/', ',')
                                d = d+'\n'
                                self.file[id-1].write(d)

            if not self.g2m_queue.empty():
                self.g2m_msg = self.g2m_queue.get()

                if self.g2m_msg[0] == REQUEST_CONN:
                    self.bm.request_conn(self.g2m_msg[1])

                elif self.g2m_msg[0] == REQUEST_DISCONN:
                    self.bm.request_disconn(self.g2m_msg[1])

                elif self.g2m_msg[0] == REQUEST_SAVE:
                    #self.cm.request_start()
                    self.data_save_status = SAVE_DATA
                    self.base_name = self.g2m_msg[1]

                elif self.g2m_msg[0] == REQUEST_DISPLAY:
                    #self.cm.request_end()
                    self.data_save_status = SHOW_DATA
                    self.close_all_file()

                elif self.g2m_msg[0] == REQUEST_EXIT:
                    for i in range(1,8):
                        self.bm.request_disconn(i)
                        time.sleep(1e-2)
                    
                    self.close_all_file()
                    #self.cm.request_end()
                    #self.cm.destroy()
                    self.bm.kill_listener = True
                    exit()

if __name__ == '__main__':
    MainModule()