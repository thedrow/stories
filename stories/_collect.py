from ._marker import substory_end, substory_start
from ._proxy import make_proxy


def collect_story(f):

    calls = []

    class Collector(object):
        def __getattr__(self, name):
            calls.append(name)
            return lambda: None

    f(Collector())

    return calls


def wrap_story(is_story, collected, obj, ctx):

    methods = []
    proxy = make_proxy(obj, ctx)

    for name in collected:
        attr = getattr(obj, name)
        if not is_story(attr):
            methods.append((proxy, attr.__func__))
            continue

        sub_methods = wrap_story(is_story, attr.collected, attr.obj, ctx)
        if not sub_methods:
            continue

        if attr.obj is obj:
            method_name = name
        else:
            method_name = name + " (" + attr.cls_name + "." + attr.name + ")"

        sub_proxy = sub_methods[0][0]
        methods.append((sub_proxy, make_validator(method_name, attr.arguments)))
        methods.extend(sub_methods)
        methods.append((sub_proxy, end_of_story))

    return methods


def make_validator(name, arguments):
    def validate_substory_arguments(self):
        assert set(arguments) <= set(self.ctx)
        return substory_start

    validate_substory_arguments.method_name = name

    return validate_substory_arguments


def end_of_story(self):
    return substory_end
