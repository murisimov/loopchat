#!/usr/bin/python

import logging
from datetime import datetime, time
from re import findall
from time import time as tm
from tornado.gen import coroutine, Return, Task
from tornado.ioloop import IOLoop
from tornado.process import Subprocess

class GetStats:
    def __init__(self, percentage=True, sleeptime = 1):
        self.percentage = percentage
        self.cpustat = '/proc/stat'
        self.loadavg = '/proc/loadavg'
        self.meminfo = '/proc/meminfo'
        self.sleeptime = sleeptime

    @coroutine
    def getcputime(self):
        ''' CPU '''
        cpu_infos = {}
        with open(self.cpustat) as f_stat:
            lines = [ [ line.split()[0] ] +
                      [ float(col) for col in line.split()[1:] if col ]
                     for line in f_stat if line.startswith('cpu') ]
            # Compute for every cpu
            for cpu_line in lines:
                if len(cpu_line) == 11:
                    (cpu_id, user, nice, system, idle, iowait, irq,
                     softrig, steal, guest, guest_nice) = cpu_line
                elif len(cpu_line) == 10:
                    (cpu_id, user, nice, system, idle, iowait, irq,
                     softrig, steal, guest) = cpu_line
                Idle = idle + iowait
                NonIdle= user + nice + system + irq + softrig + steal
                Total=Idle + NonIdle
                # Add to pool
                cpu_infos.update({cpu_id: {'total': Total, 'idle': Idle}})
            raise Return(cpu_infos)

    @coroutine
    def getloadavg(self):
        ''' LA '''
        with open(self.loadavg, 'r') as loadavg:
            la_info = [ x for x in loadavg.read().split() if x ][:3]
            la_info = " ".join(la_info)
            raise Return(la_info)

    @coroutine
    def getmeminfo(self):
        ''' RAM '''
        with open(self.meminfo) as mem:
            generator = [ findall(r"[\w']+", line) for line in mem.readlines()
                          if line.startswith('MemTotal')
                          or line.startswith('MemFree')
                          or line.startswith('Cached')
                          or line.startswith('Buffers') ]
            for array in generator:
                del(array[2])
                array[1] = int(array[1]) / 1024
            meminfo = dict((key,value) for (key,value) in generator)
            meminfo['MemUsed'] = int(round(meminfo['MemTotal'] -
                                           (meminfo['MemFree'] +
                                            meminfo['Cached'] +
                                            meminfo['Buffers'])
                                 ))
            raise Return(meminfo)

    @coroutine
    def stats(self):
        '''
        CPU_Percentage=((Total-PrevTotal) - (Idle-PrevIdle)) / (Total-PrevTotal)
        '''
        start = yield self.getcputime()
        yield Task(IOLoop.current().add_timeout, tm() + self.sleeptime)
        stop = yield self.getcputime()

        cpu_load = {}

        for cpu in start:
            Total = stop[cpu]['total']
            PrevTotal = start[cpu]['total']

            Idle = stop[cpu]['idle']
            PrevIdle = start[cpu]['idle']
            CPU_Percentage=int(round(((Total-PrevTotal) - (Idle-PrevIdle)) /
                                      (Total-PrevTotal) * 100))
            cpu_load.update({cpu: CPU_Percentage})
        else:
            now = datetime.now()
            current_time = str(time(now.hour, now.minute, now.second))

        meminfo = yield self.getmeminfo()
        loadavg = yield self.getloadavg()

        stats = {
            'loadavg': loadavg,
            'cpu': [ current_time, cpu_load['cpu'] ],
            'mem': [ current_time, meminfo['MemUsed'], meminfo['MemTotal'] ],
        }

        raise Return(stats)
