
import time, sys, os


def log(str):
    sys.stdout.write("-----"+str+"\n")
#    sys.stdout.flush()

def wait(value, unit='s'):
    value = int(value)
    print "|><|-- waiting %d %s..." % (value, unit)
    if unit.strip(' \t').lower() == 'ms':
        time.sleep(value / 1000)
    elif unit.strip(' \t').lower() == 'us':
        time.sleep(value / 1000000)
    else:
        time.sleep(value)


def system(command):
    log('Exec- \"' + command + '\"\n')
    return os.system(command)
 