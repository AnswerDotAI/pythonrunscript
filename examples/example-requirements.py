#!/usr/bin/env pythonrunscript
#
# /// pythonrunscript-requirements-txt
# tqdm==4.66.4
# ///
#
from tqdm import tqdm
import sys

print("Hello, I depend on the tqdm package!")
for i in tqdm(range(10000)):
    pass
print("Phew. That was fun!")
