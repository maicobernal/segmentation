#!/bin/bash
echo "STARTING STORESCP IN PORT 106 WITH AET NAME HIPPOAI"
echo "DATA WILL BE STORED IN /home/received"
storescp 106 -v -aet HIPPOAI -od /home/received --sort-on-study-uid st