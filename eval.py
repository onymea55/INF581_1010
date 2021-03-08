import subprocess
import gym
from models.Nets import NetTransitions
import os
import sys
import torch
import numpy as np
import matplotlib.pyplot as plt
import tqdm
import copy

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'  # or string.ascii_uppercase
N = len(ALPHABET)
ALPHABET_INDEX = {d: i for i, d in enumerate(ALPHABET, 1)}

A_UPPERCASE = ord('A')
ALPHABET_SIZE = 26


def _decompose(number):
    """Generate digits from `number` in base alphabet, least significants
    bits first.

    Since A is 1 rather than 0 in base alphabet, we are dealing with
    `number - 1` at each iteration to be able to extract the proper digits.
    """

    while number:
        number, remainder = divmod(number - 1, ALPHABET_SIZE)
        yield remainder


def base_10_to_alphabet(number):
    """Convert a decimal number to its base alphabet representation"""

    return ''.join(
            chr(A_UPPERCASE + part)
            for part in _decompose(number)
    )[::-1]


def num_to_alph(num):
    res = [0, 0, 0]
    for i in range(num):
        res[-1]+=1
        if res[-1] >= 26:
            res[-1] = 0
            res[-2] += 1
            if res[-2] >= 26:
                res[-2] = 0
                res[-3] +=1

    return ALPHABET[res[0]]+ALPHABET[res[1]]+ALPHABET[res[2]]

def play_a_game(moves):
    env = gym.make('gym_tenten:tenten-v0')
    env.init(10, 3)

    for i, move in enumerate(moves):
        env.save_grid(num_to_alph(i))
        o, r, done, _ = env.step(move, forced=True)

    i = "./tmp/*.png"
    o = f"best_game_{env.real_score}.gif"
    subprocess.call("convert -delay 25 -loop 0 " + i + " " + o, shell=True)
    os.system("rm ./tmp/*")

def pick_action(net, env):
    if env.isOver():
        return None, None

    actions = env.legal_moves_list

    q_values = torch.tensor([float('-inf') for i in range(env.action_size)])
    for action in actions:
        q_values[action] = net(env.get_transition(action)).item()

    return int(torch.argmax(q_values))

def main(model_path):
    net = NetTransitions()
    net.load_state_dict(torch.load(model_path))
    net.eval()

    env = gym.make('gym_tenten:tenten-v0')
    env.init(10, 3)

    dev = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    print(dev)
    net.to(dev)

    
    scores = []
    best_game = []
    for i in tqdm.tqdm(range(50)):
        done = False
        game = []
        while not done:
            action = pick_action(net, env)
            game.append(action)
            o, r, done, _ = env.step(action)
        if len(scores) == 0:
            best_game = copy.deepcopy(game)
        elif env.real_score > max(scores):
            best_game = copy.deepcopy(game)
        scores.append(env.real_score)
        env.reset()
    print(f"Max score : {max(scores)}; Avg score : {np.mean(scores)}")
    plt.plot(range(len(scores)), scores)
    plt.savefig("scores_plot.png")
    plt.close()
    play_a_game(best_game)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please enter a model")
        exit()
    main(sys.argv[1])