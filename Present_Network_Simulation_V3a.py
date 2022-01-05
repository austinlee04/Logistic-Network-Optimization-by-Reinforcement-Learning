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
        self.weight = [[0 for _ in range(247)] for _ in range(247)]
        self.routes = list()
        self.fin = list()
        # __ 상속 없이 가능???

    def get_state(self, time):
        self.routes = self.data.sample_maker(self.env.hub_ground_codes, random.randint(100, 400), time)
        state = []
        for sample in self.routes:
            s = list()
            s.append(round(len(self.env.hub_data[self.env.hub_data[sample[0]][3]][0]) / self.env.hub_data[self.env.hub_data[sample[0]][3]][1] * 100))
            s.append(round(len(self.env.hub_data['중부권 광역우편물류센터'][0]) / self.env.hub_data['중부권 광역우편물류센터'][1] * 100))
            s.append(round(len(self.env.hub_data[self.env.hub_data[sample[1]][3]][0]) / self.env.hub_data[self.env.hub_data[sample[1]][3]][1] * 100))
            tot = 0
            for name in self.env.hub_sky_codes:
                if name == '중부권 광역우편물류센터':
                    continue
                tot += round(len(self.env.hub_data[name][0]) / 2)
            s.append(round(tot / self.env.hub_data['중부권 광역우편물류센터'][1] * 100))
            s.append(sample)
            state.append(s)
        return state

    def path_finder(self, dep, arv):
        waypoint = list()
        waypoint.append(dep)
        waypoint.append(self.env.hub_data[dep][3])
        waypoint.append('중부권 광역우편물류센터')
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
            # print(time, self.env.hub_data[name][0])
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
                        self.data.parcel_log[key][0][i - 1][2] = time
                        self.data.parcel[key][2][0] = self.env.hub_data[self.data.parcel[key][3][i - 1][0]][4]
                        self.data.parcel[key][2][1] = self.env.hub_data[self.data.parcel[key][3][i][0]][4]
                        self.env.traffic[self.data.parcel[key][2][0]][self.data.parcel[key][2][1]] += 1
                        self.data.parcel[key][1] = time + round(self.data.parcel_log[key][1][i - 1][2] / self.speed)
                        break

        for key in self.data.parcel.keys():
            if self.data.parcel[key][0] == 'R_':
                for i in range(1, len(self.data.parcel[key][3])):
                    if not self.data.parcel[key][3][i][1]:
                        self.data.parcel_log[key][1][i-1][3] = self.env.traffic[self.data.parcel[key][2][0]][self.data.parcel[key][2][1]]
                        self.data.parcel[key][0] = 'R'
                        break

    def get_result(self):
        done = len(self.fin)
        self.fin = []
        return done

    def save_simulation(self, name):
        self.data.save_log('HnS_simulation_'+name)
