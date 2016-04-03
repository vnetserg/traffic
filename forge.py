#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from __future__ import division

import argparse, dpkt, os, itertools
import pandas as ps
import numpy as np

FEATURES = [
    "name", "app", "class",
    "bulk0", "bulk1", "bulk2", "bulk3",
    "client_bulksize_avg", "client_bulksize_dev",
    "server_bulksize_avg", "server_bulksize_dev",
    "client_packetsize_avg", "client_packetsize_dev",
    "server_packetsize_avg", "server_packetsize_dev",
    "client_packets_per_bulk", "server_packets_per_bulk",
    "client_effeciency", "server_efficiency",
    "byte_ratio", "payload_ratio",
    "packet_ratio", "proto"
]

def parse_flow(pcap, strip = None):
    ip = dpkt.ethernet.Ethernet(next(pcap.__iter__())[1]).data
    seg = ip.data
    if isinstance(seg, dpkt.tcp.TCP):
        proto = "tcp"
        pcap = itertools.islice(pcap, 3, None) # срезаем tcp handshake
    elif isinstance(seg, dpkt.udp.UDP):
        proto = "udp"
    else:
        raise ValueErrur("Unknown transport protocol: `{}`".format(
            seg.__class__.__name__))

    if strip:
        pcap = itertools.islice(pcap, None, strip)

    client = (ip.src, seg.sport)
    server = (ip.dst, seg.dport)

    client_bulks = []
    server_bulks = []
    client_packets = []
    server_packets = []

    cur_bulk_size = 0
    cur_bulk_owner = "client"
    client_fin = False
    server_fin = False
    for ts, raw in pcap:
        ip = dpkt.ethernet.Ethernet(raw).data
        seg = ip.data
        if (ip.src, seg.sport) == client:
            if client_fin: continue
            if proto == "tcp":
                client_fin = bool(seg.flags & dpkt.tcp.TH_FIN)
            client_packets.append(len(seg))
            if cur_bulk_owner == "client":
                cur_bulk_size += len(seg.data)
            elif len(seg.data) > 0:
                server_bulks.append(cur_bulk_size)
                cur_bulk_owner = "client"
                cur_bulk_size = len(seg.data)
        elif (ip.src, seg.sport) == server:
            if server_fin: continue
            if proto == "tcp":
                server_fin = bool(seg.flags & dpkt.tcp.TH_FIN)
            server_packets.append(len(seg))
            if cur_bulk_owner == "server":
                cur_bulk_size += len(seg.data)
            elif len(seg.data) > 0:
                client_bulks.append(cur_bulk_size)
                cur_bulk_owner = "server"
                cur_bulk_size = len(seg.data)
        else:
            raise ValueError("There is more than one flow in a pcap file!")

    if cur_bulk_owner == "client":
        client_bulks.append(cur_bulk_size)
    else:
        server_bulks.append(cur_bulk_size)

    flow = {
        "bulk0": client_bulks[0] if len(client_bulks) > 0 else 0,
        "bulk1": server_bulks[0] if len(server_bulks) > 0 else 0,
        "bulk2": client_bulks[1] if len(client_bulks) > 1 else 0,
        "bulk3": server_bulks[1] if len(server_bulks) > 1 else 0,
    }

    if client_bulks and client_bulks[0] == 0:
        client_bulks = client_bulks[1:]

    if not client_bulks or not server_bulks:
        return None

    flow.update({
        "client_bulksize_avg": np.mean(client_bulks),
        "client_bulksize_dev": np.std(client_bulks),
        "server_bulksize_avg": np.mean(server_bulks),
        "server_bulksize_dev": np.std(server_bulks),
        "client_packetsize_avg": np.mean(client_packets),
        "client_packetsize_dev": np.std(client_packets),
        "server_packetsize_avg": np.mean(server_packets),
        "server_packetsize_dev": np.std(server_packets),
        "client_packets_per_bulk": len(client_packets)/len(client_bulks),
        "server_packets_per_bulk": len(server_packets)/len(server_bulks),
        "client_effeciency": sum(client_bulks)/sum(client_packets),
        "server_efficiency": sum(server_bulks)/sum(server_packets),
        "byte_ratio": sum(client_packets)/sum(server_packets),
        "payload_ratio": sum(client_bulks)/sum(server_bulks),
        "packet_ratio": len(client_packets)/len(server_packets),
        "proto": int(proto == "tcp")
    })

    return flow

def get_clsnum(folder):
    if folder.startswith("class"):
        try:
            return int(folder[len("class"):])
        except ValueError:
            pass
    raise ValueError("`{}` is not valid class identifier!".format(folder))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", help="directory with classified pcap files")
    parser.add_argument("-o", "--output", help="csv output file", default="flows.csv")
    parser.add_argument("-s", "--strip", help="parse only first NUM packets", type=int)
    args = parser.parse_args()
    flows = {ftr: [] for ftr in FEATURES}
    for clsfolder in os.listdir(args.dir):
        if not os.path.isdir(os.path.join(args.dir, clsfolder)):
            raise ValueError("`{}` is not a folder!".format(clsfolder))
        clsnum = get_clsnum(clsfolder)
        for label in os.listdir(os.path.join(args.dir, clsfolder)):
            for file in os.listdir(os.path.join(args.dir, clsfolder, label)):
                full_path = os.path.join(args.dir, clsfolder, label, file)
                flow = parse_flow(dpkt.pcap.Reader(open(full_path, "rb")), args.strip)
                if flow is not None:
                    flow["name"] = file.split(".")[0]
                    flow["app"] = label
                    flow["class"] = clsnum
                    assert len(flow.keys()) == len(FEATURES)
                    for key in flows.iterkeys():
                        flows[key].append(flow[key])
    data = ps.DataFrame(flows)
    data.to_csv(args.output, index=False)

if __name__ == "__main__":
    main()