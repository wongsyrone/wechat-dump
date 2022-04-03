#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import os
import sys
import argparse
import logging

from wechat.parser import WeChatDBParser
from wechat.res import Resource
from wechat.common.textutil import ensure_unicode
from wechat.render import HTMLRender

logger = logging.getLogger("wechat")

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', help='name of contact',default="_all_")
    parser.add_argument('--output', help='output html file', default='output.html')
    parser.add_argument('--db', default='decrypted.db', help='path to decrypted database')
    parser.add_argument('--avt', default='avatar.index', help='path to avatar.index file that only exists in old version of wechat')
    parser.add_argument('--res', default='resource', help='reseource directory')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()

    name = ensure_unicode(args.name)
    output_file = args.output

    parser = WeChatDBParser(args.db)
    all_chat_ids=parser.all_chat_ids
    if name=="_all_":
        chat_ids=all_chat_ids
    else:
        try:
            chatid = parser.get_chat_id(args.name)
        except KeyError:
            sys.stderr.write(u"Valid Contacts: {}\n".format(
                u'\n'.join(parser.all_chat_nicknames)))
            sys.stderr.write(u"Couldn't find the chat {}.".format(name));
            sys.exit(1)
        chat_ids=[chatid]
    for chatid in chat_ids:
        contact_name=parser.contacts[chatid]
        if len(contact_name)==0:
            contact_name="None"
        path="./"+"result"+"/"+chatid+"_"+contact_name+"/"
        os.makedirs(path, exist_ok=True)

        res = Resource(parser, args.res, args.avt)
        msgs = parser.msgs_by_chat[chatid]
        logger.info(f"Number of Messages for chatid {chatid}: {len(msgs)}")
        assert len(msgs) > 0

        render = HTMLRender(parser, res)
        htmls = render.render_msgs(msgs)

        if len(htmls) == 1:
            with open(path+chatid+'.html', 'w',encoding='utf-8') as f:
                f.write(htmls[0])
        else:
            for idx, html in enumerate(htmls):
                with open(path+chatid+'_{}.html'.format(idx), 'w',encoding='utf-8') as f:
                    f.write(html)
        res.emoji_reader.flush_cache()

