#!/usr/bin/env python

import os
import sys
import socket
import struct
import select
import time
import threading


default_timer = time.time

ICMP_ECHO_REQUEST = 8  
#Checksum function
def checksum(source_string):
    
    sum = 0
    countTo = len(source_string)
    count = 0
    while count < countTo:
        thisVal = source_string[count + 1] * 256 + source_string[count]
        sum = sum + thisVal
        count = count + 2

    if countTo < len(source_string):
        sum = sum + ord(source_string[len(source_string) - 1])

    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff

    # Swap bytes. Bugger me if I know why.
    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer

def recieve_ping(client,ID,timeout):
    timeleft=timeout
    while True:
        start=default_timer()
        ready=select.select([client],[],[],timeleft)
        select_duration=(default_timer() - start)
        if ready[0]==[]:
            return
        
        timerecv=default_timer()
        
        packet,addr=client.recvfrom(1024)
        
        icmpHeader= packet[20:28]
        type,code,checksum, packetID, sequence = struct.unpack(
            "bbHHh", icmpHeader
        )
        #filter out echo request
        if type != 8 and packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timesent = struct.unpack("d", packet[28:28 + bytesInDouble])[0]
            return timerecv - timesent
        
        timeleft-=select_duration
        
        if timeleft<0:
            return
        
        
def send_ping(client,dest_addr,ID):
    #apply dns
    dest_addr=socket.gethostbyname(dest_addr)
    
    cs=0
    #bbHHh is format string representing two signed char, two unsigned char and one short
    header=struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, cs, ID, 1)
    bytesInDouble = struct.calcsize("d")
    data = (192 - bytesInDouble) * "Q"
    data = struct.pack("d", default_timer()) + data.encode()
    
    cs=checksum(header+data)
    
    header=struct.pack("bbHHh",ICMP_ECHO_REQUEST,0, socket.htons(cs), ID, 1)
    packet=header+data
    client.sendto(packet,(dest_addr,1))
    
    
def do_one(dest_addr,timeout):
    icmp_protocol=socket.getprotobyname("icmp")
    client=socket.socket(socket.AF_INET,socket.SOCK_RAW,icmp_protocol)
    client_ID=threading.current_thread().ident & 0xFFFF
    send_ping(client,dest_addr,client_ID)
    rtt=recieve_ping(client,client_ID,timeout)
    client.close()
    return rtt

def multi_ping(dest_addr,timeout,count):
    for i in range(count):
        print("ping '{}' ... ".format(dest_addr), end='')
        try:
            rtt=do_one(dest_addr,timeout)
        except socket.gaierror as e:
            print("Error.")
            break
        
        if rtt is None:
            print("Timeout > {}s".format(timeout))
        else:
            rtt+=1000
            print("RTT is {}ms".format(int(rtt)))
        print
        
host=input("Give a hostname or IP you want to ping or recieve: ")
#default. Can change if wanted
timeout=10
count=10
multi_ping(host,timeout,count)


        
