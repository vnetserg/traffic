#!/usr/bin/python3.4
# -*- coding: utf-8 -*-

import os, argparse, subprocess

classes = {
    0: [
        "HTTP/text",
        "HTTP/image",
        "DNS",
        "BitTorrent",
        "Skype/other",
        "Quic/other",
        ("SSL/other", "SSL_No_Cert"),
    ],
    1: [
        "HTTP/video",
        "HTTP/audio",
        "Quic/multimedia",
        "SSL/multimedia"
    ],
    2: [
        "Skype/realtime"
    ]
}

def cp(frm, to):
    assert os.path.exists(frm)
    subprocess.call(["ln", frm, to])
    #with open(frm, "rb") as out:
    #    with open(to, "wb") as in_:
    #        in_.write(out.read())

def harvest_folder(path, blacklist):
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isdir(file_path):
            yield from harvest_folder(file_path, blacklist)
        elif file not in blacklist:
            yield file_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="directory with sorted pcap files")
    parser.add_argument("-t", "--targetdir", help="directory to place grabbed pcap files", default=".")
    parser.add_argument("-a", "--all", help="grab all flows", action="store_true")
    args = parser.parse_args()
    processed_files = set()
    for cls, subdirs in classes.items():
        cls_dir = os.path.join(args.targetdir, "class{}".format(cls))
        if not os.path.exists(cls_dir):
            os.makedirs(cls_dir)
        for subdir in subdirs:
            if type(subdir) == str:
                subdir = (subdir,)
            for same_dir in subdir:
                path = os.path.join(args.path, *(same_dir.split("/")))
                if not os.path.exists(path): continue
                for file in os.listdir(path):
                    dst_folder = os.path.join(cls_dir, subdir[0].replace("/", "."))
                    if not os.path.exists(dst_folder):
                        os.makedirs(dst_folder)
                    cp(os.path.join(path, file), os.path.join(dst_folder, file))
                    if args.all:
                        processed_files.add(file)
    if args.all:
        os.makedirs(os.path.join(args.targetdir, "class0", "Other"))
        for file in harvest_folder(args.path, processed_files):
            cp(file, os.path.join(args.targetdir, "class0", "Other", os.path.split(file)[1]))

if __name__ == "__main__":
    main()