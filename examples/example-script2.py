#!/usr/bin/env pythonrunscript
#
# /// script
# requires-python = ">=3.11"
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
