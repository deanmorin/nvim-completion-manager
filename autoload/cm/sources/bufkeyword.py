#!/usr/bin/env python
# -*- coding: utf-8 -*-

# For debugging
# NVIM_PYTHON_LOG_FILE=nvim.log NVIM_PYTHON_LOG_LEVEL=INFO nvim

import os
import re
import logging
from neovim import attach, setup_logging

logger = logging.getLogger(__name__)

class Handler:

    def __init__(self,nvim):

        self._nvim = nvim
        self._words = set()

        self.refresh_keyword()

    def refresh_keyword(self):
        logger.info('refresh_keyword')
        pat = re.compile(r'[^0-9a-zA-Z_]+')
        self._words = set()
        for line in self._nvim.current.buffer[:]:
            for word in re.split(pat,line):
                self._words.add(word)

        logger.info('keyword refresh complete, count: %s', len(self._words))

    def cm_on_changed(self,info,ctx):

        lnum = ctx['curpos'][1]
        col = ctx['curpos'][2]
        line = self._nvim.current.buffer[lnum-1]
        txt = line[0 : col-1]
        
        typed = re.search(r'[0-9a-zA-Z_]*?$',txt).group(0)
        if len(typed)<2:
            return
        startcol = col-len(typed)

        matches = []
        typedLower = typed.lower()
        for word in self._words:
            if word.lower().find(typedLower)==0 and word!=typed:
                
                matches.append(dict(word=word,icase=1))

        # cm#complete(src, context, startcol, matches)
        ret = self._nvim.call('cm#complete', info['name'], ctx, startcol, matches)

        logger.info('on changed, current line: %s, typed: %s, matches: %s, ret: %s', line, typed, matches, ret)

def main():

    # logging setup
    level = logging.INFO
    if 'NVIM_PYTHON_LOG_LEVEL' in os.environ:
        # use nvim's logging
        setup_logging('bufkeyword')
        l = getattr(logging,
                os.environ['NVIM_PYTHON_LOG_LEVEL'].strip(),
                level)
        if isinstance(l, int):
            level = l
    logger.setLevel(level)

    # connect neovim
    nvim = attach('stdio')
    nvim_event_loop(nvim)

def nvim_event_loop(nvim):

    handler = Handler(nvim)

    def on_setup():
        logger.info('on_setup')

    def on_request(method, args):
        raise Exception('Not implemented')

    def on_notification(method, args):
        nonlocal handler
        logger.info('method: %s, args: %s', method, args)

        func = getattr(handler,method,None)
        if func is None:
            return

        func(*args)

    nvim.run_loop(on_request, on_notification, on_setup)

main()

