import add_path
add_path.add_subfolder_to_path("D:\\Academic\\General purpose\\communication stack\\rigol\\code")

import matplotlib
matplotlib.use('TkAgg')
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import *
import threading

import Rigol_Lib.RigolSCPI as rs
import TCPconnection.MessageIterables as mi
import TCPconnection.TCPcomm as tcp
import TCPconnection.TCPListener as tl

from Rigol_util import RigolRespProc as rrp
from Rigol_util import channelDataKeeper as cld
from Rigol_util import Rigol_plotter as Rigol_plotter
from Rigol_util import RigolCommander as rc
from doorbell import DoorBell as db 


class ConsoleControl: 
    global doorbell_obj



    def __init__(self):
        # create doorbell object for message passing between main thread
        # and the single thread
        self.doorbell_obj = db.DoorBell()

        ## create commander object to manage generation of commands
        self.rigol_commander = rc.RigolCommander()

        ## create tcp object: manages send, receive, connection
        self.tcp_connection = tcp.TCPcomm()

        self.__pause_tcp_conn = False

    def run(self):
        
        try:
            ## create commands: 
            cmd_initiate_oscilloscope = self.rigol_commander.initalize_data_query_byte(rs.RIGOL_CHANNEL_IDX.CH4)
            cmd_ask_data_oscilloscope = self.rigol_commander.ask_oscilloscope_for_data()
            ## join two commands: 
            cmd_initiate_oscilloscope.append(cmd_ask_data_oscilloscope)

            ## start a tcp connection
            self.tcp_connection.establish_conn()

            ## we only have two threads: 1 main and the other one for tcpip
            self.tcp_thread = threading.Thread(target=self.tcp_connection.send_receive_thread , args=(self.doorbell_obj,))
            self.tcp_thread.daemon = True
            self.tcp_thread.start()

            while(True):
                if(self.pause_tcp_connection):                     
                    while(self.doorbell_obj.is_data_new()):
                        # print("inside wait for doorbell to be seen")
                        pass 
                    cmd_initiate_oscilloscope = self.rigol_commander.initalize_data_query_byte(rs.RIGOL_CHANNEL_IDX.CH4)
                    cmd_ask_data_oscilloscope = self.rigol_commander.ask_oscilloscope_for_data()
                    cmd_initiate_oscilloscope.append(cmd_ask_data_oscilloscope)
                    self.doorbell_obj.put_data_to_doorbell(cmd_initiate_oscilloscope)
                    
                    # data = self.tcp_connection.get_last_data()
                    # print(data)

        

        except:
            self.tcp_connection.close_conn() 
            raise 

        finally: 
            self.tcp_connection.close_conn()

    def get_data(self): 
        return self.tcp_connection.get_last_data()

    def pause_tcp_connection(self): 
        self.__pause_tcp_conn = True

    def resume_tcp_connection(self): 
        self.__pause_tcp_conn = False

    def finalize_console(self):
        self.tcp_connection.close_conn()