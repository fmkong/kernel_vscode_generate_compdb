#!/bin/bash

product='HU_SS3'
android_root_dir=$(dirname $(dirname $(dirname "$(cd "$(dirname "$0")";pwd)")))
python3 generate_compdb_kernel.py --target $product \
    --android_root $android_root_dir \
    --docker_android_root $HOME/workspace/lagvm/LINUX/android/
