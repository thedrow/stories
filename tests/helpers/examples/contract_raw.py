from operator import itemgetter

from stories import Success, arguments, story
from stories.shortcuts import contract_in


# Helper functions.


def integer(value):
    if isinstance(value, int):
        return value, None
    elif isinstance(value, str) and value.isdigit():
        return int(value), None
    else:
        return None, "Invalid value"


def string(value):
    if isinstance(value, str):
        return value, None
    else:
        return None, "Invalid value"


def list_of(f):
    def validator(value):
        if isinstance(value, list):
            new = list(map(f, value))
            if any(map(itemgetter(1), new)):
                return None, "Invalid value"
            else:
                return list(map(itemgetter(0), new)), None
        else:
            return None, "Invalid value"

    return validator


# Mixins.


class NormalMethod(object):
    def one(self, ctx):
        return Success()


class StringMethod(object):
    def one(self, ctx):
        return Success(foo="1", bar=["2"])


class WrongMethod(object):
    def one(self, ctx):
        return Success(foo="<boom>", bar=["<boom>"])


class UnknownMethod(object):
    def one(self, ctx):
        return Success(spam="0", quiz="1")


class ExceptionMethod(object):
    def one(self, ctx):
        raise Exception


# Parent mixins.


class NormalParentMethod(object):
    def before(self, ctx):
        return Success()

    def after(self, ctx):
        return Success()


class StringParentMethod(object):
    def before(self, ctx):
        return Success(foo="1", bar=["2"])

    def after(self, ctx):
        return Success()


class ExceptionParentMethod(object):
    def before(self, ctx):
        raise Exception

    def after(self, ctx):
        return Success()


# Root mixins.


class NormalRootMethod(object):
    def start(self, ctx):
        return Success()

    def finish(self, ctx):
        return Success()


class StringRootMethod(object):
    def start(self, ctx):
        return Success(foo="1", bar=["2"])

    def finish(self, ctx):
        return Success()


class StringWideRootMethod(object):
    def start(self, ctx):
        return Success(foo="1", bar=["2"], baz="1")

    def finish(self, ctx):
        return Success()


class ExceptionRootMethod(object):
    def start(self, ctx):
        raise Exception

    def finish(self, ctx):
        return Success()


# Child base classes.


class Child(object):
    @story
    def x(I):
        I.one

    x.contract({"foo": integer, "bar": list_of(integer), "baz": integer})


class ChildWithNull(object):
    @story
    def x(I):
        I.one


class ChildWithShrink(object):
    @story
    def x(I):
        I.one

    x.contract({"baz": integer})


class ChildReuse(object):
    @story
    def x(I):
        I.one


class ParamChild(object):
    @story
    @arguments("foo", "bar")
    def x(I):
        I.one

    x.contract({"foo": integer, "bar": list_of(integer), "baz": integer})


class ParamChildWithNull(object):
    @story
    @arguments("foo", "bar")
    def x(I):
        I.one


class ParamChildWithShrink(object):
    @story
    @arguments("foo", "bar", "baz")
    def x(I):
        I.one

    x.contract({"baz": integer})


# Next child base classes.


class NextChildWithSame(object):
    @story
    def y(I):
        I.one

    y.contract({"foo": integer, "bar": list_of(integer), "baz": integer})


class NextParamChildWithString(object):
    @story
    @arguments("foo", "bar")
    def y(I):
        I.one

    y.contract({"foo": string, "bar": list_of(string)})


class NextParamChildReuse(object):
    @story
    @arguments("foo", "bar", "baz")
    def y(I):
        I.one


# Parent base classes.


class Parent(object):
    @story
    def a(I):
        I.before
        I.x
        I.after


Parent.a.contract({"ham": integer, "eggs": integer, "beans": integer})


class ParentWithNull(object):
    @story
    def a(I):
        I.before
        I.x
        I.after


class ParentWithSame(object):
    @story
    def a(I):
        I.before
        I.x
        I.after


ParentWithSame.a.contract({"foo": integer, "bar": list_of(integer), "baz": integer})


class ParentReuse(object):
    @story
    def a(I):
        I.before
        I.x
        I.after


ChildReuse.x.contract(
    ParentReuse.a.contract({"foo": integer, "bar": list_of(integer), "baz": integer})
)


class SequentialParent(object):
    @story
    def a(I):
        I.before
        I.x
        I.y
        I.after

    a.contract({})


class ParamParent(object):
    @story
    @arguments("ham", "eggs")
    def a(I):
        I.before
        I.x
        I.after


ParamParent.a.contract({"ham": integer, "eggs": integer, "beans": integer})


class ParamParentWithNull(object):
    @story
    @arguments("ham", "eggs")
    def a(I):
        I.before
        I.x
        I.after


class ParamParentWithSame(object):
    @story
    @arguments("foo", "bar", "baz")
    def a(I):
        I.before
        I.after


ParamParentWithSame.a.contract(
    {"foo": integer, "bar": list_of(integer), "baz": integer}
)


class ParamParentWithSameWithString(object):
    @story
    @arguments("foo", "bar")
    def a(I):
        I.before
        I.x
        I.after


ParamParentWithSameWithString.a.contract({"foo": string, "bar": list_of(string)})


# Next parent base classes.


class NextParamParentReuse(object):
    @story
    @arguments("foo", "bar")
    def b(I):
        I.before
        I.y
        I.after


NextParamChildReuse.y.contract(
    NextParamParentReuse.b.contract(
        {"foo": integer, "bar": list_of(integer), "baz": integer}
    )
)


# Root base classes.


class Root(object):
    @story
    def i(I):
        I.start
        I.a
        I.finish


contract_in(Root, {"fizz": integer, "buzz": integer})


class RootWithSame(object):
    @story
    def i(I):
        I.start
        I.a
        I.finish


contract_in(RootWithSame, {"foo": integer, "bar": list_of(integer), "baz": integer})


class SequentialRoot(object):
    @story
    def i(I):
        I.start
        I.a
        I.b
        I.finish


contract_in(SequentialRoot, {"fizz": integer, "buzz": integer})


class ParamRoot(object):
    @story
    @arguments("fizz")
    def i(I):
        I.start
        I.a
        I.finish


contract_in(ParamRoot, {"fizz": integer, "buzz": integer})
