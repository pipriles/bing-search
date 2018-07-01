#!/usr/bin/env python3

import subprocess
import random
import time
import os

def change_agent():
    return random.choice(AGENTS)

def change_vpn():
    active_vpn = random.choice(VPN)
    print(active_vpn)
    kill = "sudo killall openvpn" #horrible, si encuentras otra solucion ponla aca
    command = "sudo openvpn --config "+ active_vpn +" --auth-user-pass auth.in"
    FNULL = open(os.devnull, 'w')
    subprocess.call(kill.split(), stdout=FNULL, stderr=subprocess.STDOUT)
    subprocess.Popen(command.split(), stdout=FNULL, stderr=subprocess.STDOUT)
    time.sleep(6)

def load_vpn(vpn_dir):
    vpn = os.listdir(vpn_dir)
    vpn = list(map(lambda x: "vpn/"+x,vpn))
    return vpn

def load_agents(filename):
    with open(filename, 'r', encoding='utf-8') as f:    
        agents = f.readlines()
    if agents:    
        agents = [x.replace('\u2028','').strip() for x in agents]
    return agents

AGENTS = load_agents("agents.txt")
VPN = load_vpn("vpn")

def user_agent(headers):
    def wrap(f):
        def wrapped_f(*args):
            resp = None
            retries = 2
            while retries > 0:
                change_vpn()
                headers['user-agent'] = change_agent()
                resp = f(*args)
                if resp > 0: 
                    retries = 0
                else: 
                    retries -= 1
                    headers['user-agent'] = random.choice(AGENTS)
                    #cambio de ip
                    time.sleep(10)
            return resp
        return wrapped_f
    return wrap

