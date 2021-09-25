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
    for pat in patterns:
        text = re.sub(pat, lambda m: '[' + m.group(0) + ']', text)
    return text


def format_sql(sql):
    return protect(sql)

if __name__ == '__main__':
    testcases = parse_testcases()
    for (test_name, input_sql, expected_output) in testcases[:1]:
        print('Test name:', test_name)
        print('\nInput:')
        print(input_sql)
        print('\nOutput:')
        print(format_sql(input_sql))
        print('=' * 72)


