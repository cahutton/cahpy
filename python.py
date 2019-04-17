"""TODO."""


class DummyCallable(object):
    """TODO."""

    def __call__(self, *args, **kwargs):
        """TODO."""
        pass


class DummyContainer(object):
    """TODO."""

    def __contains__(self, item):
        """TODO."""
        """item in self"""
        return False

    def __delitem__(self, key):
        """TODO."""
        """del self[key]"""
        pass

    def __getitem__(self, key):
        """TODO."""
        """self[key]"""
        return key

    def __iter__(self):
        """TODO."""
        return DummyIterator()

    def __len__(self):
        """TODO."""
        """len(self)"""
        return 0

    def __length_hint__(self):
        """TODO."""
        """operator.length_hint(self)"""
        return 0

    def __missing__(self, key):
        """TODO."""
        """self[key] if instanceof(self, dict)"""
        return key

    def __reversed__(self):
        """TODO."""
        """reversed(self)"""
        return DummyIterator()

    def __setitem__(self, key, value):
        """TODO."""
        """self[key] = value"""
        pass


class DummyContextManager(object):
    """TODO."""

    def __enter__(self):
        """TODO."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """TODO."""
        return None


# TODO
# class DummyIterable(object):
    """TODO."""

    # def __iter__(self):
    #     return self


class DummyIterator(object):
    """TODO."""

    def __iter__(self):
        """TODO."""
        return self


class DummyNumericType(object):
    """TODO."""

    def __abs__(self):
        """TODO."""
        """abs(self)"""
        return self

    def __add__(self, other):
        """TODO."""
        """self + other"""
        return other

    def __ceil__(self):
        """TODO."""
        """ceil(self)"""
        return int(self)

    def __complex__(self):
        """TODO."""
        """complex(self)"""
        return complex()

    def __divmod__(self, other):
        """TODO."""
        """divmod(self, other)"""
        return self // other, self % other

    def __float__(self):
        """TODO."""
        """float(self)"""
        return float()

    def __floor__(self):
        """TODO."""
        """floor(self)"""
        return int(self)

    def __floordiv__(self, other):
        """TODO."""
        """self // other"""
        return other

    def __iadd__(self, other):
        """TODO."""
        """self += other"""
        return self

    def __ifloordiv__(self, other):
        """TODO."""
        """self //= other"""
        return self

    def __imatmul__(self, other):
        """TODO."""
        """self @= other"""
        return self

    def __imod__(self, other):
        """TODO."""
        """self %= other"""
        return self

    def __imul__(self, other):
        """TODO."""
        """self *= other"""
        return self

    def __int__(self):
        """TODO."""
        """int(self)"""
        return int()

    def __ipow__(self, other):
        """TODO."""
        """self **= other"""
        return self

    def __isub__(self, other):
        """TODO."""
        """self -= other"""
        return self

    def __itruediv__(self, other):
        """TODO."""
        """self /= other"""
        return self

    def __matmul__(self, other):
        """TODO."""
        """self @ other"""
        return other

    def __mod__(self, other):
        """TODO."""
        """self % other"""
        return other

    def __mul__(self, other):
        """TODO."""
        """self * other"""
        return other

    def __neg__(self):
        """TODO."""
        """-self"""
        return self

    def __pos__(self):
        """TODO."""
        """+self"""
        return self

    def __pow__(self, other, modulo=None):
        """TODO."""
        """self ** other, pow(self, other, modulo)"""
        return other

    def __radd__(self, other):
        """TODO."""
        """other + self"""
        return self + other

    def __rdivmod__(self, other):
        """TODO."""
        """divmod(other, self)"""
        return divmod(self, other)

    def __rfloordiv__(self, other):
        """TODO."""
        """other // self"""
        return self // other

    def __rmatmul__(self, other):
        """TODO."""
        """other @ self"""
        return self.__matmul__(other)
        # >=3.5
        # return self @ other

    def __rmod__(self, other):
        """TODO."""
        """other % self"""
        return self % other

    def __rmul__(self, other):
        """TODO."""
        """other * self"""
        return self * other

    def __round__(self, ndigits=None):
        """TODO."""
        """round(self, ndigits)"""
        if ndigits:
            return float(self)
        else:
            return int(self)

    def __rpow__(self, other):
        """TODO."""
        """other ** self"""
        return self ** other

    def __rsub__(self, other):
        """TODO."""
        """other - self"""
        return self - other

    def __rtruediv__(self, other):
        """TODO."""
        """other / self"""
        return self / other

    def __sub__(self, other):
        """TODO."""
        """self - other"""
        return other

    def __truediv__(self, other):
        """TODO."""
        """self / other"""
        return other

    def __trunc__(self):
        """TODO."""
        """trunc(self)"""
        return int(self)


class DummyIntegralType(DummyNumericType):
    """TODO."""

    def __and__(self, other):
        """TODO."""
        """self & other"""
        return other

    def __iand__(self, other):
        """TODO."""
        """self &= other"""
        return self

    def __ilshift__(self, other):
        """TODO."""
        """self <<= other"""
        return self

    def __index__(self):
        """TODO."""
        """operator.index(self), foo[self], foo[self:], foo[:self], bin(self),
        hex(self), oct(self)"""
        return int(self)

    def __invert__(self):
        """TODO."""
        """~self"""
        return self

    def __ior__(self, other):
        """TODO."""
        """self |= other"""
        return self

    def __irshift__(self, other):
        """TODO."""
        """self >>= other"""
        return self

    def __ixor__(self, other):
        """TODO."""
        """self ^= other"""
        return self

    def __lshift__(self, other):
        """TODO."""
        """self << other"""
        return other

    def __or__(self, other):
        """TODO."""
        """self | other"""
        return other

    def __rand__(self, other):
        """TODO."""
        """other & self"""
        return self & other

    def __rlshift__(self, other):
        """TODO."""
        """other << self"""
        return self << other

    def __ror__(self, other):
        """TODO."""
        """other | self"""
        return self | other

    def __rrshift__(self, other):
        """TODO."""
        """other >> self"""
        return self >> other

    def __rshift__(self, other):
        """TODO."""
        """self >> other"""
        return other

    def __rxor__(self, other):
        """TODO."""
        """other ^ self"""
        return self ^ other

    def __xor__(self, other):
        """TODO."""
        """self ^ other"""
        return other


def safe_eval(input_string, safe_globals=None, safe_locals=None):
    """TODO."""
    if safe_globals is None:
        safe_globals = {
            '__builtins__': None
        }

    if safe_locals is None:
        safe_locals = {}

    return eval(input_string, safe_globals, safe_locals)
