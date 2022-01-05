from Environment_V3 import LogisticNetwork
from Data_manager_V2 import DataManager
import networkx as nx
import random


# class Simulation(LogisticNetwork, DataManager):
class Simulation:
    def __init__(self):
        # super(LogisticNetwork, self).__init__()
        # super(DataManager, self).__init__()
        self.speed = 20
        self.env = LogisticNetwork()
        self.data = DataManager()
        self.weight = list()
        self.routes = list()
        self.fin = list()
        self.error = 0
        self.state_log = dict()
        # __ 상속 없이 가능???

    def save_state_log(self):
        for name in self.env.hub_sky_codes:
            self.state_log[name] = [self.env.hub_data[name][1]]

    def reset_network(self):
        self.env.reset_network('data/data_road_V3.csv', 'data/data_hub_V3.csv')
        self.data.parcel = dict()
        self.data.parcel_log = dict()
        self.fin = []
        self.weight = [[0 for _ in range(247)] for _ in range(247)]
        self.state_log = dict()

    def get_state(self, time):
        self.routes = self.data.sample_maker(self.env.hub_ground_codes, random.randint(200, 500), time)
        # (60, 300) or (200, 500)
        for name in self.env.hub_sky_codes:
            self.state_log[name].append(len(self.env.hub_data[name][0]))
        state = []
        for sample in self.routes:
            s = list()
            s.append(round(self.state_log[self.env.hub_data[sample[0]][3]][time] / self.state_log[self.env.hub_data[sample[0]][3]][0] * 100))
            s.append(round(self.state_log['중부권 광역우편물류센터'][time] / self.state_log['중부권 광역우편물류센터'][0] * 100))
            s.append(round(self.state_log[self.env.hub_data[sample[1]][3]][time] / self.state_log[self.env.hub_data[sample[1]][3]][0] * 100))
            tot = 0
            for name in self.env.hub_sky_codes:
                if name == '중부권 광역우편물류센터':
                    continue
                tot += len(self.env.hub_data[name][0])
            s.append(round(tot / self.state_log['중부권 광역우편물류센터'][0] * 50))
            s.append(sample)
            state.append(s)
        return state

    def path_finder(self, dep, arv):
        waypoint = list()
        action = self.weight[self.env.hub_data[dep][4]-25][self.env.hub_data[arv][4]-25]
        waypoint.append(dep)
        if action in (2, 5, 6, 8):
            waypoint.append(self.env.hub_data[dep][3])
        if action in (3, 5, 7, 8):
            waypoint.append('중부권 광역우편물류센터')
        if action in (4, 6, 7, 8):
            waypoint.append(self.env.hub_data[arv][3])
        waypoint.append(arv)
        return waypoint

    def simulate(self, time):
        for key in list(self.data.parcel.keys()):
            # Ground(경로 설정 해야 함), Road(R_ : 도로 배치), Hub, Finished
            # print(key, self.data.parcel[key])
            if self.data.parcel[key][0] == 'G':
                # 운송정보 초기 설정
                path = self.path_finder(self.data.parcel[key][-1][0], self.data.parcel[key][-1][1])
                # 인공지능 반영할 때 path_finder 함수를 변경할 것!!!
                path = [i for i in path if not '']
                for i in range(len(path)):
                    self.data.parcel[key][3].append([path[i], False])
                    self.data.parcel_log[key][0].append([path[i], 0, 0])
                for i in range(len(path) - 1):
                    self.data.parcel_log[key][1].append([path[i], path[i+1], round(
                        nx.shortest_path_length(self.env.network, path[i], path[i + 1], weight='weight')), 1])
                del self.data.parcel[key][-1]
                self.data.parcel[key][3][0][1] = True
                self.data.parcel[key][0] = 'R_'

            elif self.data.parcel[key][0] == 'R':
                # 도로 주행
                if self.data.parcel[key][1] == time:
                    for i in range(1, len(self.data.parcel[key][3])):
                        if not self.data.parcel[key][3][i][1]:
                            self.data.parcel[key][3][i][1] = True
                            if self.data.parcel[key][3][-1][1]:
                                # 운송 완료
                                self.data.parcel[key][0] = 'F'
                                self.fin.append(key)
                                # print(key)
                                self.data.parcel_log[key][0][-1][1] = time
                                del self.data.parcel[key]
                                # 데이터를 효율적으로 사용하기 위해 운송이 끝난 parcel 의 데이터를 삭제하는 과정
                            else:
                                self.data.parcel[key][0] = 'H'
                                self.data.parcel_log[key][0][i][1] = time
                                self.env.hub_load(self.data.parcel[key][3][i][0], time, key)
                                self.env.traffic[self.data.parcel[key][2][0]][self.data.parcel[key][2][1]] -= 1
                                break

        for name in self.env.hub_sky_codes:
            # 허브에서 간선상차
            # print(self.env.hub_data[name][0])
            done = self.env.hub_classification(name, time)
            if not done:
                continue
            for key in done:
                for i in range(2, len(self.data.parcel[key][3])):
                    if not self.data.parcel[key][3][i][1]:
                        self.data.parcel[key][0] = 'R_'
                        self.data.parcel_log[key][0][i-1][2] = time
                        break

        for key in self.data.parcel.keys():
            if self.data.parcel[key][0] == 'R_':
                for i in range(1, len(self.data.parcel[key][3])):
                    if not self.data.parcel[key][3][i][1]:
                        self.data.parcel_log[key][0][i-1][2] = time
                        self.data.parcel[key][2][0] = self.env.hub_data[self.data.parcel[key][3][i - 1][0]][4]
                        self.data.parcel[key][2][1] = self.env.hub_data[self.data.parcel[key][3][i][0]][4]
                        self.env.traffic[self.data.parcel[key][2][0]][self.data.parcel[key][2][1]] += 1
                        self.data.parcel[key][1] = time + round(self.data.parcel_log[key][1][i-1][2] / self.speed)
                        break

        for key in self.data.parcel.keys():
            if self.data.parcel[key][0] == 'R_':
                for i in range(1, len(self.data.parcel[key][3])):
                    if not self.data.parcel[key][3][i][1]:
                        self.data.parcel_log[key][1][i-1][3] = self.env.traffic[self.data.parcel[key][2][0]][self.data.parcel[key][2][1]]
                        self.data.parcel[key][0] = 'R'
                        break

    def get_result(self):
            if not self.fin:
                return False
            step = []
            for i in range(len(self.fin)):
                try:
                    for key in self.fin:
                        start_time = self.data.parcel_log[key][0][0][2]
                        # get starting state
                        state = list()
                        dep = self.data.parcel_log[key][0][0][0]
                        dep_top = self.env.hub_data[dep][3]
                        arv = self.data.parcel_log[key][0][-1][0]
                        arv_top = self.env.hub_data[arv][3]
                        state.append(round(self.state_log[dep_top][start_time] / self.state_log[dep_top][0] * 100))
                        state.append(round(self.state_log['중부권 광역우편물류센터'][start_time] / self.state_log['중부권 광역우편물류센터'][0] * 100))
                        state.append(round(self.state_log[arv_top][start_time] / self.state_log[arv_top][0] * 100))
                        tot = 0
                        for name in self.env.hub_sky_codes:
                            if name == '중부권 광역우편물류센터':
                                continue
                            tot += len(self.env.hub_data[name][0])
                        state.append(round(tot / self.env.hub_data['중부권 광역우편물류센터'][1] * 50))

                        # get action
                        num = len(self.data.parcel_log[key][0])
                        if num == 5:
                            action = 8
                        elif num == 4:
                            if self.data.parcel_log[key][0][1][0] == '중부권 광역우편물류센터':
                                action = 7
                            elif self.data.parcel_log[key][0][2][0] == '중부권 광역우편물류센터':
                                action = 5
                            else:
                                action = 6
                        elif num == 3:
                            if self.data.parcel_log[key][0][1][0] == dep_top:
                                action = 2
                            elif self.data.parcel_log[key][0][1][0] == arv_top:
                                action = 4
                            else:
                                action = 3
                        else:
                            action = 1

                        # get reward
                        dist, cost = 0, 0
                        for j in range(num-1):
                            dist += self.data.parcel_log[key][1][j][2]
                            cost += self.data.parcel_log[key][1][j][2] / (self.data.parcel_log[key][1][j][3])
                        t = self.data.parcel_log[key][0][-1][1] - self.data.parcel_log[key][0][0][2]
                        reward = round((dist ** 2) / (cost * t))
                        step.append(((state, action, reward), (dist, cost)))
                except ZeroDivisionError:
                    self.error += 1

            return step

    def save_simulation(self, name):
        self.data.save_log('HnS_simulation_'+name)
