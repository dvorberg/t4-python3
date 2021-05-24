#!/usr/bin/env python
# -*- coding: utf-8 -*-

##  This file is part of the t4 Python module collection. 
##
##  Copyright 2002–2021 by Diedrich Vorberg <diedrich@tux4web.de>
##
##  All Rights Reserved
##
##  For more Information on orm see the README file.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 2 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program; if not, write to the Free Software
##  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
##
##  I have added a copy of the GPL in the file COPYING

"""

"""
__author__ = "Diedrich Vorberg <diedrich@tux4web.de>"

import re, json, io, inspect, datetime
from typing import TypeVar, Generic, Any, Sequence, get_type_hints

NULL = "NULL"

whitespace_re = re.compile(r"\s+")
def normalize_whitespace(s):
    return whitespace_re.sub(s, " ")

def separated(char, parts):
    ret = list()
    for part in parts:
        if part is not None:
            ret.append(part)
            ret.append(char)

    if len(ret) == 0:
        return tuple()
    else:        
        del ret[-1]
        return tuple(ret)

def comma_separated(parts):
    return separated(", ", parts)

def space_separated(parts):
    return separated(" ", parts)


class Backend:
    """
    This class provies all the methods needed for a datasource to work
    with an SQL backend.  This class' instances will work for most
    SQL92 complient backends that use utf-8 unicode encoding. 
    """
    def _param_placeholder_function(self, paramstyle):
        """
        Return a function-object for the param_placeholder(self, index)
        method. 
        """
        def qmark( index):
            return "?"

        def numeric(index):
            return ":%i" % index

        def named(index):
            return ":param%i" % index

        def format(index):
            return "%s"

        pyformat = format

        return locals()[paramstyle]
    
    def __init__(self, dbi_module, connection):
        self.connection = connection
        
        self.param_placeholder = self._param_placeholder_function(
            dbi_module.paramstyle)


    # These are used mostly for debugging.
    def quote_identifyer(self, name):
        return ( '"', name, '"', )

    def quote_string(self, string):
        return ( "'", string, "'", )

    escaped_chars = ( ('"', r'\"',),
                      ("'", r"\'",),
                      ("%", "%%",), )    
    def escape_string(self, string):
        for a in self.escaped_chars:
            string = string.replace(a[0], a[1])

        return string
    
        
    # This function is set in the constructur
    # 
    # def param_placeholder(self, index):
    #    . . .
    #
    # Return a function-object of a method that accepts a 1-based 
    # index and returns a placeholder to be used in SQL commands.
    # See the `parmstyle` parameter of the connection as documented
    # in PEP 249.
    # 
    # See _param_placeholder_function() above.


class Part:
    """
    Part of an SQL expression. 
    """
    def sql_to(self, sql_buffer):
        if sql_buffer.debug:
            func = self.debug
        else:
            func = self.sql

        available = { "self": self,
                      "sql_buffer": sql_buffer,
                      "backend": sql_buffer.backend, }
        signature = inspect.signature(func)
        args = [ available[name] for name in signature.parameters ]
        sql_buffer.print(func(*args))
    
    def sql(self):
        raise NotImplementedError()
        
    def debug(self):
        return self.sql()

    
class Parameter:
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value        

    
class SQLBuffer:
    def __init__(self, backend, debug=False):
        self.backend = backend
        self.debug = debug
        
        self._sql = io.StringIO()
        self._parameters = []


    def print(self, *args, **kw):
        if "end" not in kw:
            kw["end"] = ""

        for a in args:
            if isinstance(a, Parameter):
                self._parameters.append(a.value)
                print(self.backend.param_placeholder(len(self._parameters)),
                      file=self._sql, **kw)
            elif isinstance(a, Part):
                a.sql_to(self)
            elif type(a) in ( tuple, list, ):
                for b in a:
                    if hasattr(b, "sql_to"):
                        b.sql_to(self)
                    else:
                        self.print(b)
            else:
                print(a, file=self._sql, **kw)

    @property
    def sql(self):
        return self._sql.getvalue()
    
    @property
    def parameters(self):
        return tuple(self._parameters)

def rollup(backend, *sql, debug=False):
    sql_buffer = SQLBuffer(backend, debug)
    sql_buffer.print(*sql)
    return ( sql_buffer.sql, sql_buffer.parameters, )



class Statement(Part):
    """
    Base class for all statements (select, update, delete, etc)
    """

class Command(Part):
    pass
    
class Clause(Part):
    """
    Base class for clauses. They will be ordered according to rank
    when used to form a statement.
    """
    rank = 0

    
class Identifyer(Part):
    """
    Base class that encapsulates all sql identifyers.
    """
    def __init__(self, name, quote=False):
        self._name = name
        self._quote = quote

    def sql(self, backend):
        if self._quote:
            return backend.quote_identifyer(self._name)
        else:
            return self._name

    debug = sql

    @property
    def name(self):
        return self._name

    @property
    def quote(self):
        return self._quote

identifyer = Identifyer

def ensure_identifyer(i, quote=None):
    if i is None:
        return None
    
    if isinstance(i, identifyer):
        name = i.name
        quote = i.quote or quote
    elif type(i) == str:
        name = i
    else:
        raise TypeError("Identifyers must either be Identifyer "
                        "instances or strings.")
        
    return Identifyer(name, quote)


class quoted(Identifyer):
    """
    Shorthand for an identifyer that you'd like to be surrounded in
    quotes within the sql code.
    """
    def __init__(self, name):
        Identifyer.__init__(self, name, True)


        
T = TypeVar("T")
class Literal(Generic[T], Part):
    """
    Base class for the representation of values in SQL literals.
    """
    def __init__(self, value:T):
        #print(self.__class__, get_type_hints(self.__class__.__init__))
        self._value = value

    @property
    def value(self) -> T:
        return self._value    
    
class BackendLiteral(Literal[T]):
    """
    Base class for those literals passed to the backend as
    datastructures and represented in the output SQL as param
    placeholders like “%s” and “?”.
    """
    def __init__(self, value:T):
        super().__init__(value)

    def sql(self):
        return Parameter(self._value)

    def debug(self):
        raise NotImplemented("Don’t know how to represent the value "
                             "in debug SQL.")

    
class PythonLiteral(Literal[T]):
    """
    Base class for all values whose Python print() representation is
    identical to an SQL literal.
    """
    def sql(self):
        return self._value
        
    debug = sql
    
integer_literal = PythonLiteral[int]
float_literal = PythonLiteral[float]


class string_literal(BackendLiteral[str]):
    def debug(self, backend):
        value = self._value

        if len(value) > 40:
            value = "%s[%i more chars]%s" % ( value[:10], len(value) - 20,
                                              value[-10:], )
        
        return backend.quote_string(backend.escape_string(value))

    
class bytes_literal(BackendLiteral[bytes]):
    def debug(self, backend):
        value = "<%i bytes>" % len(self._value)
        return backend.quote_string(value)

    
class bool_literal(PythonLiteral[bool]):
    def sql(self):
        if self.value:
            return "TRUE"
        else:
            return "FALSE"

    debug = sql

    
class casted_literal(string_literal):
    sql_type_name = None
    
    def __init__(self, data:Any):
        super().__init__(json.dumps(data))

    def debug(self, backend):
        return super().debug(backend), "::" + self.sql_type_name,
        
    def sql(self):
        return ( Parameter(self._value), "::" + self.sql_type_name, )

class json_literal(casted_literal):
    sql_type_name = "JSON"
        
class jsonb_literal(casted_literal):
    sql_type_name = "JSONB"


class date_literal(casted_literal):
    sql_type_name = "DATE"

    def __init__(self, value:datetime.date):
        super().__init__(value.strftime("%Y-%m-%d"))
    
    
types = { int: integer_literal,
          float: float_literal,
          str: string_literal,
          bytes: bytes_literal,
          bool: bool_literal,
          datetime.date: date_literal,
         }
def find_literal_maybe(value):
    if isinstance(value, (Literal, expression)):
        return value
    elif value is None:
        return NULL
    else:
        t = type(value)
        if t in types:
            return types[t](value)
        else:
            raise TypeError("Can’t find literal class for: %s" % repr(t))
        
    
class relation(Part): 
    def __init__(self, name, schema=None):
        self._name = ensure_identifyer(name)
        self._schema = ensure_identifyer(schema)
        
    def sql(self):
        if self.schema is not None:
            return ( self.schema, ".", self.name, )
        else:
            return self.name

    @property
    def name(self):
        return self._name

    @property
    def schema(self):
        return self._schema

    
class column(Part):
    def __init__(self, name, relation=None):
        self._name = ensure_identifyer(name)
        self._relation = ensure_identifyer(relation)

    def sql(self):
        if self._relation is not None:
            return ( self._relation, ".", self._name, )
        else:
            return self._name

    def name(self, underscore=False):
        """
        @param underscore: If underscore is True, dots in the output will be
            replaced by underscores.
        """
        ret = self._name.name
        
        if underscore:
            return replace(ret, ".", "_")
        else:
            return ret

    def quote(self):
        return self._quote

            
class expression(Part):
    """
    Encapsolate an SQL expression like an arithmetic expression or a
    function call.
    """
    def __init__(self, *parts):
        self._parts = parts

    def sql(self):
        return self._parts

    def __add__(self, other):
        ret = expression()
        ret.parts = self._parts + other._parts

        return ret

class as_(expression):
    """
    Encapsulates an expression that goes into an AS statement in a
    SELECT's column list.
    """
    def __init__(self, identifyer, *parts):
        self._identifyer = ensure_identifyer(identifyer)
        expression.__init__(self, *parts)

    def sql(self):
        return ( expression.sql(self), " AS ", self._identifyer, )


class left_join(Clause):
    rank = 0
    
    def __init__(self, relation, *on):
        self._relation = relation
        self._on = on

    def sql(self):
        return ( "LEFT JOIN ", self._relation, " ON ", ) + self._on
    
class right_join(Clause):
    rank = 0
    
    def __init__(self, relation, *on):
        self._relation = relation
        self._on = on

    def sql(self):
        return ( "RIGHT JOIN ", self._relation, " ON ", ) + self._on
    
class where(Clause, expression):
    """
    Encapsulates the WHERE clause of a SELECT, UPDATE and DELETE
    statement. Just an expression with WHERE prepended.
    """
    rank = 1

    def __init__(self,  *parts):
        expression.__init__(self, *parts)

    def sql(self):
        return ( "WHERE ", expression.sql(self), )

    def __add__(self, other):
        """
        Adding two where clauses connects them using OR (including
        parantheses). 
        """
        return self.or_(other)

    def __mul__(self, other):
        """
        Multiplying two where clauses connects them using AND (including
        parantheses)
        """
        return self.and_(other)

    @staticmethod
    def _conjoin(conjunction, *others):
        """
        OTHERS is a list of sql.where instances that are connected
        using OR.
        """
        others = filter(lambda o: o is not None, others)

        ret = list()
        
        for other in others:
            ret.append("(")
            ret += list(other._parts)
            ret.append(")")
            ret.append(" %s " % conjunction)
            
        if len(ret) < 1:
            raise ValueError("Empty input for %s_()" % conjunction.lower())
        
        del ret[-1] # remove the last OR

        return where(*ret)        
    
    def or_(*others):
        return where._conjoin("OR", *others)
    
    def and_(*others):
        return where._conjoin("AND", *others)

    
class subquery_as_relation(relation):
    def __init__(self, select, alias):
        self._select = select
        self._alias = alias

    def sql(self):
        return ( "(", self._select, ") AS ", self._alias, )

    
class order_by(Clause):
    """
    Encapsulate the ORDER BY clause of a SELECT statement. Takes a
    list of columns as argument.
    """
    
    rank = 4
    
    def __init__(self, *expressions, dir=None):
        """
        `dir` is either ASC (default) or DESC.
        
        `expressions` may be expressions or tuples like ( expression,
        dir, ). The `dir` keyword parameter applies only to the last
        column identifyer and may create an SQL syntax error, of you
        supply one through a tuple in *expressions. 
        """
        def fixex(expression):
            if type(expression) in (list, tuple):
                assert len(expression) == 2, ValueError
                ex, dir = expression
                assert dir in ("ASC", "DESC"), ValueError
                return ( ex, " " + dir, )
            else:
                return expression
            
        self._expressions = [ fixex(ex) for ex in expressions
                              if ex is not None ]
        self._dir = dir

        if dir is not None and upper(dir) not in ("ASC", "DESC",):
            raise ValueError("dir must bei either ASC or DESC")
        else:
            if dir == "ASC":
                self._dir = None
            else:
                self._dir = dir

    def sql(self):
        ret = [ "ORDER BY ", comma_separated(self._expressions), ]
        
        if self._dir is not None:
            ret.append(self._dir)

        return tuple(ret)

orderby = order_by    


class select(Statement):
    """
    Encapsulate a SELECT statement.
    """
    def __init__(self, expressions, relations, *clauses):
        if type(expressions) == str:
            expressions = ( expressions, )
        self._expressions = expressions
        if type(relations) == str:
            expressions = ( relations, )
        self._relations = relations
        clauses = [ clause for clause in clauses if clause is not None ]
        
        for c in clauses:
            if not isinstance(c, Clause):
                raise TypeError("%s is not an SQL clause" % repr(c))

        self._clauses = sorted(clauses, key=lambda clause: clause.rank)
            
    def sql(self):
        return ( "SELECT ",
                 comma_separated(self._expressions),
                 " FROM ",
                 comma_separated(self._relations),
                 " ", 
                 space_separated(self._clauses), )


class group_by(Clause):
    """
    Encapsulate the GROUP BY clause of a SELECT statement. Takes a
    list of columns as argument.
    """
    rank = 3
    
    def __init__(self, *expressions, **kw):
        self._expressions = expressions

    def __sql__(self):
        return ( "GROUP BY ", comma_separated(self._expressions), )
        
groupby = group_by


class limit(Clause):
    """
    Encapsulate a SELECT statement's limit clause.
    """
    rank = 5
    
    def __init__(self, limit:int):
        self._limit = limit

    def sql(self):
        #limit = integer_literal(self._limit)
        #return ( "LIMIT ", limit, )
        return "LIMIT %i" % self._limit

class offset(Clause):
    """
    Encapsulate a SELECT statement's offset clause.
    """    
    rank = 6
    
    def __init__(self, offset:int):
        self._offset = offset

    def sql(self):
        #return ( "OFFSET ", integer_literal(self._offset), )
        return "OFFSET %i" % self._offset

class insert(Command):
    """
    Encapsulate an INSERT statement.

    The VALUES param to the constructor may be a sql.select() instance.
    We'll do the right thing.
    """
    def __init__(self,
                 relation:relation,
                 columns:Sequence[column],
                 values:Sequence[Sequence[Literal]]):
        self._relation = relation
        self._columns = columns
        self._values = values

        if len(values) == 0:
            raise ValueError("You must supply values to an insert statement")

    def sql(self):
        relation = self._relation
    
        ret = ["INSERT INTO ", self._relation,]

        if self._columns:
            ret += [ "(", comma_separated(self._columns), ")", ]

        if isinstance(self._values, select):
            ret.append(" ")
            ret.append(self._values)
        else:
            ret.append(" VALUES ")
            for tpl in self._values:
                if type(tpl) is dict:
                    data = tpl
                    tpl = []
                    for column in self._columns:
                        if type(column) is str:
                            name = column
                        else:
                            name = column.name()
                        value = data[name]
                        tpl.append(find_literal_maybe(value))

                ret.append("(")
                ret.append(comma_separated(tpl))
                ret.append(")")
                ret.append(", ")
            del ret[-1]

        return ret
        
class update(Command):
    def __init__(self, relation, where_clause, data={}):
        self._relation = relation
        self._where = where_clause
        
        self._data = {}

        for name, value in data.items():
            if type(name) is str: name = Identifyer(name)
            value = find_literal_maybe(value)

            self._data[name] = value
                

    def sql(self):
        ret = ["UPDATE ", self._relation, " SET "]

        pairs = [ ( column, " = ", value, )
                  for (column, value) in self._data.items() ]
        ret.append(comma_separated(pairs))
        ret.append(" ")
        ret.append(self._where)
        return ret
        
class delete(Command):
    def __init__(self, relation, where_clause):
        self._relation = relation
        self._where_clause = where_clause

    def sql(self):
        return [ "DELETE FROM ", self._relation, " ", self._where_clause, ]
