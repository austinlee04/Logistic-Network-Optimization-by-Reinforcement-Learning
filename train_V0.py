from Present_Network_Simulation_V4 import Simulation
from Agent_REINFORCE_V0 import Agent
import numpy as np
from tqdm import tqdm
import csv

if __name__ == "__main__":
    name = input('save_log file name : ')
    state_size = 4
    # 각 허브의 포화도
    actions = [1, 2, 3, 4, 5, 6, 7, 8]
    '''
        0=pass, 1=go through
        1:(0,0,0)   2:(1,0,0)   3:(0,1,0)   4:(0,0,1)
        5:(1,1,0)   6:(1,0,1)   7:(0,1,1)   8:(1,1,1)
    '''
    # 0은 허브 패싱, 1은 허브 통과
    action_size = len(actions)
    agent = Agent(state_size, action_size)
    sim = Simulation()
    sim.reset_network()

    episodes, time_taken, scores, entropy_log, action_log, dists, costs = [], [], [], [], [], [], []
    hub_log = dict()
    for place in sim.env.hub_sky_codes:
        hub_log[place] = [sim.env.hub_data[place][1]]
    episode_num = int(input('how many episodes? : '))
    MTE = int(input('parcels to move : '))
    # 에피소드 종료시키기 위해 이동시켜야 하는 소포 양
    sim.save_state_log()

    for e in tqdm(range(1, episode_num+1)):
        done = 0
        score = 0
        time = 1
        dist, cost = [], []
        sim.reset_network()
        sim.save_state_log()
        action_log.append([0 for _ in range(8)])
        while done <= MTE:
            state = sim.get_state(time)
            for sample in state:
                route = sample.pop()
                s = np.reshape(sample, [1, state_size])
                action = agent.get_action(s)
                action_log[-1][action-1] += 1
                sim.weight[sim.env.hub_data[route[0]][4]-25][sim.env.hub_data[route[1]][4]-25] = action
                # 경로 따른 가중치(행동 선택) 설정
            sim.simulate(time)
            val = sim.get_result()
            if val:
                for result in val:
                    done += 1
                    first_state, action_made, reward = result[0][0], result[0][1], result[0][2]
                    dist.append(result[1][0])
                    cost.append(result[1][1])
                    first_state = np.reshape(first_state, [1, state_size])
                    agent.append_sample(first_state, action_made, reward)
                    score += reward
            time += 1
        left = len(sim.data.parcel.keys())
        while len(sim.data.parcel.keys()) > round(left * 0.75):
            sim.simulate(time)
            val = sim.get_result()
            if val:
                for result in val:
                    done += 1
                    first_state, action_made, reward = result[0][0], result[0][1], result[0][2]
                    dist.append(result[1][0])
                    cost.append(result[1][1])
                    first_state = np.reshape(first_state, [1, state_size])
                    agent.append_sample(first_state, action_made, reward)
                    score += reward
            time += 1

        entropy = agent.train_model()
        episodes.append(e)
        time_taken.append(time)
        scores.append(score)
        entropy_log.append(entropy)
        dists.append(np.mean(dist))
        costs.append(np.mean(cost))
        for place in sim.env.hub_sky_codes:
            hub_log[place].append(np.mean(sim.state_log[place][1:]))
        # print("episode: {:3d} | score: {:3d} | entropy: {:.3f}".format(time, score, entropy))
        agent.model.save_weights('save_model/model_03', save_format='tf')
        # sim.save_simulation(name)
        # sim.save_simulation('211214_{0:2d}'.format(e))

    f = open('study_log/'+name+'.csv', 'w', newline='')
    wr = csv.writer(f)
    head = ['episode', 'dist', 'cost', 'score', 'entropy',
            '(0,0,0)', '(1,0,0)', '(0,1,0)', '(0,0,1)',
            '(1,1,0)', '(1,0,1)', '(0,1,1)', '(1,1,1)']
    names = list(sim.env.hub_sky_codes)
    head.extend(names)
    wr.writerow(head)
    for i in range(episode_num):
        row = list()
        row.extend([episodes[i], dists[i], costs[i], scores[i], entropy_log[i]])
        row.extend(action_log[i])
        for hub in names:
            row.append(hub_log[hub][i+1])
        wr.writerow(row)
    f.close()
