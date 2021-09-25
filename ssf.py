import re
import pathlib

def parse_testcases():
    p = pathlib.Path(__file__).with_name('testcases.txt')
    with p.open('rt') as f:
        sections = f.read().split('###')
        sections.pop(0)
    testcases = []
    for section in sections:
        first_line, rest = section.split('\n', maxsplit=1)
        test_name = first_line.strip()
        input_sql, expected_output = rest.split('->')
        input_sql = input_sql.strip()
        expected_output = expected_output.strip()
        testcases.append((test_name, input_sql, expected_output))
    return testcases

def protect(text):
    patterns = ('".*?"', "'.*?'", '--.*', '(?s)/\*.*?\*/')
    protected = []
    def subfunc(m):
        protected.append(m.group(0))
        return '[protected' + str(len(protected)) + ']'
    for pat in patterns:
        text = re.sub(pat, subfunc, text)
    return text

def uppercase_keywords(tokens):
    # Convert all keywords to uppercase
    keywords = ['WITH', 'AS', 'SELECT', 'FROM', 'WHERE', 'AND', 'OR',
        'NOT', 'LEFT', 'RIGHT', 'FULL', 'INNER', 'OUTER', 'JOIN',
        'GROUP', 'BY', 'OVER', 'HAVING', 'BETWEEN', 'ON', 'CASE', 'WHEN',
        'THEN', 'DISTINCT', 'ORDER', 'DESC', 'ASC',
        'UNION', 'ALL', 'END', 'LIMIT']
    return [token.upper() if token.upper() in keywords else token for
        token in tokens]

def uppercase_functions(tokens):
    return [re.sub('^\w+?\(', lambda m: m.group(0).upper(), token) for
        token in tokens]

def format_sql(sql):
    s = protect(sql)
    tokens = s.split()
    tokens = uppercase_keywords(tokens)
    tokens = uppercase_functions(tokens)
    formatted_sql = tokens
    return formatted_sql

if __name__ == '__main__':
    testcases = parse_testcases()
    for (test_name, input_sql, expected_output) in testcases[:1]:
        print('Test name:', test_name)
        print('\nInput:')
        print(input_sql)
        print('\nOutput:')
        print(format_sql(input_sql))
        print('=' * 72)


