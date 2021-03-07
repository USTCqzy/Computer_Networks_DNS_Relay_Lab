import socket
import multiprocessing
import threading
import time
# global
config_dic = {}
QNAMEPOSITION = 12
count = 0

def byte_to_bitstr(one_byte):
    str = bin(one_byte)[2:]
    end = '0'*(8-len(str))+str
    return end

def getQname(data): # according the rule
    i = QNAMEPOSITION
    Qname = ""
    while data[i] != 0:
        for j in range(1, data[i]+1):
            Qname += chr(data[i+j])
        Qname += '.'
        i += data[i]+1
    return Qname[:-1], i+1

def handle(receive_message, respond_message):
    global count
    bit_str = byte_to_bitstr(receive_message[2])
    if bit_str[:6] == "000000": # is_query
        Qname, next_bit = getQname(receive_message)
        print(count)
        count += 1
        print("Qname", Qname)
        if Qname in config_dic:
            fix_ip = config_dic[Qname]
            print("find the ip in the dic:", fix_ip)
            if fix_ip == "0.0.0.0":
                print("intercept")
            else:
                print("local resolve")
            # create the response
            response = receive_message[:2]
            response += b'\x81\x80'  # Flags: 0x8180 Standard query response, No error
            response += b'\x00\x01'  # Questions: 1
            response += b'\x00\x01'  # Answer RRs: 1
            response += b'\x00\x00'  # Authority RRs: 0
            response += b'\x00\x00'  # Additional RRs: 0
            response += receive_message[QNAMEPOSITION:]
            response += b'\xC0\x0C'  # point to qname
            response += b'\x00\x01'  # TYPE:A Todo?
            response += b'\x00\x01'  # Class: IN (0x0001)
            response += b'\x00\x00\x02\x58'  # Time to live: 600
            response += b'\x00\x04'  # Data length: 4
            ip_list = fix_ip.split(".")
            for ip in ip_list:
                response += int(ip).to_bytes(length=1, byteorder='big')
            return response
        else:
            print("relay")
            return respond_message
    else: # no
        return respond_message

def thread_receive(socket53, data, address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #server_address = ('8.8.8.8', 53) # Google
    server_address = ('223.5.5.5', 53) # ali
    sent = sock.sendto(data, server_address)
    
    try:
        response, _ = sock.recvfrom(4096)
        #print("handle response message...")
        starttime = time.time()
        result = handle(data, response)
        endtime = time.time()
        print("cost time:", endtime - starttime,"secs")
        #print("result", result)
        sent = socket53.sendto(result, address)
        #print("sent", sent)
    except socket.timeout:
        sock.close()
    finally:
        sock.close()
    return

# make the dictionary
def read_config():
    global config_dic
    #file_object = open('../Example_config_file.txt','r')
    file_object = open('./config_file.txt','r')
    try:
        for line in file_object:
            line_split = line.split()
            config_dic[line_split[1]] = line_split[0]
    finally:
        file_object.close()

def receive():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the port
    server_address = ('localhost', 8053)
    print('starting up on {} port {}'.format(*server_address))
    sock.bind(server_address)
    while True:
        data, address = sock.recvfrom(4096)
        #print("data", data)
        #print("address", address)
        thread = threading.Thread(target=thread_receive, args=(sock, data, address))
        thread.start()
        thread.join(timeout = 5)
    sock.close()
    return

def main():
    read_config()

    receiver = multiprocessing.Process(target=receive)
    receiver.start()
    receiver.join()

if __name__ == '__main__':
    main()