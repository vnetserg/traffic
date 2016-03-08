#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import argparse, os, re, dpkt, itertools
from subprocess import Popen, PIPE

from reassemble_tcp import tcp_streams, ip_address

def dpi(file):
    pipe = Popen(["ndpiReader", "-i", file, "-v2"], stdout=PIPE)
    raw = pipe.communicate()[0].decode("utf-8")
    reg = re.compile(r'\[proto: [\d+\.]*\d+\/(\w+\.?\w+)*\]')
    protos = [proto for proto in re.findall(reg, raw)]
    if len(protos) > 2:
        print("[WARNING] File {} has more than 1 flow, skipping".format(file))
    elif len(set(protos)) > 1:
        print("[WARNING] File {} is recognised controversially, skipping".format(file))
    else:
        return protos[0].split(".")

def get_html_mime(file):
    pcap = dpkt.pcap.Reader(open(file, "rb"))

    pkt = next(itertools.islice(pcap, 1, 2))[1]
    eth = dpkt.ethernet.Ethernet(pkt)
    ip_src, ip_dst = ip_address(eth.data.src), ip_address(eth.data.dst)
    port_src, port_dst = eth.data.data.sport, eth.data.data.dport

    streams = tcp_streams([dpkt.ethernet.Ethernet(raw).data
                           for ts, raw in pcap])
    st = streams[(ip_src, port_src, ip_dst, port_dst)]
    try:
        resp = dpkt.http.Response(st)
    except:
        return "unknown"
    else:
        return resp.headers.get("content-type", "unknown").split(";")[0]

def cp(frm, to):
    with open(frm, "rb") as out:
        with open(to, "wb") as in_:
            in_.write(out.read())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="+", help="pcap file with single flow")
    parser.add_argument("-d", "--dir", help="directory to place flow groups", default=".")
    parser.add_argument("-s", "--subproto", help="detect subprotocols", action="store_true")
    parser.add_argument("-m", "--mime", help="parse HTML MIME info", action="store_true")
    parser.add_argument("-m2", "--mimemore", help="parse HTML MIME info with subcategories", action="store_true")
    args = parser.parse_args()
    for file in args.file:
        proto = dpi(file)
        if proto is None: continue
        path = os.path.join(args.dir, *(proto[:1+int(args.subproto)]))
        if proto[0] == u"HTTP" and (args.mime or args.mimemore):
            mime = get_html_mime(file).replace("/", ".")
            if not args.mimemore:
                mime = mime.split(".")[0]
            path = os.path.join(path, mime)
        if not os.path.exists(path):
            os.makedirs(path)
        cp(file, os.path.join(path, os.path.split(file)[-1]))

if __name__ == "__main__":
    main()