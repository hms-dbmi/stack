#!/usr/bin/env python3
# coding: utf-8

import sys

import logging

logger = logging.getLogger("stack")

# Get the name of the app being built, or 'all' if the whole stack is being built
app = sys.argv[1]
