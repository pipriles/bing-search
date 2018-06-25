#!/usr/bin/env python3

import random
import time

def load_agents(filename):
    with open(filename, 'r', encoding='utf-8') as f:    
        agents = f.readlines()
    if agents:    
        agents = [x.replace('\u2028','').strip() for x in agents]
    return agents

AGENTS = load_agents("agents.txt")

def user_agent(headers):
    def wrap(f):
        def wrapped_f(*args):
            resp = None
            retries = 2
            while retries > 0:
                    resp = f(*args)
                    if resp > 0: 
                        retries = 0
                    else: 
                        retries -= 1
                        headers['user-agent'] = random.choice(AGENTS)
                        time.sleep(3)
            return resp
        return wrapped_f
    return wrap