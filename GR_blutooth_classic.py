from threading import Thread
from bluetooth import *
import time

from multiprocessing import Process, Queue

# Manager to Handler command
M2H_HANDLE_DISCONNECT = 4001

# Handler to Manager command
H2M_SET_USABLE = 5001

# Ble to Main command
CONN_SUCCESS = 1000
CONN_FAIL = 1001
CONN_CLOSED = 1002
READ_DATA = 1003

IMU_DICT = {
    1:"98:D3:71:FE:00:70",
    2:"98:D3:11:FC:91:2A",
    3:"98:D3:71:FE:09:C1",
    4:"98:D3:91:FD:EF:77",
    5:"98:D3:51:FE:2F:D3",
    #6:"98:D3:71:FE:09:C4", #IMU
    #6:"98:D3:C1:FD:4C:B2" #PP             
}

class BluetoothManager():
    def __init__(self, queue=Queue()):
        self.reconnect_num = 5
        
        self.bluetooth_queue = queue
        self.manager_to_handler_queue = [Queue() for _ in range(7)]
        self.handler_to_manager_queue = [Queue() for _ in range(7)]
        self.id_usable = [True for _ in range(7)]
        self.kill_listener = False
        
        handler_msg_listener = Thread(target=self.listen_handler_msg, args=())
        handler_msg_listener.start()

    def listen_handler_msg(self):
        while not self.kill_listener:
            for d in self.handler_to_manager_queue:
                if not d.empty():
                    msg = d.get()

                    if msg[0] == H2M_SET_USABLE:
                        id = msg[1]
                        bool = msg[2]
                        self.id_usable[id-1] = bool
            time.sleep(1e-3)

        exit()
        
    def request_conn(self, id):
        if self.id_usable[id-1]:
            conn_handler = Process(target=self.handle_conn, args=(id,)) # for multi-processing
            conn_handler.start()
        elif not self.id_usable[id-1]:
            print("already connected")
        
    def request_disconn(self, id):
        m2h_msg = (M2H_HANDLE_DISCONNECT, id)
        self.manager_to_handler_queue[id-1].put(m2h_msg)

    def handle_conn(self, id):
        h2m_msg = (H2M_SET_USABLE, id, False)
        self.handler_to_manager_queue[id-1].put(h2m_msg)
        handler_id = id
        client_socket = BluetoothSocket(RFCOMM)

        def handle_disconnection():
            client_socket.close()
            
            main_msg = (CONN_FAIL, id)
            self.bluetooth_queue.put(main_msg)

            h2m_msg = (H2M_SET_USABLE, id, True)
            self.handler_to_manager_queue[id-1].put(h2m_msg)
            return

        def listen_manager_msg():
            while True:
                if not self.manager_to_handler_queue[id-1].empty():
                    msg = self.manager_to_handler_queue[id-1].get()

                    if msg[0] == M2H_HANDLE_DISCONNECT:
                        handle_disconnection()
                        exit()

                time.sleep(1e-2)

        manager_msg_handler = Thread(target=listen_manager_msg, args=())
        manager_msg_handler.start()        

        try:
            client_socket.connect((IMU_DICT[handler_id],1))
            msg=(CONN_SUCCESS, handler_id)
            self.bluetooth_queue.put(msg)
        except Exception as e:
            print(handler_id,' connection fail', sep='')
            print(e, end='')  
            handle_disconnection()

        try:
            while True:
                tmp_msg = client_socket.recv(8096)
                
                if tmp_msg == b'':
                    handle_disconnection()
                    break
                
                if handler_id <= 5:
                    tmp_msg = tmp_msg.decode('utf-8')

                data_msg = (READ_DATA, handler_id, tmp_msg)
                self.bluetooth_queue.put(data_msg)
                data_msg = None
                        
        except Exception as e: 
            print(e)
            handle_disconnection()
        finally:
            handle_disconnection()
                
if __name__ == '__main__':
    # test code
    bm = BluetoothManager()
    for i in range(1,6):
        bm.request_conn(i)
        time.sleep(1)
