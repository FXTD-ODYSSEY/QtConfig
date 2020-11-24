# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2020-11-02 23:47:53"

import os
import sys
import six
import json
import types
import inspect
from functools import partial

import Qt
from Qt import QtCore, QtWidgets, QtGui

from .binding import Binding
from .util import nestdict, defaultdict

HOOKS = nestdict()
_HOOKS_REL = nestdict()
qt_dict = {"QtWidgets.%s" % n: m for n, m in inspect.getmembers(QtWidgets)}
qt_dict.update({"QtCore.%s" % n: m for n, m in inspect.getmembers(QtCore)})
qt_dict.update({"QtGui.%s" % n: m for n, m in inspect.getmembers(QtGui)})


def byte2str(text):
    # NOTE compat python 2 and 3
    return str(text, encoding="utf-8") if sys.hexversion >= 0x3000000 else str(text)


def get_method_name(method):
    # NOTE compat Qt 4 and 5
    version = QtCore.qVersion()
    name = ""
    count = False
    if version.startswith("5"):
        name = method.name()
        count = method.parameterCount()
    elif version.startswith("4"):
        name = method.signature()
        name = name.split("(")[0]
        count = method.parameterNames()
    return byte2str(name), count


# NOTE read filter func list
path = os.path.join(__file__, "..", "hook.json")
with open(path, "r") as f:
    filter_method = json.load(f, encoding="utf-8")

for name, member in qt_dict.items():

    for method_name, method in inspect.getmembers(member, inspect.isroutine):
        if filter_method.get(name, {}).get(method_name):
            HOOKS[name][method_name] = {}
            _HOOKS_REL[name][method_name.lower()] = method_name

    # for i in range(meta_obj.methodCount()):
    #     method = meta_obj.method(i)
    #     method_name, count = get_method_name(method)
    #     if count and method.methodType() != QtCore.QMetaMethod.Signal:
    #         if hasattr(member, method_name):
    #             HOOKS[name][method_name] = {}
    #             _HOOKS_REL[name][method_name.lower()] = method_name

    if not hasattr(member, "staticMetaObject"):
        continue
    meta_obj = getattr(member, "staticMetaObject")
    # NOTE auto bind updater
    for i in range(meta_obj.propertyCount()):
        property = meta_obj.property(i)
        if not property.hasNotifySignal():
            continue
        property_name = property.name()
        method_name = _HOOKS_REL[name].get("set%s" % property_name.lower())
        data = HOOKS[name].get(method_name)
        if isinstance(data, dict):
            updater, _ = get_method_name(property.notifySignal())
            if updater:
                data.update({"updater": updater, "property": property_name})

def binding_handler(func, options=None):
    """
    # NOTE initialize the Qt Widget setter
    """
    options = options if options is not None else {}

    def fix_cursor_position(func, widget):
        """maintain the Qt edit cusorPosition after setting a new value"""

        def wrapper(*args, **kwargs):
            pos = widget.property("cursorPosition")
            res = func(*args, **kwargs)
            QtCore.QTimer.singleShot(
                0, lambda: widget.setProperty("cursorPosition", pos)
            ) if pos else None
            return res

        return wrapper

    def auto_dump(binding):
        """auto dump for two way binding"""
        from .constant import AUTO_DUMP

        binder = binding.__binder__
        if not AUTO_DUMP or not binder:
            return
        dumper = binder("dumper")
        for k, v in binder._var_dict_.items():
            if v is binding:
                # print("auto_dump", dumper.path, k)
                dumper._filters_.add(k)
                break

    def combine_args(val, args):
        if isinstance(val, tuple):
            return val + args[1:]
        else:
            return (val,) + args[1:]

    @six.wraps(func)
    def wrapper(self, *args, **kwargs):
        if len(args) == 0:
            return func(self, *args, **kwargs)

        callback = args[0]

        if isinstance(callback, types.LambdaType):

            # NOTE get the running bindings (with __get__ method) add to Binding.TRACE_LIST
            with Binding.set_trace():
                val = callback()

            def connect_callback(callback, args):
                val = callback()
                args = combine_args(val, args)
                func(self, *args, **kwargs)

            # NOTE register auto update
            _callback_ = partial(connect_callback, callback, args)
            for binding in Binding._trace_list_:
                binding.connect(_callback_)
                # binding.bind_widgets.append(
                #     self
                # ) if self not in binding.bind_widgets else None

            args = combine_args(val, args)

            # NOTE Single binding connect to the updater
            updater = options.get("updater")
            prop = options.get("property")
            getter = options.get("getter")
            _getter_1 = getattr(self, getter) if getter else None
            _getter_2 = lambda: self.property(prop) if prop else None
            getter = _getter_1 if _getter_1 else _getter_2
            code = callback.__code__

            if (
                updater
                and getter
                and len(Binding._trace_list_)
                == 1  # NOTE only bind one response variable
                and len(code.co_consts) == 1  # NOTE only bind directly variable
            ):
                updater = getattr(self, updater)
                updater.connect(
                    fix_cursor_position(lambda *args: binding.set(getter()), self)
                )
                binding = Binding._trace_list_.pop()
                QtCore.QTimer.singleShot(0, partial(auto_dump, binding))

        return func(self, *args, **kwargs)

    return wrapper


def hook_initialize(hooks):
    """
    # NOTE Dynamic wrap the Qt Widget setter base on the HOOKS Definition
    """
    for widget, setters in hooks.items():
        lib, widget = widget.split(".")
        widget = getattr(getattr(Qt, lib), widget)
        for setter, options in setters.items():
            wrapper = binding_handler(getattr(widget, setter), options)
            setattr(widget, setter, wrapper)
