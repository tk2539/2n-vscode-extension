import re
import random
import json
import os
import sys

variables = {}
functions = {}
json_data = {}
current_json_context = None

def replace_variables(expr, check_defined=False):
    def repl(m):
        var = m.group(0)
        if re.fullmatch(r'\d+(\.\d+)?', var):
            return var
        if var in variables:
            return str(variables[var])
        elif check_defined:
            raise ValueError(f"{var}が定義されていません")
        return var
    return re.sub(r'\b\w+(?:\.\w+)*\b', repl, expr)

def calc_simple(expr):
    tokens = expr.split()
    if len(tokens) != 3:
        raise ValueError("Invalid expression")
    a, op, b = map(str.strip, tokens)
    a = float(a)
    b = float(b)
    if op not in ['+', '-', '*', '/']:
        raise ValueError(f"Unsupported operator '{op}' in expression.")
    return {
        '+': a + b,
        '-': a - b,
        '*': a * b,
        '/': a / b
    }[op]

def eval_condition_line(line):
    if line.startswith("if ?(") or line.startswith("else if ?("):
        cond = line.split("?(", 1)[1].rsplit(")", 1)[0]
        cond = replace_variables(cond, check_defined=True)
        return eval(cond, {}, {})
    elif line == "else":
        return True
    return False

def evaluate(expr):
    if expr.startswith("action "):
        match = re.match(r"action\s+(\w+)\s*\(\)", expr)
        if not match:
            raise ValueError("Invalid action format")
        func_name = match.group(1)
        if func_name not in functions:
            raise ValueError(f"関数 '{func_name}' は定義されていません")
        parse_and_execute_block(functions[func_name])
        return None

    elif expr.startswith("print "):
        match = re.match(r'print\s+"(.*?)"', expr)
        if match:
            print(match.group(1))
        else:
            raise ValueError("Invalid print format. Use: print \"...\"")
        return None

    elif expr.startswith("output "):
        parts = expr.split()
        if len(parts) != 2:
            raise ValueError("output 構文が不正です。正しい形式: output 変数名")
        var_name = parts[1]
        if var_name in variables:
            print(variables[var_name])
        else:
            raise ValueError(f"{var_name}が定義されていません")
        return None

    elif expr.startswith("?(") and expr.endswith(")"):
        condition = expr[2:-1].strip()
        condition_replaced = replace_variables(condition, check_defined=True)
        result = eval(condition_replaced, {}, {})
        print("true" if result else "false")
        return None

    elif expr == "break":
        raise StopIteration

    elif expr.startswith("input "):
        match = re.match(r"input\s+(\w+)\s*=\s*(.+)", expr)
        if not match:
            raise ValueError("Invalid input format.")
        var_name, value_expr = match.groups()

        match_random = re.match(r"random\[\s*(.*?)\s*\]$", value_expr.replace(" ", ""))
        if match_random:
            content = match_random.group(1)
            if content in variables:
                values = variables[content]
                if not isinstance(values, list):
                    raise ValueError(f"{content} はリストではありません")
            else:
                values = [float(v.strip()) for v in content.split(',') if v.strip()]
            if not values:
                raise ValueError("ランダム対象のリストが空です")
            result = random.choice(values)
            variables[var_name] = result
            return None

        result = evaluate(value_expr)
        variables[var_name] = result
        return None

    elif expr.startswith("addlist "):
        match = re.match(r"addlist\s+(\w+(?:\.\w+)*)\s*=\s*(.+)", expr)
        if not match:
            raise ValueError("Invalid addlist format.")
        var_name, values = match.groups()
        
        # 値が json.getkey のとき
        if values.startswith("json.getkey "):
            keyname = values[len("json.getkey "):].strip()
            if current_json_context is None:
                raise ValueError("json.getkey は operation ブロックの中でしか使えません")
            if keyname not in json_data[current_json_context]:
                raise ValueError(f"JSON '{current_json_context}' にキー '{keyname}' は存在しません")
            extracted = json_data[current_json_context][keyname]
            if not isinstance(extracted, list):
                raise ValueError(f"'{keyname}' の値はリストではありません")
            values = extracted
        elif values in variables:
            # 変数の中にあれば、その型によって処理
            val = variables[values]
            if isinstance(val, list):
                values = val
            else:
                values = [float(val)]
        else:
            # 普通の文字列として , 区切りリストとみなす
            values = [float(v.strip()) for v in values.split(',') if v.strip()]
        
        if var_name in variables:
            if not isinstance(variables[var_name], list):
                raise ValueError(f"{var_name} はリストではありません")
            merged = variables[var_name] + values
            variables[var_name] = sorted(set(merged))
        else:
            variables[var_name] = sorted(set(values))
        return None

    elif expr.startswith("getlist "):
        match = re.match(r"getlist\s+(\w+(?:\.\w+)*)\s*=\s*json\.addkey\s+(\w+)", expr)
        if not match:
            raise ValueError("Invalid getlist format or missing 'json.addkey'")
        var_name, keyname = match.groups()
        if current_json_context is None:
            raise ValueError("json.addkey は operation ブロックの中でしか使えません")
        if var_name not in variables or not isinstance(variables[var_name], list):
            raise ValueError(f"{var_name} は存在しないかリストではありません")
        json_data[current_json_context][keyname] = variables[var_name]
        return None

    expr = replace_variables(expr)
    while '(' in expr:
        expr = re.sub(r'\(([^()]+)\)', lambda m: str(calc_simple(m.group(1))), expr)
    return float(expr)

def collect_block(lines, start_index):
    block = []
    i = start_index
    if i >= len(lines) or lines[i] != "{":
        raise SyntaxError("Expected '{' to start block")
    i += 1
    depth = 0
    while i < len(lines):
        line = lines[i]
        if line == "{":
            depth += 1
            block.append(line)
        elif line == "}":
            if depth == 0:
                return block, i + 1
            else:
                depth -= 1
                block.append(line)
        else:
            block.append(line)
        i += 1
    raise SyntaxError("Expected '}' to close block")

def parse_and_execute(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    parse_and_execute_block(lines)

def parse_and_execute_block(lines):
    i = 0
    while i < len(lines):
        line = lines[i]

        if line in ("{", "}"):
            i += 1
            continue

        if line.startswith("if ?(") or line.startswith("else if ?(") or line == "else":
            branches = []
            while i < len(lines) and (lines[i].startswith("if ?(") or lines[i].startswith("else if ?(") or lines[i] == "else"):
                cond = lines[i]
                block, i = collect_block(lines, i + 1)
                branches.append((cond, block))
            executed = False
            for cond, block in branches:
                try:
                    if not executed and eval_condition_line(cond):
                        parse_and_execute_block(block)
                        executed = True
                except StopIteration:
                    raise
                except Exception as e:
                    print(f"Error in line: {cond}")
                    print(f"  {e}")

        elif line == "while":
            block, i = collect_block(lines, i + 1)
            while True:
                try:
                    parse_and_execute_block(block)
                except StopIteration:
                    break

        elif line.startswith("for "):
            count_expr = line[4:].strip()
            block, i = collect_block(lines, i + 1)
            count = evaluate(count_expr)
            for _ in range(int(count)):
                try:
                    parse_and_execute_block(block)
                except StopIteration:
                    break

        elif line.startswith("function "):
            func_name = line[9:].strip()
            block, i = collect_block(lines, i + 1)
            functions[func_name] = block

        elif line.startswith("import.2n"):
            parts = line.split()
            if len(parts) >= 2:
                import_path = parts[1]
                try:
                    parse_and_execute(import_path)
                except Exception as e:
                    print(f"Error importing {import_path}: {e}")
            i += 1

        elif line.startswith("import.json"):
            parts = line.split()
            if len(parts) >= 2:
                path = parts[1]
                try:
                    name = os.path.basename(path).split('.')[0]
                    with open(path, 'r', encoding='utf-8') as jf:
                        json_data[name] = json.load(jf)
                except Exception as e:
                    print(f"Error loading JSON {path}: {e}")
            i += 1

        elif line.startswith("operation "):
            op_name = line[len("operation "):].strip()
            block, i = collect_block(lines, i + 1)
            if op_name not in json_data:
                print(f"Error: JSON '{op_name}' が読み込まれていません")
            else:
                global current_json_context
                current_json_context = op_name
                parse_and_execute_block(block)
                with open(f"{op_name}.json", "w", encoding="utf-8") as f:
                    json.dump(json_data[op_name], f, ensure_ascii=False, indent=2)
                current_json_context = None

        else:
            try:
                evaluate(line)
            except StopIteration:
                raise
            except Exception as e:
                print(f"Error in line: {line}")
                print(f"  {e}")
            i += 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python main.py ファイル名.2n")
    else:
        parse_and_execute(sys.argv[1])