# -*- coding: utf-8 -*-

class _EventHook(object):
    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler):
        if handler in self.__handlers:
            self.__handlers.remove(handler)
        return self

    def fire(self, *a, **k):
        for handler in self.__handlers:
            handler(*a, **k)

    def clearObjectHandlers(self, inObject):
        for handler in self.__handlers:
            if handler.im_self == inObject:
                self -= handler

class _OverrideLib(object):
    def __init__(self):
        self.registerEvent = self.__hookDecorator(self.__registerEvent) 
        self.overrideMethod = self.__hookDecorator(self.__overrideMethod)
        self.overrideClassMethod = self.__hookDecorator(self.__overrideClassMethod)
        self.overrideStaticMethod = self.__hookDecorator(self.__overrideStaticMethod)

    def __logTrace(self, func, debug):
        if debug:
            import traceback
            print traceback.format_exc() #Test

    def __eventHandler(self, func, debug, prepend, e, m, *a, **k):
        try:
            if prepend:
                e.fire(*a, **k)
                r = m(*a, **k)
            else:
                r = m(*a, **k)
                e.fire(*a, **k)
            return r
        except:
            self.__logTrace(func, debug)

    def __overrideHandler(self, func, orig, debug, *a, **k):
        try: 
            return func(orig, *a, **k)
        except:
            self.__logTrace(func, debug)

    def __hookDecorator(self, func):
        def Decorator1(*a, **k):
            def Decorator2(handler):
                func(handler, *a, **k)
            return Decorator2
        return Decorator1

    def __override(self, cls, method, new_method):
        orig = getattr(cls, method)
        if type(orig) is property:
            setattr(cls, method, property(new_method))
        else:
            setattr(cls, method, new_method) 

    def __registerEvent(self, handler, cls, method, debug=True, prepend=False):
        evt = '__event_%i_%s' % (1 if prepend else 0, method)
        if hasattr(cls, evt):
            e = getattr(cls, evt)
        else:
            new_method = '__orig_%i_%s' % (1 if prepend else 0, method)
            setattr(cls, evt, _EventHook())
            setattr(cls, new_method, getattr(cls, method))
            e = getattr(cls, evt)
            m = getattr(cls, new_method)
            l = lambda *a, **k: self.__eventHandler(handler, debug, prepend, e, m, *a, **k)
            l.__name__ = method
            setattr(cls, method, l)
        e += handler

    def __overrideMethod(self, handler, cls, method, debug=True):
        orig = getattr(cls, method)
        new_method = lambda *a, **k: self.__overrideHandler(handler, orig, debug, *a, **k)
        new_method.__name__ = method
        self.__override(cls, method, new_method)

    def __overrideStaticMethod(self, handler, cls, method, debug=True):
        orig = getattr(cls, method)
        new_method = staticmethod(lambda *a, **k: self.__overrideHandler(handler, orig, debug, *a, **k))
        self.__override(cls, method, new_method)

    def __overrideClassMethod(self, handler, cls, method, debug=True):
        orig = getattr(cls, method)
        new_method = classmethod(lambda *a, **k: self.__overrideHandler(handler, orig, debug, *a, **k))
        self.__override(cls, method, new_method)

g_overrideLib = _OverrideLib()
