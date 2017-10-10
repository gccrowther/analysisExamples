from datetime import datetime
import os
from construct import *

class DateTimeAdapter(Adapter):
    def _encode(self, obj, context):
        return int(obj.timestamp() * 1000)
    def _decode(self, obj, context):
        return datetime.utcfromtimestamp(obj / 1000) 

OUTPUT = r'E:\Backup - 04102017\ShareFile\Personal Folders\Rice Energy\Belmont Project\data\DTS_Fracture_Treatment_07'

PAYLOAD_HEADER = Struct("size" / Int32ub,
            "timestamp" / DateTimeAdapter(Int64ub),
            "config" / Enum(Flag, single = False, double = True),
            "fibre_number" / Float32b)

PAYLOAD_HEADER_RAW = Struct("size" / Int32ub,
            "timestamp" / Int64ub,
            "config" / Enum(Flag, single = False, double = True),
            "fibre_number" / Float32b)

PAYLOAD_DATA_S = Struct("distance" / Float32b,
                       "temperature" / Float32b,
                       "forward_stokes" / Float32b,
                       "forward_anti_stokes" / Float32b)

PAYLOAD_DATA_D = Struct("distance" / Float32b,
                       "temperature" / Float32b,
                       "forward_stokes" / Float32b,
                       "forward_anti_stokes" / Float32b,
                       "reverse_stokes" / Float32b,
                       "reverse_anti_stokes" / Float32b)

SINGLE_PAYLOAD = Struct("header" / PAYLOAD_HEADER,
                         "data" / Switch(this.header.config,
                                  {
                                      "single" : LazyRange(0, (this.header.size - 13) / 16, PAYLOAD_DATA_S),
                                      "double" : LazyRange(0, (this.header.size - 13) / 24, PAYLOAD_DATA_D)
                                  }))

ERROR = datetime(2016, 2, 27, 15, 8, 0).timestamp() * 1000
OFFSET = 37

def dts_correction(fin, error = ERROR, offset = OFFSET, output = OUTPUT):
    name = fin.split('\\')[-1]
    print("Reading {0}".format(name))
    start = datetime.now()
    with open(fin, 'rb') as f:
        dts = []
        header = []
        pointer = 0
        packets_left = True
        count = 0
        while packets_left:
            if count % 50 == 0:
                print("{0}: Reading {1} - {2} samples".format(datetime.now(), name, count))
            try:
                header.append(PAYLOAD_HEADER_RAW.parse(f.read(17)))
                if header[-1].timestamp < ERROR:
                    if header[-1].config == 'single':
                        header[-1].size -= offset * 16
                        f.read(offset * 16)
                    else:
                        header[-1].size -= offset * 24
                        f.read(offset * 24)
                        
                data = Struct("data" / Switch(header[-1].config,
                              {
                                  "single" : LazyRange(0, (header[-1].size - 13) / 16, PAYLOAD_DATA_S),
                                  "double" : LazyRange(0, (header[-1].size - 13) / 24, PAYLOAD_DATA_D)
                              })).parse(f.read(header[-1].size - 13))
                            
                dts.append(data)
                count += 1
            except:
                print("{0}: Read {1} - {2} total samples".format(datetime.now(), name, count))
                packets_left = False
    
    with open(os.path.join(output, name), 'wb') as of:
        for i, head in enumerate(header):
            of.write(PAYLOAD_HEADER_RAW.build(head))
            of.write(Struct("data" / Switch(head.config,
                              {
                                  "single" : LazyRange(0, (head.size - 13) / 16, PAYLOAD_DATA_S),
                                  "double" : LazyRange(0, (head.size - 13) / 24, PAYLOAD_DATA_D)
                              })).build(dts[i]))