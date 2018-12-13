import sys
import time
import subprocess
import os
import threading


'''
if len(sys.argv) < 2:
    print "Specify the input file as argument"
    sys.exit()

# dato che passiamo valori da terminale, siamo (quasi) sicuri sia una stringa
file_input = str(sys.argv[1])

tok_file_input = file_input.split(".")

if tok_file_input[-1] != "txt":
    print "The input file must be a txt file"
    sys.exit(-1)

try:
    filein = open(file_input, 'r')
except Exception as e:
    print "EXCEPTION while opening ", file_input, ",exit"
    sys.exit(-1)

file_output = "".join(tok_file_input[:-2]) + "_result_" + int(time.time()) + tok_file_input[-1]

fileout = open(file_output,"w")

'''
#GLOBAL CONSTANTS

SERVER_ADDRESS = '0.0.0.0'
SERVER_IPERF_PORT = 5201
pipe_name = 'pipe_iperf_measurement'

#GLOBAL VARIABLES
keep_executing = True


#SUPPORT FUNCTIONS AND THREADS

def toKilo(control,value):

    value = str_to_float(value)[1]
    if control[0]=="M":
        value = value * 1000
    if control[0]== "G":
        value = value * 1000000

    return value

def str_to_float(val):

    try:
        val_float=float(val)
    except ValueError:
        return False,0

    return True,val_float


def UDPiperfthread():

    #in theory this thread should never terminate
    print "UDPiperfthread:  launching UDP test with iperf3 server"

    global keep_executing
    pipeout = os.open(pipe_name, os.O_WRONLY)
    process_to_open = 'stdbuf -oL iperf3 -s -V' #default port 5201


    p = subprocess.Popen(process_to_open, shell=True, stdout=pipeout,stderr=pipeout, close_fds=True)

    p.wait()
    #udp_stream_active = False

    print "UDPiperfthread: after p.wait() now i will start waiting"

    while keep_executing:
        time.sleep(1)


    print "UDPiperfthread:  Exiting..."



#MAIN THREAD

if len(sys.argv) < 2:
    print "Specify the output file as argument (without extension)"
    sys.exit()


# dato che passiamo valori da terminale, siamo (quasi) sicuri sia una stringa
file_output = "./results/" + str(sys.argv[1]) + "_" + str(int(time.time())) + ".txt"



try:
    fileout = open(file_output, "w")
except Exception as e:
    print "EXCEPTION while opening ", file_output, ",exit"
    print e
    sys.exit(-1)

#initialize the pipe between UDPiperfthread and computemetricsthread
if not os.path.exists(pipe_name):
    os.mkfifo(pipe_name)

print "MAIN: initialize threads"



#initialize the thread to receive the udp streaming (start iperf server)
iperf_thread = threading.Thread(target = UDPiperfthread)
iperf_thread.start()


print "MAIN: generating metrics..."
pipein = open(pipe_name, 'r')

try:

    while True:
        line = pipein.readline()[:-1]
        print "MAIN: readline-",line

        if line == "iperf3: the client has terminated":
            print "ERROR: server not reachable anymore"
            break

        tokenize = line.split()

        if len(tokenize) > 2 and tokenize[1] == "error":
            print line
            break

        # real metrics
        if len(tokenize) > 3 and tokenize[3] == 'sec':
            transfer = toKilo(tokenize[5], tokenize[4])
            bandwidth = toKilo(tokenize[7], tokenize[6])
            jitter = str_to_float(tokenize[8])[1]
            received_perc = 100 - str_to_float(tokenize[11].translate(None, '()%'))[1]

            print "transfer:", transfer, "Kb - bandwidth:", bandwidth, "Kb/s - jitter:", jitter, " - received_perc:", received_perc, "%"
            fileout.write(str(int(time.time())) + ":" + str(transfer) + ":" + str(bandwidth) + ":" + str(jitter) + ":" + str(received_perc)+"\n")


except KeyboardInterrupt:
    print "\n#######KeyboardInterrupt#######\nTerminating iperf thread and main thread"



keep_executing = False
pipein.close()


print "MAIN: finished working, now exiting..."

iperf_thread.join()

print "MAIN:iper_thread joined"

sys.exit(1)
