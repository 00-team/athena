from time import time
import json

filename = "./period_users.json"

DATABASE = {}

def now():
    return int(time())

def add_users(userid):
    global DATABASE
    t = now()
    with open(filename, "r") as f:
        DATABASE = json.load(f)
    DATABASE[userid] = t
    with open(filename, 'w') as f:
        json.dump(DATABASE, f)
    print("user has been saved as : ", json.dumps(DATABASE, indent=4))
        
        
def main():
    while True:
        test = input("-->")
        add_users(test)

if __name__ == '__main__':
  main()