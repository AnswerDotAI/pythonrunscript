#!/usr/bin/env pythonrunscript
#
# /// script
# dependencies = [
#   "tqdm==4.66.4",
# ]
# ///
#
from tqdm import tqdm
import sys

print("Hello, I depend on the tqdm package!")
for i in tqdm(range(10000)):
    pass
print("Phew. That was fun!")
