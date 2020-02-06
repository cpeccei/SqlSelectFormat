import re
import textwrap
import unittest

try:
    import sublime
    import sublime_plugin
except:
    class sublime_plugin():
        TextCommand = object

INDENT = '  '
SEP = '-' * 40

# =====================================================================

class TestSqlFormat(unittest.TestCase):

    def test_select(self):
        input_sql = 'select a, b from d'
        desired_output = """
SELECT
  a,
  b
FROM
  d
"""
        desired_output = re.sub('  ', INDENT, desired_output.strip())
        actual_output = format_sql(input_sql)
        print('Input:\n' + input_sql)
        print('Desired output:\n' + desired_output)
        print('Actual output:\n' + actual_output)
        print(repr(desired_output))
        print(repr(actual_output))
        self.assertEqual(desired_output, actual_output)

    def test_subquery(self):
        input_sql = 'select * from (select a, b from d) x'
        desired_output = """
SELECT
  *
FROM
  (SELECT
    a,
    b
  FROM
    d) x
"""
        desired_output = re.sub('  ', INDENT, desired_output.strip())
        actual_output = format_sql(input_sql)
        print('Input:\n' + input_sql)
        print('Desired output:\n' + desired_output)
        print('Actual output:\n' + actual_output)
        print(repr(desired_output))
        print(repr(actual_output))
        self.assertEqual(desired_output, actual_output)

    def test_with(self):
        input_sql = 'with a as (select * from x), b as (select * from y) select * from a inner join b on a.id = b.id'
        desired_output = """
WITH
---
a AS
(SELECT
  *
FROM
  x),
---
b AS
(SELECT
  *
FROM
  y)
---
SELECT
  *
FROM
  a
  INNER JOIN
  b
  ON a.id = b.id
"""
        desired_output = re.sub('  ', INDENT, desired_output.strip())
        desired_output = desired_output.replace('---', SEP)
        actual_output = format_sql(input_sql)
        print('Input:\n' + input_sql)
        print('Desired output:\n' + desired_output)
        print('Actual output:\n' + actual_output)
        print(repr(desired_output))
        print(repr(actual_output))
        self.assertEqual(desired_output, actual_output)


# =====================================================================

def split_parens(text):
    istart = []  # stack of indices of opening parentheses
    j = 0
    for i, c in enumerate(text):
        if c == '(':
             istart.append(i)
        if c == ')':
            if not istart:
                print('Error:', text)
                raise ValueError('Too many closing parentheses')
            start = istart.pop()
            end = i
            if not istart:
                # End of top level parens
                if j < start:
                    yield text[j:start]
                yield text[start:end + 1]
                j = end + 1
    if istart:  # check if stack is empty afterwards
        raise ValueError('Too many opening parentheses')
    if j < len(text):
        yield text[j:]

def uppercase_keywords(sql):
    # Convert all keywords to uppercase
    keywords = ['WITH', 'AS', 'SELECT', 'FROM', 'WHERE', 'AND', 'OR',
        'NOT', 'LEFT', 'RIGHT', 'FULL', 'INNER', 'OUTER', 'JOIN',
        'GROUP', 'BY', 'OVER', 'HAVING', 'BETWEEN', 'ON', 'CASE', 'WHEN',
        'THEN', 'DISTINCT', 'ORDER', 'DESC', 'ASC',
        'UNION', 'ALL', 'END', 'LIMIT']
    for keyword in keywords:
        sql = re.sub(r'\b' + keyword + r'\b', keyword, sql,
            flags = re.IGNORECASE)
    return sql

def to_single_line(sql):
    # Convert to single line
    return ' '.join(sql.split())

def protect(text, regex, prefix):
    split_regex = '(' + regex + ')'
    fields = re.split(split_regex, text)
    mapping = {}
    for i in range(1, len(fields), 2):
        # key = '{' + prefix + str(len(mapping)) + '}'
        key = '{' + prefix + str(len(mapping)) + '}' + '_' * len(fields[i])
        mapping[key] = fields[i]
        fields[i] = key
    return ''.join(fields), mapping

def unprotect(text, mapping):
    for key in mapping:
        text = text.replace(key, mapping[key])
    return text

def protect_parens(text, prefix):
    fields = list(split_parens(text))
    mapping = {}
    for i, field in enumerate(fields):
        if field.startswith('('):
            key = '{' + prefix + str(len(mapping)) + '}'
            mapping[key] = fields[i]
            fields[i] = key
    return ''.join(fields), mapping

def split_comma_sep_expressions(text):
    blocks = ['']
    paren_depth = 0
    for i, c in enumerate(text):
        if c == ',' and paren_depth == 0:
            blocks.append('')
        else:
            blocks[-1] += c
        if c == '(':
            paren_depth += 1
        elif c == ')':
            paren_depth -= 1
    return blocks

def select_blocks(sql):
    # Note: this requires sql to be all on one line with consistent spacing
    sql, parens_map = protect_parens(sql, 'P')
    blocks = re.sub(' (SELECT|FROM|WHERE|HAVING|GROUP|UNION|ORDER|LIMIT) ',
        r'\n\1 ', sql).splitlines()
    return [unprotect(block, parens_map) for block in blocks]

def wrap(sql):
    wrapped = []
    lines = sql.splitlines()
    for line in lines:
        initial_indent = re.search('^ *', line).group(0)
        subsequent_indent = initial_indent + INDENT
        wrapped_lines = textwrap.fill(line.strip(),
            width = 104 - len(initial_indent), break_long_words=False,
            break_on_hyphens=False,
            initial_indent=initial_indent,
            subsequent_indent=subsequent_indent)
        wrapped.append(wrapped_lines)
    return '\n'.join(wrapped)


sample_sql = """
with t as (
  SELECT
    ckd.date AS "ckd_date",
    -- comment
    SUM(ckd.total_widgets_2017) OVER
      (ORDER BY ckd.date
      ROWS UNBOUNDED PRECEDING) AS total_widgets_2017,
    SUM(ckd.total_widgets_2018) OVER
      (ORDER BY ckd.date
      ROWS UNBOUNDED PRECEDING) AS total_widgets_2018,
    SUM(ckd.goal_widgets_2019) OVER
      (ORDER BY ckd.date
      ROWS UNBOUNDED PRECEDING) AS goal_widgets_2019,
    SUM(ckd.total_widgets_2019) OVER
      (ORDER BY ckd.date
      ROWS UNBOUNDED PRECEDING) AS total_widgets_2019
  FROM
    cds_widgets_daily ckd inner join p on ckd.id = p.id left join d on p.x = d.x
left join (SELECT min(a) as mina, b from j inner join m on j.id = m.id where
j.x = 'hello') mt
on d.pw = mt.pw
where ckd.date > '2019-01-01' and substr(ckd.x, 1, 4) = 'moo'

ORDER by goal_widgets_2019 desc, total_widgets_2019 ASC
union all select *, '   ' as moo1 from z
),
scd AS
(SELECT
  person_id,
  SPLIT_PART(option_str, '.' , 1) AS option_str,
  MIN(CASE WHEN option_str LIKE '%.1' THEN TRUNC(first_opt_time) END) AS opt1_date,
  MIN(CASE WHEN option_str LIKE '%.2' THEN TRUNC(first_opt_time) END) AS opt2_date ,
  CASE option_str
     WHEN 'option 1' THEN opt1_date + 1
     WHEN 'option 2' THEN opt1_date + 2
     WHEN 'another option' THEN opt1_date + 3
     WHEN 'option 4' THEN opt1_date + 4
     WHEN 'last option' THEN opt1_date + 5
  END AS eg_date,
  eg_date + 30 AS ct_date,
  CASE WHEN opt2_date BETWEEN start_date AND end_date THEN 100.00 ELSE 0.00 END AS opt_rate
FROM
  mytables.option
WHERE
  option_str IN
    ('option 1',
    'option 2',
    'another option',
    'option 4',
    'last option')
GROUP BY
  person_id,
  option_str limit 20)
select a, myfunction( b,  c ) as b1, 'hi there' as d -- a comment
from t inner join z on t.id = z.id and t.col = z.col
-- end comment
"""

def format_select_clause(sql):
    if sql.startswith('SELECT DISTINCT'):
        col_start_ind = 16
    elif sql.startswith('SELECT'):
        col_start_ind = 7
    elif sql.startswith('ORDER BY'):
        col_start_ind = 9
    elif sql.startswith('GROUP BY'):
        col_start_ind = 9
    cols = split_comma_sep_expressions(sql[col_start_ind:])
    for i, col in enumerate(cols):
        cols[i] = cols[i].strip()
        if cols[i].count(' THEN ') > 1:
            cols[i] = cols[i].replace(' WHEN ', '\n' + INDENT + 'WHEN ')
            cols[i] = cols[i].replace(' ELSE ', '\n' + INDENT + 'ELSE ')
            cols[i] = cols[i].replace(' END', '\nEND')
    cols = ',\n'.join(cols)
    cols = re.sub('^', INDENT, cols, flags=re.MULTILINE)
    return sql[:col_start_ind] + '\n' + cols

def format_from_clause(sql):
    sql, parens_map = protect_parens(sql, 'P')
    sql = re.sub('^FROM ', 'FROM\n', sql)
    sql = re.sub(' (ON|INNER|LEFT|FULL|AND|OR) ', r'\n\1 ', sql)
    sql = sql.replace(' JOIN ', ' JOIN\n')
    for key in parens_map:
        if parens_map[key].startswith('(SELECT'):
            subselect_sql = parens_map[key][1:-1]
            parens_map[key] = '(' + format_select_sql(subselect_sql) + ')'
    sql = unprotect(sql, parens_map)
    sql = re.sub('^', INDENT, sql, flags=re.MULTILINE)
    return sql.strip()

def format_where_clause(sql):
    sql, parens_map = protect_parens(sql, 'P')
    sql = re.sub('(^WHERE|^HAVING | AND| OR) ', r'\1\n', sql)
    sql = re.sub('^', INDENT, sql, flags=re.MULTILINE)
    return unprotect(sql, parens_map).strip()

def format_union_clause(sql):
    return sql

def format_select_sql(sql):
    blocks = select_blocks(sql)
    new_blocks = []
    for block in blocks:
        if block.startswith('SELECT'):
            block = format_select_clause(block)
        elif block.startswith('FROM'):
            block = format_from_clause(block)
        elif block.startswith('WHERE'):
            block = format_where_clause(block)
        elif block.startswith('HAVING'):
            block = format_where_clause(block)
        elif block.startswith('GROUP'):
            block = format_select_clause(block)
        elif block.startswith('ORDER'):
            block = format_select_clause(block)
        elif block.startswith('UNION'):
            block = format_union_clause(block)
        elif block.startswith('LIMIT'):
            block = format_union_clause(block)
        else:
            raise ValueError('Unknown block type:' + block)
        new_blocks.append(block)
    return '\n'.join(new_blocks)

def format_sql(sql):

    # Replace comments
    sql = re.sub('--.*', '', sql)
    # sql, comment_map = protect(sql, '--.*', 'C')
    # Replace quoted strings
    sql, sq_string_map = protect(sql, "'.*?'", 'S')
    sql, dq_string_map = protect(sql, '".*?"', 'D')
    # Ensure there is a space after all commas
    sql = sql.replace(',', ', ')
    # Put all SQL on a single line
    sql = to_single_line(sql)
    # Remove any space after/before parentheses
    sql = re.sub('\( +', '(', sql)
    sql = re.sub(' +\)', ')', sql)
    # Remove any space before commas
    sql = re.sub(' +,', ',', sql)
    # Make keywords and functions uppercase
    sql = uppercase_keywords(sql)
    sql = re.sub('\w+\(', lambda m: m.group(0).upper(), sql)
    # At this point the sql is a single line, properly cleaned up spacing,
    # and all single-quotes and parentheses have been replaced with placeholders

    if sql.startswith('WITH '):
        try:
            ind = sql.index(') SELECT')
        except ValueError:
            raise ValueError('WITH statement but no SELECT')
        with_sql = sql[:ind + 1]
        select_sql = sql[ind + 2:]
    elif sql.startswith('SELECT'):
        with_sql = None
        select_sql = sql
    else:
        raise ValueError('No SELECT statement')

    lines = []
    if with_sql:
        subselects = split_comma_sep_expressions(with_sql[5:])
        lines.append('WITH')
        for i, subselect in enumerate(subselects):
            subselect = subselect.strip()
            ind = subselect.index('(')
            subselect_sql = subselect[ind + 1:-1]
            subselects[i] = SEP + '\n' + subselect[:ind] + \
                '\n(' + format_select_sql(subselect_sql) + ')'
        lines.append(',\n'.join(subselects) + '\n' + SEP)
    lines.append(format_select_sql(select_sql))

    sql = '\n'.join(lines)
    sql = wrap(sql)
    sql = unprotect(sql, dq_string_map)
    sql = unprotect(sql, sq_string_map)
    return sql

def normalize(text):
    text = re.sub('--.*', '', text)
    return ''.join(text.split()).lower()

class SqlSelectFormatCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        text = self.view.substr(self.view.sel()[0])
        sql = '\n' + format_sql(text) + '\n'
        if normalize(text) == normalize(sql):
            self.view.replace(edit, self.view.sel()[0], sql)
        else:
            print('Unable to transform SQL')

if __name__ == '__main__':
    # new_sql = format_sql(sample_sql)
    # if normalize(sample_sql) != normalize(new_sql):
    #     print('Normalized sample:', normalize(sample_sql))
    #     print('Normalized new:', normalize(new_sql))
    # else:
    #     print(new_sql)
    unittest.main()

