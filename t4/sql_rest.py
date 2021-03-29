class group_by(clause):
    """
    Encapsulate the GROUP BY clause of a SELECT statement. Takes a
    list of columns as argument.
    """
    
    rank = 3
    
    def __init__(self, *columns, **kw):
        self._columns = columns

    def __sql__(self, runner):
        return "GROUP BY %s" % flatten_identifyer_list(runner, self._columns)
        
groupby = group_by

class limit(clause):
    """
    Encapsulate a SELECT statement's limit clause.
    """
    
    rank = 5
    
    def __init__(self, limit):
        if type(limit) != IntType:
            raise TypeError("Limit must be an integer")
        
        self._limit = limit

    def __sql__(self, runner):
        limit = integer_literal(self._limit)
        return "LIMIT %s" % runner(limit)

class offset(clause):
    """
    Encapsulate a SELECT statement's offset clause.
    """
    
    rank = 6
    
    def __init__(self, offset):
        if not type(offset) in (IntType, LongType,):
            raise TypeError("Offset must be an integer")
        
        self._offset = offset

    def __sql__(self, runner):
        offset = integer_literal(self._offset)
        return "OFFSET %s" % runner(offset)

class insert(statement):
    """
    Encapsulate an INSERT statement.

    The VALUES param to the constructor may be a sql.select() instance.
    We'll do the right thing.
    """
    def __init__(self, relation, columns, *values):
        self._relation = relation
        self._columns = columns
        self._values = values

        if len(values) == 0:
            raise SQLSyntaxError(
                "You  must supply values to an insert statement")
        
        if not isinstance(values[0], select):
            for tpl in values:
                if len(self._columns) != len(tpl):
                    raise SQLSyntaxError(
                        "You must provide exactly one value for each column")

    def __sql__(self, runner):
        relation = self._relation
        columns = flatten_identifyer_list(runner, self._columns)

        INSERT = "INSERT INTO %(relation)s(%(columns)s)" % locals()

        if isinstance(self._values[0], select):
            return "%s %s" % ( INSERT, self._values[0].__sql__(runner), ) 
        else:
            # ok, values are no identifyers, but it's really the same thing
            # that's supposed to happen with them: call sql() on each of them,
            # put a , in between and return them as a string
            tuples = []
            for tpl in self._values:
                # Look for expressions among the values. Convert them into
                # simple strings with ( argound them ).
                tpl = list(tpl)
                for idx, part in enumerate(tpl):
                    if isinstance(part, expression):
                        tpl[idx] = "(" + runner(part) + ")"
                        
                tpl = flatten_identifyer_list(runner, tpl)
                tuples.append("(" + tpl + ")")
            tuples = join(tuples, ", ")
                                
            return INSERT + " VALUES " + tuples
    
class update(statement):
    """
    Encapsulate a UPDATE statement.
    """
    
    def __init__(self, relation, where_clause, info={}, **param_info):
        """
        @param relation: The relation to be updates.
        @param where_clause: where clause that determines the row to be updated
        @param info: Dictionary as {'column': sql_literal}
        """
        self._relation = relation
        self._info = info
        self._info.update(param_info)

        if not isinstance(where_clause, where):
            where_clause = where(where_clause)
            
        self._where = where_clause
        
    def __sql__(self, runner):
        relation = runner(self._relation)
        where = runner(self._where)

        info = []
        for column, value in self._info.items():
            column = runner(column)
            value = runner(value)

            info.append( "%s = %s" % (column, value,) )

        info = join(info, ", ")
        
        return "UPDATE %(relation)s SET %(info)s %(where)s" % locals()


class delete(statement):
    """
    Encapsulate a DELETE statement.
    """
    
    def __init__(self, relation, where_clause=None):
        self._relation = relation
        self._where = where_clause
        
    def __sql__(self, runner):
        relation = runner(self._relation)

        if self._where is not None:
            where = runner(self._where)        
            return "DELETE FROM %(relation)s %(where)s" % locals()
        else:
            return "DELETE FROM %(relation)s" % locals()

class left_join(clause, expression):
    def __init__(self, relation, *parts):
        if hasattr(relation, "__relation__"): relation = relation.__relation__
        expression.__init__(self, *parts)
        self._relation = relation

    def __sql__(self, runner):
        relation = flatten_identifyer_list(runner, self._relation)
        return "LEFT JOIN %s ON %s" % ( relation,
                                        expression.__sql__(self, runner), )
    
class right_join(clause, expression):
    def __init__(self, relation, *parts):
        if hasattr(relation, "__relation__"): relation = relation.__relation__
        expression.__init__(self, *parts)
        self._relation = relation

    def __sql__(self, runner):
        relation = flatten_identifyer_list(runner, self._relation)
        return "RIGHT JOIN %s ON %s" % ( relation,
                                        expression.__sql__(self, runner), )

class nil(expression, clause, statement):
    def __sql__(self, runner):
        return ""
    
class cursor_wrapper:
    """
    The cursor wrapper takes a regular database cursor and 'wraps' it
    up so that its execute() method understands sql.* objects as
    parameters. 
    """
    def __init__(self, ds, cursor):
        self._ds = ds
        self._cursor = cursor

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def execute(self, command, params=None):
        if type(command) == UnicodeType:
            raise TypeError("Database queries must be strings, not unicode")

        if isinstance(command, statement):
            runner = sql(self._ds)
            command = runner(command)
            params = runner.params

        if params is None:
            print >> sqllog, self._cursor, command
            self._cursor.execute(command)
        else:
            print >> sqllog, self._cursor, command, " || ", repr(params)
            self._cursor.execute(command, tuple(params))


def join_tokens(lst, sep):
    ret = []
    for a in lst:
        ret.append(a)
        ret.append(sep)

    ret.pop()
    
    return ret

