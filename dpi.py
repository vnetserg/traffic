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

    try:
        pkt = next(itertools.islice(pcap, 1, 2))[1]
    except StopIteration:
        return "unknown"
    
    eth = dpkt.ethernet.Ethernet(pkt)
    ip_src, ip_dst = ip_address(eth.data.src), ip_address(eth.data.dst)
    port_src, port_dst = eth.data.data.sport, eth.data.data.dport

    streams = tcp_streams([dpkt.ethernet.Ethernet(raw).data
                           for ts, raw in pcap])
    st = streams[(ip_src, port_src, ip_dst, port_dst)]

    types = {}
    while "HTTP/" in st:
        st = st[st.find("HTTP/"):]
        try:
            resp = dpkt.http.Response(st)
        except dpkt.dpkt.UnpackError:
            print("`{}`: invalid http packet".format(file))
            break
        if "content-type" in resp.headers:
            cont = resp.headers["content-type"]
            types[cont] = types.get(cont, 0) + int(resp.headers.get("content-length", 1))
        st = st[st.find("\r\n\r\n")+len("\r\n\r\n"):]
        if "content-length" in resp.headers:
            st = st[int(resp.headers["content-length"]):]

    if not types: return "unknown"
    return max(types.items(), key=lambda t: t[1])[0]

def is_realtime_heuristic(file):
    pcap = dpkt.pcap.Reader(open(file, "rb"))
    t1 = min(pcap, key=lambda x: x[0])[0]
    t2 = max(pcap, key=lambda x: x[0])[0]
    if t2 - t1 > 3 and sum(1 for _ in pcap)/(t2-t1) > 50:
        return True
    else:
        return False

def is_multimedia_heuristic(file):
    return os.path.getsize(file) > 2**20

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
    parser.add_argument("-m2", "--mime2", help="parse HTML MIME info with subcategories", action="store_true")
    parser.add_argument("-r", "--realtime", help="apply realtime heuristic for Skype", action="store_true")
    parser.add_argument("-q", "--quic", help="apply heuristic to QUIC to detect multimedia", action="store_true")
    args = parser.parse_args()
    for file in args.file:
        proto = dpi(file)
        if proto is None: continue
        path = os.path.join(args.dir, *(proto[:1+int(args.subproto)]))
        if proto[0] == u"HTTP" and (args.mime or args.mime2):
            mime = get_html_mime(file).replace("/", ".")
            if not args.mime2:
                mime = mime.split(".")[0]
            path = os.path.join(path, mime)
        elif proto[0] == u"Skype" and args.realtime:
            if is_realtime_heuristic(file):
                path = os.path.join(path, "realtime")
            else:
                path = os.path.join(path, "best_effort")
        elif proto[0] == u"Quic":
            if is_multimedia_heuristic(file):
                path = os.path.join(path, "multimedia")
            else:
                path = os.path.join(path, "other")
        if not os.path.exists(path):
            os.makedirs(path)
        cp(file, os.path.join(path, os.path.split(file)[-1]))

if __name__ == "__main__":
    main()