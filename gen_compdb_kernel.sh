#!/bin/bash

product='HU_SS3'
python3 generate_compdb_kernel.py --target $product \
    --android_root /home/fanming/data/work/projects/ss3_8295/code/lagvm/LINUX/android \
    --docker_android_root /home/fanming/workspace/lagvm/LINUX/android/
