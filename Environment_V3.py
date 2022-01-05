import networkx as nx
import csv
from collections import deque


class LogisticNetwork:
    def __init__(self):
        self.network = nx.Graph()
        self.hub_num = 0
        self.hub_data = {}
        self.hub_ground_codes = list()
        self.hub_sky_codes = list()
        self.traffic = list()

    def reset_network(self, road_file, hub_file):            # 시뮬레이션 초기화             ## 구현 완료
        f1 = open(road_file, 'r', encoding='UTF-8')
        f2 = open(hub_file, 'r', encoding='UTF-8')
        data_road = csv.reader(f1)
        data_hub = csv.reader(f2)
        next(data_hub)
        next(data_road)
        self.hub_ground_codes = []
        self.hub_sky_codes = []
        for row in data_hub:
            if not row[0]:
                break
            self.hub_data[row[0]] = [deque(), int(row[1])*10, int(row[4]), row[2], int(row[5])]
            # 이름:[대기열, 처리용량, 처리시간, 상위허브, 번호]
            self.network.add_edge(row[0], row[3].split()[1], weight=15.0)
            if row[1] == '0':
                self.hub_ground_codes.append(row[0])
            else:
                self.hub_sky_codes.append(row[0])
        self.hub_num = len(self.hub_data.keys())
        self.traffic = [[0 for _ in range(self.hub_num+1)] for _ in range(self.hub_num+1)]
        # [출발지][도착지]

        name = list()
        dist = list()
        n = 1
        for row in data_road:
            if n == 1:
                for value in row:
                    if value:
                        name.append(value)
            else:
                for value in row:
                    if value:
                        dist.append(value)
                for i in range(1, len(name)):
                    if dist[i] == '0':
                        continue
                    self.network.add_edge(name[i - 1], name[i], weight=float(dist[i]))
                name = []
                dist = []
            n *= -1

# 허브에서의 이동 관련 함수들

    def hub_load(self, hub, time, sample):
        if len(self.hub_data[hub][0]) <= self.hub_data[hub][1]:
            self.hub_data[hub][0].append([sample, time+self.hub_data[hub][2]])
        else:
            self.hub_data[hub][0].append([sample, 0])

    def hub_classification(self, hub, time):
        done = list()
        k = 0
        for i in range(self.hub_data[hub][1]):
            if not self.hub_data[hub][0] or len(self.hub_data[hub][0]) <= k:
                break
            if self.hub_data[hub][0][0][1] == time:
                done.append(self.hub_data[hub][0].popleft()[0])
            elif not self.hub_data[hub][0][k][1]:
                self.hub_data[hub][0][k][1] = time + self.hub_data[hub][2]
                k += 1
        return done
