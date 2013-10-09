# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import platform
import tempfile
import os

import pexpect
import unittest
import PexpectTestCase

# the program cat(1) may display ^D\x08\x08 when \x04 (EOF, Ctrl-D) is sent
_CAT_EOF = '^D\x08\x08'

class UnicodeTests(PexpectTestCase.PexpectTestCase):
    def test_expect_basic (self):
        p = pexpect.spawnu('cat')
        p.sendline('Hello')
        p.sendline('there')
        p.sendline('Mr. þython') # þ is more like th than p, but never mind
        p.expect('Hello')
        p.expect('there')
        p.expect('Mr. þython')
        p.sendeof ()
        p.expect (pexpect.EOF)

    def test_expect_exact_basic (self):
        p = pexpect.spawnu('cat')
        p.sendline('Hello')
        p.sendline('there')
        p.sendline('Mr. þython')
        p.expect_exact('Hello')
        p.expect_exact('there')
        p.expect_exact('Mr. þython')
        p.sendeof()
        p.expect_exact (pexpect.EOF)

    def test_expect_echo (self):
        '''This tests that echo can be turned on and off.
        '''
        p = pexpect.spawnu('cat', timeout=10)
        self._expect_echo(p)

    def test_expect_echo_exact (self):
        '''Like test_expect_echo(), but using expect_exact().
        '''
        p = pexpect.spawnu('cat', timeout=10)
        p.expect = p.expect_exact
        self._expect_echo(p)

    def _expect_echo (self, p):
        p.sendline('1234') # Should see this twice (once from tty echo and again from cat).
        index = p.expect (['1234', 'abcdé', 'wxyz', pexpect.EOF, pexpect.TIMEOUT])
        assert index == 0, (index, p.before)
        index = p.expect (['1234', 'abcdé', 'wxyz', pexpect.EOF])
        assert index == 0, index
        p.setecho(0) # Turn off tty echo
        p.sendline('abcdé') # Now, should only see this once.
        p.sendline('wxyz') # Should also be only once.
        index = p.expect ([pexpect.EOF,pexpect.TIMEOUT, 'abcdé', 'wxyz', '1234'])
        assert index == 2, index
        index = p.expect ([pexpect.EOF, 'abcdé', 'wxyz', '7890'])
        assert index == 2, index
        p.setecho(1) # Turn on tty echo
        p.sendline('7890') # Should see this twice.
        index = p.expect ([pexpect.EOF, 'abcdé', 'wxyz', '7890'])
        assert index == 3, index
        index = p.expect ([pexpect.EOF, 'abcdé', 'wxyz', '7890'])
        assert index == 3, index
        p.sendeof()

    def test_log_unicode(self):
        msg = "abcΩ÷"
        filename_send = tempfile.mktemp()
        filename_read = tempfile.mktemp()
        p = pexpect.spawnu('cat')
        if platform.python_version_tuple() < ('3', '0', '0'):
            import codecs
            def open(fname, mode, **kwargs):
                if 'newline' in kwargs:
                    del kwargs['newline']
                return codecs.open(fname, mode, **kwargs)
        else:
            import io
            open = io.open

        p.logfile_send = open(filename_send, 'w', encoding='utf-8')
        p.logfile_read = open(filename_read, 'w', encoding='utf-8')
        p.sendline(msg)
        p.sendeof()
        p.expect(pexpect.EOF)
        p.close()
        p.logfile_send.close()
        p.logfile_read.close()

        # ensure the 'send' log is correct,
        with open(filename_send, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), msg + '\n\x04')

        # ensure the 'read' log is correct,
        with open(filename_read, 'r', encoding='utf-8', newline='') as f:
            output = f.read().replace(_CAT_EOF, '')
            self.assertEqual(output, (msg + '\r\n')*2 )


    def test_spawn_expect_ascii_unicode(self):
        # A bytes-based spawn should be able to handle ASCII-only unicode, for
        # backwards compatibility.
        p = pexpect.spawn('cat')
        p.sendline('Camelot')
        p.expect('Camelot')

        p.sendline('Aargh')
        p.sendline('Aårgh')
        p.expect_exact('Aargh')
        try:
            p.expect_exact('Aårgh')
            assert False, 'should have raised UnicodeEncodeError'
        except UnicodeEncodeError, err:
            # basically assert the error that this fork of pexpect was meant to
            # resolve, 'ascii' codec can't encode character u'\xe5' in
            #          position 1: ordinal not in range(128)
            pass

        p.sendeof()
        p.expect(pexpect.EOF)

    def test_spawn_send_unicode(self):
        # A bytes-based spawn should be able to send arbitrary unicode
        p = pexpect.spawn('cat')
        p.sendline('3½')
        p.sendeof()
        p.expect(pexpect.EOF)

    def test_utf8_driven_editor (self):
        # requires 'ed' editor
        if pexpect.which('ed') is None:
            self.skipTest('ed(1) not found in path')

        p = pexpect.spawnu('ed UTF-8-demo.txt')
#                encoding='utf-8',
#                env={'LANG':'en_US.UTF-8'})
        # should report some number of characters upon opening
        p.expect(u'14052', timeout=1)
        # Search for term 'Greek anthem', then print the 2nd line following,
        p.sendline(u'/Greek anthem/2p')
        # echo back, and result
        p.expect(u'/Greek anthem/2p', timeout=1)
        p.expect(u'Σὲ γνωρίζω ἀπὸ τὴν κόψη', timeout=1)
#        p.expect(u'\u03a3\u1f72 \u03b3\u03bd\u03c9\u03c1\u1f77\u03b6\u03c9 '
#                 u'\u1f00\u03c0\u1f78 \u03c4\u1f74\u03bd \u03ba\u1f79\u03c8\u03b7', timeout=1)
        # bye!
        p.sendline('q')
        p.expect('q', timeout=1)

    def test_utf8_driven_vim (self):
        # requires 'vim' editor
        if pexpect.which('vim') is None:
            self.skipTest('vim(1) not found in path')

        p = pexpect.spawnu('vim --nofork UTF-8-demo.txt')
#                encoding='utf-8',
#                env={'LANG':'en_US.UTF-8'})
        # should report some number of characters upon opening
        p.expect(u'14052', timeout=1)
        # Search for term 'Greek anthem', then print the 2nd line following,
        p.send('0G')
        p.sendline(u'/Greek anthem')
        p.send('jj')
        # echo back, and result
#        p.expect(u'/Greek anthem/2p', timeout=1)
        p.expect(u'Σὲ γνωρίζω ἀπὸ τὴν κόψη', timeout=1)
#        p.expect(u'\u03a3\u1f72 \u03b3\u03bd\u03c9\u03c1\u1f77\u03b6\u03c9 '
#                 u'\u1f00\u03c0\u1f78 \u03c4\u1f74\u03bd \u03ba\u1f79\u03c8\u03b7', timeout=1)
        # bye!
        p.sendline('!q')
        p.expect('!q', timeout=1)


if __name__ == '__main__':
    unittest.main()

suite = unittest.makeSuite(UnicodeTests, 'test')
