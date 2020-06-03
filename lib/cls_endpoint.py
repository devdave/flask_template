from flask import Flask
from werkzeug.routing import Submount

import inspect
import functools
import typing as T
from dataclasses import dataclass

@dataclass
class ExposedRule:
    uri:str
    route_kwargs:dict


ExposedClassDefinition = T.TypeVar("ExposedClassDefinition")
ExposedClassInstance = T.TypeVar("ExposedClassInstance")

EXPOSED_ID = "_EXPOSED"
EXCLUSIVE_ID = "_EXCLUSIVE"
PREFILTER_ID = "_PREFILTER"
POSTFILTER_ID = "_POSTFILTER"



class CLSEndpointFlask(Flask):
    """
        Adds logic to allow class routing

        > @app.add_class("/foo")
        > class Foo(object):
        >
        >   @app.expose("/bar")  #http://my_website/foo/bar
        >   def do_Bar(self):
        >       return "/foo/bar says hello"

    """

    _instances:T.Dict[str, ExposedClassInstance]

    def __init__(self, *args, **kwargs):
        Flask.__init__(self, *args, **kwargs)  # TODO - Use super() instead?

        # Just as a precaution to prevent the class from being garbage collected
        self._instances = {}

    def _get_name(self, thing:T.Callable):
        name = thing.__qualname__ \
            if hasattr(thing, "__qualname__") else thing.__name__ \
            if hasattr(thing, "__name__") else repr(thing)
        if name.count(".") > 2:
            name = ".".join(name.split(".")[-2:])

        return name




    def _find_exposed(self, cls_def:ExposedClassDefinition, identifier:str=EXPOSED_ID)->T.Iterator:
        """
            Originally I used inspect.getmembers but I kept running into a problem where reserved words (ex 'update')
            weren't being picked up.

        :param cls_def: A class defintion but as written this could be any type of basic object.
        :param identifier: The attribute name to look for.
        :return:
        """
        filter = lambda x: hasattr(x, EXPOSED_ID) and (inspect.ismethod(x) or inspect.isfunction(x))
        for name, thing in inspect.getmembers(cls_def, filter):
            yield self._get_name(thing), thing

    def _find_exclusive(self, cls_def:ExposedClassInstance, identifier:str=EXCLUSIVE_ID)->T.Iterator:
        filter = lambda x: hasattr(x, identifier) and (inspect.ismethod(x) or inspect.isfunction(x))

        for name, member in inspect.getmembers(cls_def, filter):
            yield self._get_name(member), member


    def _find_member(self, cls_def:ExposedClassDefinition, identifier:str)->T.Union[bool, T.Callable]:
        for name, member in inspect.getmembers(cls_def):
            if hasattr(member, identifier) and (inspect.isfunction(member) or inspect.ismethod(member)):
                return member

        return False

    def expose(self, uri:str, **route_args:T.Dict[str, T.Any]):
        """
        Behaves similar to flask.route except it just adds a custom attribute "_EXPOSED" to
            the decorated method or function
        :param uri:
        :param route_args:
        :return:
        """
        def processor(method:T.Callable):
            setattr(method, EXPOSED_ID, ExposedRule(uri, route_args))
            return method

        return processor

    def exclusive_route(self, uri:str, **route_args:T.Dict[str, T.Any]):
        """
        Expose a method but also make it a first-class routed callable as well

        @expose adds a route "__class__.__name__/{uri}
        @exclusive_route "/uri" + exposed above

        :param uri:
        :param route_args:
        :return:
        """

        def processor(method:T.Callable):
            setattr(method, EXCLUSIVE_ID, ExposedRule(uri, route_args))
            return method

        return processor


    def set_prefilter(self, func):
        setattr(func, PREFILTER_ID, True)
        return func

    def _find_prefilter(self, clsdef):
        return self._find_member(clsdef, PREFILTER_ID)

    def set_postfilter(self, func):
        setattr(func, POSTFILTER_ID, True)
        return func

    def _find_postfilter(self, clsdef):
        return self._find_member(clsdef, POSTFILTER_ID)

    def _get_exposed_rules(self, endpoints):
        # time to build the rules
        rules = []
        for endpoint, view_func in endpoints.items():  # type: str, T.Callable
            exposed_rule = getattr(view_func, EXPOSED_ID)  # type: ExposedRule
            methods = exposed_rule.route_kwargs.pop("methods", ["GET"])  # type: T.List[str]

            if methods is None:
                methods = getattr(view_func, "methods", None) or ("GET",)

            rule = self.url_rule_class(exposed_rule.uri, methods=methods, endpoint=endpoint,
                                       **exposed_rule.route_kwargs)
            rules.append(rule)
            if endpoint not in self.view_functions:
                self.view_functions[endpoint] = view_func
            else:
                raise AssertionError(
                    f"View function {view_func} mapping is overwriting an existing endpoint function: {endpoint}"
                )
        return rules

    def _assign_exclusive_rules(self, cls_obj, prefilter, postfilter):
        # Find exclusives
        for qname, exclusive_method in self._find_exclusive(cls_obj):

            if hasattr("exclusive_method", "__wrapped__") is False and (prefilter or postfilter):
                exclusive_method = self._pre_and_postfilter_decorator(exclusive_method, prefilter, postfilter)

            if qname not in self.view_functions:
                self.view_functions[qname] = exclusive_method

            exclusive_rule = getattr(exclusive_method, EXCLUSIVE_ID)  # type: ExposedRule
            rule = self.url_rule_class(exclusive_rule.uri, endpoint=qname, **exclusive_rule.route_kwargs)
            self.url_map.add(rule)


    def _pre_and_postfilter_decorator(self, method, prefilter=False, postfilter=False):

        method_name = getattr(method, "__qualname__", getattr(method, "__name__", repr(method)))

        @functools.wraps(method)
        def view_method_decorator(*args, **kwargs) -> str:

            if prefilter is not False:
                prefilter(method_name)

            if postfilter is not False:
                response = method(*args, **kwargs)
                return postfilter(method_name, response)
            else:
                return method(*args, **kwargs)

        return view_method_decorator


    def add_class(self, class_uri:str, **rule_kwargs:T.Dict[str, T.Any]) -> T.Callable:
        """
        Instantiates a generic class Foo(object) and wraps its exposed methods into a werkzeug.Submount

        TODO find a way to make this smaller/shorter

        :param class_uri:  The base URI for a class view ( eg "/base" is prepended to its exposed methods)
        :param rule_kwargs: Currently not used and not sane for use
        :return:
        """

        def decorator(cls_def:ExposedClassDefinition) -> ExposedClassDefinition:
            """

            :param cls_def: A class with atleast one method decoratored by CLSEndpointFlask.expose
            :return: Returns cls_def
            """
            cls_name = cls_def.__name__
            assert cls_name not in self._instances, \
                f"There is already a {cls_name} in add_class"

            cls_obj = self._instances[cls_name] = cls_def()

            prefilter = self._find_prefilter(cls_obj)
            postfilter = self._find_postfilter(cls_obj)

            endpoints = {name:func for name, func in self._find_exposed(cls_obj)}

            # Does the class have pre or post filter methods?
            if prefilter or postfilter:
                # TODO to shorten this scope down, this decorator could be made into a staticmethod of CLSEndpointFlask



                for name, method in endpoints.items():
                    orig_method_rule = getattr(endpoints[name], "_EXPOSED")
                    endpoints[name] = self._pre_and_postfilter_decorator(method, postfilter=postfilter, prefilter=prefilter)

                    # partial_method = functools.partial(view_method_decorator, endpoints[name])
                    # # To make it easier for debugging, have the common attributes like __qualname__ copied over to the partial
                    # partial_method = functools.update_wrapper(partial_method, endpoints[name])
                    # setattr(partial_method, "_EXPOSED", orig_method_rule)
                    # endpoints[name] = partial_method

            else:
                # acknowledge nothing needs to be done to the endpoints
                pass

            sub_rule = Submount(class_uri, self._get_exposed_rules(endpoints))
            self.url_map.add(sub_rule)
            # setup our exclusives
            self._assign_exclusive_rules(cls_obj, postfilter=postfilter, prefilter=prefilter)

            return cls_def

        return decorator
















