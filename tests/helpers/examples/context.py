from stories import Success, arguments, story


# Mixins.


class NormalMethod(object):
    def one(self, ctx):
        return Success(foo=self.foo)


class AssignMethod(object):
    def one(self, ctx):
        ctx.foo = 1


class DeleteMethod(object):
    def one(self, ctx):
        del ctx.foo


# Parent mixins.


class NormalParentMethod(object):
    def before(self, ctx):
        return Success()

    def after(self, ctx):
        return Success()


# Base classes.


class Child(object):
    @story
    def x(I):
        I.one


class ParamChild(object):
    @story
    @arguments("bar")
    def x(I):
        I.one


class Parent(object):
    @story
    def a(I):
        I.before
        I.x
        I.after


class ParamParent(object):
    @story
    @arguments("bar")
    def a(I):
        I.before
        I.x
        I.after