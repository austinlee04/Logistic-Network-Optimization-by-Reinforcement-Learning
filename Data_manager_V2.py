import random
import csv
from Environment_V3 import LogisticNetwork
# try to use pandas

env = LogisticNetwork()

MAX = 10 ** 4


class DataManager:
    def __init__(self):
        self.parcel = dict()            # code : [state, dep, arv, route]
        self.parcel_log = dict()

    def sample_maker(self, nodes, num, time):
        key = list()
        for i in range(1, num+1):
            parcel_code = format(time, '03')+'P'+str(MAX + i)
            dep, arv = random.sample(nodes, 2)
            if (dep, arv) not in key:
                key.append((dep, arv))
            self.parcel[parcel_code] = ['G', 0, [0, 0], [], [dep, arv]]
            # [위치, 도로운송완료시간, [경로 출발지 번호, 경로 도착지 번호], [[경유지, 도착여부]], [출발지, 도착지]]
            # [3].append left [경유지, 통과여부]
            self.parcel_log[parcel_code] = [[], []]
            # [허브 통과 정보[경유지, 도착시간, 출발시간], 도로 운송 정보[출발지, 도착지, 거리, 구간 통행량]] --> append 사용
        return key

    def save_log(self, name):
        f = open('HnS_simulation/'+name+'.csv', 'w', newline='')
        wr = csv.writer(f)

        wr.writerow(['택배번호',
                     '출발지', '출발시간', '거리', '통행량',
                     '경유지', '하차시간', '상차시간', '거리', '통행량',
                     '경유지', '하차시간', '상차시간', '거리', '통행량',
                     '경유지', '하차시간', '상차시간', '거리', '통행량',
                     '도착지', '도착시간'])

        for key in self.parcel_log.keys():
            if self.parcel_log[key][0][-1][1]:
                row = list()
                row.append(key)                                    # 택배번호
                row.append(self.parcel_log[key][0][0][0])          # 출발지
                for i in range(len(self.parcel_log[key][1])):
                    row.append(self.parcel_log[key][0][i][2])       # 출발시간
                    row.append(self.parcel_log[key][0][i+1][1])     # 도착시간
                    row.extend(self.parcel_log[key][1][i][2:])      # (도로 운송) 거리, 구간 통행량
                    row.append(self.parcel_log[key][1][i][1])       # 경유지
                wr.writerow(row)

        f.close()
