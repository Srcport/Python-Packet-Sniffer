import pcapy
import sys
import os
from struct import *
import datetime
import atexit
import socket

dev = ""

def manmode():
    os.system("ifconfig " + dev + " down")
    os.system("iwconfig " + dev + " mode managed")
    os.system("ifconfig " + dev + " up")
    print "[+] Network (" + dev + ") reverted to managed mode"

def main():
    try:
		if len(sys.argv) != 2:
		    print "Available devices:"
		    print
		    devices = pcapy.findalldevs()

		    for device in devices:
		        print device

		    print
		    print "Usage: ./%s deviceName", sys.argv[0]
		    exit()

		global dev
		dev = sys.argv[1]

		print "Trying to set monitor mode for device " + dev + "..."
		os.system("ifconfig " + dev + " down")
		os.system("iwconfig " + dev + " mode monitor")
		os.system("ifconfig " + dev + " up")
		print "Done. If you don't see any data, the monitor mode setup may have failed."

		cap = pcapy.open_live(dev, 65536, True, 0)

		print
		print "Listening on %s: net=%s, mask=%s, linktype=%d" % (dev, cap.getnet(), cap.getmask(), cap.datalink())

		(header, packet) = cap.next()
		while header:
		    parse_packet(packet)
		    (header, packet) = cap.next()
    except KeyboardInterrupt:
    	sys.exit(0)

#Convert a string of 6 characters of ethernet address into a dash separated hex string
def eth_addr (a) :
    b = "%.2x:%.2x:%.2x:%.2x:%.2x:%.2x" % (ord(a[0]) , ord(a[1]) , ord(a[2]), ord(a[3]), ord(a[4]) , ord(a[5]))
    return b

#function to parse a packet
def parse_packet(packet) :
     
    #parse ethernet header (mac src/dst + eth type)
    eth_length = 14
    eth_header = packet[:eth_length]
    eth = unpack('!6s6sH' , eth_header)
    eth_protocol = socket.ntohs(eth[2])
    
    print('Destination MAC : ' + eth_addr(packet[0:6]) + 
		  ' Source MAC : ' + eth_addr(packet[6:12]) + 
		  ' Protocol : ' + str(eth_protocol))
 
    #Parse IP packets, IP Protocol number = 8
    if eth_protocol == 8 :
        #Parse IP header
        #take first 20 characters for the ip header
        ip_header = packet[eth_length:20+eth_length]
         
        #now unpack them :)
        iph = unpack('!BBHHHBBH4s4s' , ip_header)
 
        version_ihl = iph[0]
        version = version_ihl >> 4
        ihl = version_ihl & 0xF
 
        iph_length = ihl * 4
 
        ttl = iph[5]
        protocol = iph[6]
        s_addr = socket.inet_ntoa(iph[8]);
        d_addr = socket.inet_ntoa(iph[9]);
 
        print ('Version : ' + str(version) + 
			   ' IP Header Length : ' + str(ihl) + 
			   ' TTL : ' + str(ttl) + 
		 	   ' Protocol : ' + str(protocol) + 
			   ' Source Address : ' + str(s_addr) + 
			   ' Destination Address : ' + str(d_addr))
 
        #TCP protocol
        if protocol == 6 :
            t = iph_length + eth_length
            tcp_header = packet[t:t+20]
 
            tcph = unpack('!HHLLBBHHH' , tcp_header)
             
            source_port = tcph[0]
            dest_port = tcph[1]
            sequence = tcph[2]
            acknowledgement = tcph[3]
            doff_reserved = tcph[4]
            tcph_length = doff_reserved >> 4
             
            print ('Source Port : ' + str(source_port) + 
				   ' Dest Port : ' + str(dest_port) + 
				   ' Sequence Number : ' + str(sequence) + 
			       ' Acknowledgement : ' + str(acknowledgement) + 
				   ' TCP header length : ' + str(tcph_length))
             
            h_size = eth_length + iph_length + tcph_length * 4
            data_size = len(packet) - h_size
             
            #get data from the packet
            data = packet[h_size:]
             
            #print 'Data : ' + data
 
        #ICMP Packets
        elif protocol == 1 :
            u = iph_length + eth_length
            icmph_length = 4
            icmp_header = packet[u:u+4]
 
            #now unpack them :)
            icmph = unpack('!BBH' , icmp_header)
             
            icmp_type = icmph[0]
            code = icmph[1]
            checksum = icmph[2]
             
            print ('Type : ' + str(icmp_type) + 
				   ' Code : ' + str(code) + 
				   ' Checksum : ' + str(checksum))
             
            h_size = eth_length + iph_length + icmph_length
            data_size = len(packet) - h_size
             
            #get data from the packet
            data = packet[h_size:]
             
            #print 'Data : ' + data
 
        #UDP packets
        elif protocol == 17 :
            u = iph_length + eth_length
            udph_length = 8
            udp_header = packet[u:u+8]
 
            #now unpack them :)
            udph = unpack('!HHHH' , udp_header)
             
            source_port = udph[0]
            dest_port = udph[1]
            length = udph[2]
            checksum = udph[3]
             
            print ('Source Port : ' + str(source_port) + 
				   ' Dest Port : ' + str(dest_port) + 
			  	   ' Length : ' + str(length) + 
				   ' Checksum : ' + str(checksum))
             
            h_size = eth_length + iph_length + udph_length
            data_size = len(packet) - h_size
             
            #get data from the packet
            data = packet[h_size:]
             
            #print 'Data : ' + data
 
        #some other IP packet like IGMP
        else :
            print 'Protocol other than TCP/UDP/ICMP'
             
        print


if __name__ == "__main__":
    atexit.register(manmode)
    main()
