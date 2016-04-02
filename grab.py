#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import os, argparse

classes = {
    0: [
        "HTTP/text",
        "HTTP/image",
        "DNS",
        "BitTorrent",
    ],
    1: [
        "HTTP/video",
        "HTTP/audio",
        "Quic/multimedia"
    ],
    2: [
        "Skype/realtime"
    ]
}

def cp(frm, to):
    with open(frm, "rb") as out:
        with open(to, "wb") as in_:
            in_.write(out.read())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="directory with sorted pcap files")
    parser.add_argument("-t", "--targetdir", help="directory to place grabbed pcap files", default=".")
    args = parser.parse_args()
    for cls, subdirs in classes.items():
        cls_dir = os.path.join(args.targetdir, "class{}".format(cls))
        if not os.path.exists(cls_dir):
            os.makedirs(cls_dir)
        for subdir in subdirs:
            path = os.path.join(args.path, *(subdir.split("/")))
            if not os.path.exists(path): continue
            for file in os.listdir(path):
                dst_folder = os.path.join(cls_dir, subdir.replace("/", "."))
                if not os.path.exists(dst_folder):
                    os.makedirs(dst_folder)
                cp(os.path.join(path, file), os.path.join(dst_folder, file))

if __name__ == "__main__":
    main()