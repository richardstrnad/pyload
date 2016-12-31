# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import print_function
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import object
from builtins import COREDIR
from imp import find_module
from os.path import join, exists
from urllib.parse import quote


ENGINE = ""

DEBUG = False
JS = False
PYV8 = False
NODE = False
RHINO = False

# TODO: Refactor + clean up this class

if not ENGINE:
    try:
        import subprocess

        subprocess.Popen(["js", "-v"], bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        p = subprocess.Popen(["js", "-e", "print(23+19)"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        #integrity check
        if out.strip() == "42":
            ENGINE = "js"
        JS = True
    except Exception:
        pass

if not ENGINE or DEBUG:
    try:
        import PyV8
        ENGINE = "pyv8"
        PYV8 = True
    except Exception:
        pass

if not ENGINE or DEBUG:
    try:
        import subprocess
        subprocess.Popen(["node", "-v"], bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        p = subprocess.Popen(["node", "-e", "console.log(23+19)"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        #integrity check
        if out.strip() == "42":
            ENGINE = "node"
        NODE = True
    except Exception:
        pass

if not ENGINE or DEBUG:
    try:
        path = "" #path where to find rhino

        if exists("/usr/share/java/js.jar"):
            path = "/usr/share/java/js.jar"
        elif exists("js.jar"):
            path = "js.jar"
        elif exists(join(COREDIR, "js.jar")): #may raises an exception, but js.jar wasnt found anyway
            path = join(COREDIR, "js.jar")

        if not path:
            raise Exception

        import subprocess

        p = subprocess.Popen(["java", "-cp", path, "org.mozilla.javascript.tools.shell.Main", "-e", "print(23+19)"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        #integrity check
        if out.strip() == "42":
            ENGINE = "rhino"
        RHINO = True
    except Exception:
        pass


class JsEngine(object):
    def __init__(self):
        self.engine = ENGINE
        self.init = False

    def __bool__(self):
        return False if not ENGINE else True

    def set_debug(self, value):
        global DEBUG
        DEBUG = value

    def eval(self, script):
        if not self.init:
            if ENGINE == "pyv8" or (DEBUG and PYV8):
                import PyV8
                global PyV8

            self.init = True

        if isinstance(script, str):
            script = script.encode("utf8")

        if not ENGINE:
            raise Exception("No JS Engine")

        if not DEBUG:
            if ENGINE == "pyv8":
                return self.eval_pyv8(script)
            elif ENGINE == "js":
                return self.eval_js(script)
            elif ENGINE == "node":
                return self.eval_node(script)
            elif ENGINE == "rhino":
                return self.eval_rhino(script)
        else:
            results = []
            if PYV8:
                res = self.eval_pyv8(script)
                print("PyV8:", res)
                results.append(res)
            if JS:
                res = self.eval_js(script)
                print("JS:", res)
                results.append(res)
            if NODE:
                res = self.eval_node(script)
                print("NODE:", res)
                results.append(res)
            if RHINO:
                res = self.eval_rhino(script)
                print("Rhino:", res)
                results.append(res)

            warning = False
            for x in results:
                for y in results:
                    if x != y:
                        warning = True

            if warning: print("### WARNING ###: Different results")

            return results[0]

    def eval_pyv8(self, script):
        rt = PyV8.JSContext()
        rt.enter()
        return rt.eval(script)

    def eval_js(self, script):
        script = "print(eval(unescape('{}')))".format(quote(script))
        p = subprocess.Popen(["js", "-e", script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=-1)
        out, err = p.communicate()
        res = out.strip()
        return res

    def eval_node(self, script):
        script = "console.log(eval(unescape('{}')))".format(quote(script))
        p = subprocess.Popen(["node", "-e", script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=-1)
        out, err = p.communicate()
        res = out.strip()
        return res

    def eval_rhino(self, script):
        script = "print(eval(unescape('{}')))".format(quote(script))
        p = subprocess.Popen(["java", "-cp", path, "org.mozilla.javascript.tools.shell.Main", "-e", script],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=-1)
        out, err = p.communicate()
        res = out.strip()
        return res.decode("utf8").encode("ISO-8859-1")

    def error(self):
        return _("No js engine detected, please install either Spidermonkey, ossp-js, pyv8, nodejs or rhino")
