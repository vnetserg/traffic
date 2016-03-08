#!/usr/bin/python2.7

# $Id$
#
# Adapted from code by Tim Newsham.

import dpkt


def compare_by_sequence(a, b):

      """Compares a and b by the value of their .seq attributes."""

      return int(a.seq - b.seq)


def ip_address(bytes):
      return ".".join([str(ord(b)) for b in bytes])


def ethernet_frames(packets):

      """Given a sequence of raw packets, yields dpkt.ethernet.Ethernet
objects for each packet. If the packet is not an Ethernet frame, it is
skipped and the next packet is tried."""

      for p in packets:
            try:
                  yield dpkt.ethernet.Ethernet(p)
            except dpkt.dpkt.NeedData, e:
                  continue


def ip_datagrams(frames):

      """Given a sequence of Ethernet frames, yields the enclosed IP
datagrams iff the frame payload is an IP datagram."""

      for f in frames:
            if dpkt.ethernet.ETH_TYPE_IP == f.type:
                  yield f.data


def tcp_streams(datagrams):

      """Given a sequence of IP datagrams returns a dictionary containing
streams of bytes from each direction of a TCP connection. The keys are
(source IP, source port, destination IP, destination port) tuples. IP
datagrams that do not contain TCP packets are skipped."""

      cnctns = { }
      for d in datagrams:
            if d.p != dpkt.ip.IP_PROTO_TCP:
                  continue
            tcp = d.data
            k = (ip_address(d.src), tcp.sport, ip_address(d.dst), tcp.dport)
            if k in cnctns:
                  cnctns[k].append(tcp)
            else:
                  cnctns[k] = [tcp]

      for c in cnctns:
            try:
                  cnctns[c].sort(compare_by_sequence)
                  d = []
                  for p in cnctns[c]:
                        try:
                              d.append(p.data)
                        except AttributeError, e:
                              pass
                  cnctns[c] = "".join(d)
            except TypeError, e:
                  print "Packet:", type(e), str(e)

      return cnctns


if __name__ == "__main__":

      import sys
      from PcapReader import PcapReader

      if 2 != len(sys.argv):
            print "Usage: reassemble.py pcap-file"
            sys.exit(1)

      strms = streams(PcapReader(sys.argv[1]))
      for s in strms:
            print "(begin", str(s), ")"
            print strms[s]
            print "(end", str(s), ")"
            print

