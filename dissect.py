#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import argparse, dpkt, os
from math import log

def get_flows(pcap, unidir=False):
    if unidir:
        make_key = lambda ip, tr: (ip.src, ip.dst, tr.sport, tr.dport, tr.__class__)
    else:
        make_key = lambda ip, tr: (frozenset(((ip.src, tr.sport),(ip.dst, tr.dport))), tr.__class__)
    flows = {}
    for ts, data in pcap:
        eth = dpkt.ethernet.Ethernet(data)
        if eth.type != dpkt.ethernet.ETH_TYPE_IP:
            continue
        ip = eth.data
        if ip.p == dpkt.ip.IP_PROTO_TCP:
            tcp = ip.data
            key = make_key(ip, tcp)
            if key not in flows:
                flows[key] = []
            if (tcp.flags & dpkt.tcp.TH_SYN) and (unidir or
                    not flows[key] or len(flows[key][-1]) > 1):
                flows[key].append([])
            if flows[key]:
                flows[key][-1].append((ts, data))
        elif ip.p == dpkt.ip.IP_PROTO_UDP:
            udp = ip.data
            key = make_key(ip, udp)
            if key not in flows:
                flows[key] = [[(ts, data)]]
            elif ts - flows[key][-1][-1][0] > 64:
                flows[key].append([(ts, data)])
            else:
                flows[key][-1].append((ts, data))
    return [flow for fls in flows.values() for flow in fls]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="+", help="pcap file with captured packets")
    parser.add_argument("-d", "--dir", help="directory to place flow files", default=".")
    parser.add_argument("-u", "--unidir", help="make a separate flow for each direction", action="store_true")
    args = parser.parse_args()
    flows = []
    for file in args.file:
        pcap = dpkt.pcap.Reader(open(file, "rb"))
        flows += get_flows(pcap, args.unidir)
    for i, flow in enumerate(flows):
        outfile = dpkt.pcap.Writer(open(os.path.join(args.dir,
            ("flow{:0" + str(int(log(len(flows),10)+0.5)) + "}.pcap").format(i)), "wb"))
        for ts, pkt in flow:
            outfile.writepkt(pkt, ts)
        outfile.close()

if __name__ == "__main__":
    main()