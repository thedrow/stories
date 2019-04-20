from ._compat import CerberusSpec, MarshmallowSpec, PydanticError, PydanticSpec
from .exceptions import ContextContractError


# FIXME:
#
# [ ] Handle protocol extension.  There should be way to say in the
#     substory contract "this variable should be an integer" and in
#     addition in the story "this integer should be greater then 7".
#     This way we also can require a certain substory to declare
#     context variable for parent story.
#
# [ ] Split `Contract` class into `NullContract` and `SpecContract`
#     classes.  Checking `self.spec is None` at the beginning of
#     methods is ugly.  Drop `available_null` and `validate_null`
#     functions.
#
# [ ] Remove all get methods.  Populate contract subcontracts
#     attributes in the wrap stage.
#
# [ ] Add fix suggestion to the bottom of the error message.


# Declared validators.


def available_null(spec):
    raise Exception


def available_pydantic(spec):
    return set(spec.__fields__)


def available_marshmallow(spec):
    return set(spec._declared_fields)


def available_cerberus(spec):
    return set(spec.schema)


def available_raw(spec):
    return set(spec)


# Validation.


def validate_null(spec, ns, keys):
    raise Exception


def validate_pydantic(spec, ns, keys):
    result, errors = {}, {}
    for key in keys:
        field = spec.__fields__[key]
        new_value, error = field.validate(ns[key], {}, loc=field.alias, cls=spec)
        if error:
            errors[key] = error
        else:
            result[key] = new_value
    return result, errors


def validate_marshmallow(spec, ns, keys):
    result, errors = spec().load(ns)
    return result, errors


def validate_cerberus(spec, ns, keys):
    validator = CerberusSpec(allow_unknown=True)
    validator.validate(ns, spec.schema.schema)
    return dict((key, validator.document[key]) for key in keys), validator.errors


def validate_raw(spec, ns, keys):
    result, errors = {}, {}
    for key in keys:
        new_value, error = spec[key](ns[key])
        if error:
            errors[key] = error
        else:
            result[key] = new_value
    return result, errors


# Execute.


def make_contract(cls_name, name, arguments, spec):
    if spec is None:
        available_func = available_null
        validate_func = validate_null
    elif isinstance(spec, PydanticSpec):
        available_func = available_pydantic
        validate_func = validate_pydantic
    elif isinstance(spec, MarshmallowSpec):
        available_func = available_marshmallow
        validate_func = validate_marshmallow
    elif isinstance(spec, CerberusSpec):
        available_func = available_cerberus
        validate_func = validate_cerberus
    elif isinstance(spec, dict):
        available_func = available_raw
        validate_func = validate_raw
    # FIXME: Raise error on unsupported types.
    return Contract(cls_name, name, arguments, spec, available_func, validate_func)


class Contract(object):
    def __init__(self, cls_name, name, arguments, spec, available_func, validate_func):
        self.cls_name = cls_name
        self.name = name
        self.arguments = arguments
        self.spec = spec
        self.available_func = available_func
        self.validate_func = validate_func
        self.subcontracts = []
        self.check_arguments_definitions()

    def add_substory_contract(self, contract):
        self.subcontracts.append(contract)

    def check_arguments_definitions(self):
        # vvv
        if self.spec is None:
            return
        # ^^^
        undefined = set(self.arguments) - self.available_func(self.spec)
        if undefined:
            message = undefined_argument_template.format(
                undefined=", ".join(sorted(undefined)),
                cls=self.cls_name,
                method=self.name,
                arguments=", ".join(self.arguments),
            )
            raise ContextContractError(message)

    def check_story_call(self, kwargs):
        unknown_arguments = self.get_unknown_arguments(kwargs)
        if unknown_arguments:
            if self.arguments:
                # FIXME: What if arguments were defined only in the substory?
                template = unknown_argument_template
            else:
                template = unknown_argument_null_template
            message = template.format(
                unknown=", ".join(sorted(unknown_arguments)),
                cls=self.cls_name,
                method=self.name,
                arguments=", ".join(self.arguments),
            )
            raise ContextContractError(message)
        # vvv
        if self.spec is None:
            return kwargs
        # ^^^
        kwargs, errors, _ = self.get_invalid_variables(kwargs)
        if errors:
            message = invalid_argument_template.format(
                variables=", ".join(map(repr, sorted(errors))),
                cls=self.cls_name,
                method=self.name,
                violations=format_violations(errors),
            )
            raise ContextContractError(message)
        return kwargs

    def check_substory_call(self, ctx):
        missed = set(self.arguments) - set(ctx._Context__ns)
        if missed:
            message = missed_variable_template.format(
                missed=", ".join(sorted(missed)),
                cls=self.cls_name,
                method=self.name,
                arguments=", ".join(self.arguments),
                ctx=ctx,
            )
            raise ContextContractError(message)

    def check_success_statement(self, method, ctx, ns):
        tries_to_override = set(ctx._Context__ns) & set(ns)
        if tries_to_override:
            message = variable_override_template.format(
                variables=", ".join(map(repr, sorted(tries_to_override))),
                cls=method.__self__.__class__.__name__,
                method=method.__name__,
            )
            raise ContextContractError(message)
        # vvv
        if self.spec is None:
            return ns
        # ^^^
        unknown_variables, available = self.get_unknown_variables(ns)
        if unknown_variables:
            message = unknown_variable_template.format(
                unknown=", ".join(map(repr, sorted(unknown_variables))),
                available=", ".join(map(repr, sorted(available))),
                cls=method.__self__.__class__.__name__,
                method=method.__name__,
            )
            raise ContextContractError(message)
        kwargs, errors, _ = self.get_invalid_variables(ns)
        if errors:
            message = invalid_variable_template.format(
                variables=", ".join(map(repr, sorted(errors))),
                cls=method.__self__.__class__.__name__,
                method=method.__name__,
                violations=format_violations(errors),
            )
            raise ContextContractError(message)
        return kwargs

    def get_arguments(self):
        # FIXME: Remove repeated arguments.
        arguments = []
        arguments.extend(self.arguments)
        for contract in self.subcontracts:
            arguments.extend(contract.get_arguments())
        return arguments

    def get_available(self):
        available = self.available_func(self.spec)
        for contract in self.subcontracts:
            available |= contract.get_available()
        return available

    def find_conflict_contract(self, repeated):
        available = self.available_func(self.spec)
        if available & repeated:
            return self.cls_name, self.name
        for contract in self.subcontracts:
            result = contract.find_conflict_contract(repeated)
            if result:
                return result

    def get_unknown_arguments(self, kwargs):
        available = set(self.arguments)
        unknown_arguments = set(kwargs) - available
        for contract in self.subcontracts:
            unknown_arguments = contract.get_unknown_arguments(unknown_arguments)
        return unknown_arguments

    def get_unknown_variables(self, ns):
        available = self.available_func(self.spec)
        unknown_variables = set(ns) - available
        for contract in self.subcontracts:
            unknown_variables, _ = contract.get_unknown_variables(unknown_variables)
        return unknown_variables, available

    def get_invalid_variables(self, ns):
        # FIXME: This method is unbelievably complex.
        available = set(ns) & self.available_func(self.spec)
        kwargs, errors = self.validate_func(self.spec, ns, available)
        normalized = dict(
            (variable, (self.cls_name, self.name)) for variable in available
        )
        for contract in self.subcontracts:
            sub_kwargs, sub_errors, sub_normalized = contract.get_invalid_variables(ns)
            conflict = set()
            for variable, value in sub_kwargs.items():
                if variable in kwargs and kwargs[variable] != value:
                    conflict.add(variable)
            if conflict:
                message = normalization_conflict_template.format(
                    conflict=", ".join(map(repr, sorted(conflict))),
                    # FIXME: Normalization conflict can consist of two
                    # variables.  The first variable can be set by one
                    # substory.  The second variable can be set by
                    # another substory.
                    cls=normalized[next(iter(conflict))][0],
                    method=normalized[next(iter(conflict))][1],
                    result="\n".join(
                        [
                            " - " + variable + ": " + repr(kwargs[variable])
                            for variable in sorted(conflict)
                        ]
                    ),
                    other_cls=contract.cls_name,
                    other_method=contract.name,
                    other_result="\n".join(
                        [
                            " - " + variable + ": " + repr(sub_kwargs[variable])
                            for variable in sorted(conflict)
                        ]
                    ),
                )
                raise ContextContractError(message)
            kwargs.update(sub_kwargs)
            errors.update(sub_errors)
            normalized.update(sub_normalized)
        return kwargs, errors, normalized


def format_violations(errors):
    result = []

    def normalize_pydantic(value, indent):
        normalize_str(value.msg, indent)

    def normalize_str(value, indent):
        result.append(" " * indent + value)

    def normalize_list(value, indent):
        for elem in value:
            if isinstance(elem, dict):
                normalize_dict(elem, indent + 2)
            elif isinstance(elem, PydanticError):
                normalize_pydantic(elem, indent)
            else:
                normalize_str(elem, indent)

    def normalize_dict(value, indent, sep=None):
        for k in sorted(value):
            v = value[k]
            normalize_str(str(k) + ":", indent)
            if isinstance(v, dict):
                normalize_dict(v, indent + 2)
            elif isinstance(v, list):
                normalize_list(v, indent + 2)
            elif isinstance(v, PydanticError):
                normalize_pydantic(v, indent + 2)
            else:
                normalize_str(v, indent + 2)
            if sep is not None:
                normalize_str(sep, 0)

    normalize_dict(errors, 0, "")

    return "\n".join(result)


# Wrap.


def combine_contract(parent, child):
    if parent.spec is child.spec:
        parent.add_substory_contract(child)
        return
    if parent.spec is None and child.spec is None:
        parent.add_substory_contract(child)
        return
    for spec_type in [PydanticSpec, MarshmallowSpec, CerberusSpec, dict]:
        if isinstance(parent.spec, spec_type) and isinstance(child.spec, spec_type):
            break
    else:
        message = type_error_template.format(
            cls=parent.cls_name,
            method=parent.name,
            contract=parent.spec,
            other_cls=child.cls_name,
            other_method=child.name,
            other_contract=child.spec,
        )
        raise ContextContractError(message)
    available = parent.get_available() & child.get_available()
    arguments = set(parent.get_arguments()) & set(child.get_arguments())
    repeated = available - arguments
    if repeated:
        cls_name, name = parent.find_conflict_contract(repeated)
        other_cls, other_method = child.find_conflict_contract(repeated)
        message = incompatible_contracts_template.format(
            repeated=", ".join(map(repr, sorted(repeated))),
            cls=cls_name,
            method=name,
            other_cls=other_cls,
            other_method=other_method,
        )
        raise ContextContractError(message)
    parent.add_substory_contract(child)


# Messages.


undefined_argument_template = """
These arguments should be declared in the context contract: {undefined}

Story method: {cls}.{method}

Story arguments: {arguments}
""".strip()


missed_variable_template = """
These variables are missing from the context: {missed}

Story method: {cls}.{method}

Story arguments: {arguments}

{ctx!r}
""".strip()


variable_override_template = """
These variables are already present in the context: {variables}

Function returned value: {cls}.{method}

Use different names for Success() keyword arguments.
""".strip()


unknown_variable_template = """
These variables were not defined in the context contract: {unknown}

Available variables are: {available}

Function returned value: {cls}.{method}

Use different names for Success() keyword arguments or add these names to the contract.
""".strip()


unknown_argument_template = """
These arguments are unknown: {unknown}

Story method: {cls}.{method}

Story composition arguments: {arguments}
""".strip()


unknown_argument_null_template = """
These arguments are unknown: {unknown}

Story method: {cls}.{method}

Story composition has no arguments.
""".strip()


invalid_variable_template = """
These variables violates context contract: {variables}

Function returned value: {cls}.{method}

Violations:

{violations}
""".strip()


invalid_argument_template = """
These arguments violates context contract: {variables}

Story method: {cls}.{method}

Violations:

{violations}
""".strip()


incompatible_contracts_template = """
Repeated variables can not be used in a story composition.

Variables repeated in both context contracts: {repeated}

Story method: {cls}.{method}

Substory method: {other_cls}.{other_method}

Use variables with different names.
""".strip()


type_error_template = """
Story and substory context contracts has incompatible types:

Story method: {cls}.{method}

Story context contract: {contract}

Substory method: {other_cls}.{other_method}

Substory context contract: {other_contract}
""".strip()


normalization_conflict_template = """
These arguments have normalization conflict: {conflict}

Story method: {cls}.{method}

Story normalization result:
{result}

Substory method: {other_cls}.{other_method}

Substory normalization result:
{other_result}
""".strip()
