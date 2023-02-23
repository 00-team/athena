from time import time
import json

expier_date = 60 * 60 * 6


filename = "./period_users.json"

DATABASE = {}

def now():
    return int(time())

def check_user(userid):
    global DATABASE
    t = now()
    with open(filename,'r') as f:
        DATABASE = json.load(f)
    if (t + expier_date > DATABASE.get(userid)):
        print("user kirie")
    else:
        print("user koonie")

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
        check_user(test)
        check_result = check_user(test)
        print(check_result)
        if check_result == "user kirie":
            add_users(test)
        else:
            print("user has been period time")

if __name__ == '__main__':
  main()