from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
from copy import deepcopy

app = FastAPI(
    title="Lambda Calculus",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LAMBDA = "\u03BB"

class LambdaExpression:
    def __init__(self):
        pass

    def evaluate(self, x):
        return x
    
    def __str__(self):
        pass
    
class Application(LambdaExpression):
    def __init__(self, exp1, exp2):
        self.exp1 = exp1
        self.exp2 = exp2

    def evaluate(self, x):
        return super().evaluate(x)
    
    def __str__(self):
        return f"({self.exp1}{self.exp2})" if type(self.exp2) == Variable else f"{self.exp1}{self.exp2}"

    def __repr__(self) -> str:
        return f"Application({repr(self.exp1)}, {repr(self.exp2)})"

    
class Variable(LambdaExpression):
    def __init__(self, value):
        self.value = value
    
    def evaluate(self, x):
        return Variable(x)
    
    def __str__(self):
        return self.value

    def __repr__(self) -> str:
        return f"Variable({repr(self.value)})"
    
class Abstraction(LambdaExpression):
    def __init__(self, value, exp):
        self.value = value
        self.exp = exp

    def evaluate(self, x):
        return Abstraction(self.value, self.exp.evaluate(x))
    
    def __str__(self):
        return f"{LAMBDA}{self.value}.{self.exp}"

    def __repr__(self) -> str:
        return f"Abstraction({repr(self.value)}, {repr(self.exp)})"

def preform_bidmas(expression:str) -> list[str]:

    expression = expression.replace(")", "\"],\"")
    expression = expression.replace("(", "\",[\"")
    expression = expression[2:-2]
    expression = expression.replace("\"\",", "")
    expression = expression.replace(",\"\"", "")
    expression = eval(expression)

    return expression
    

def parse_expression(expression_list: list[str]) -> LambdaExpression:
    if len(expression_list) == 1 and len(expression_list[0]) == 1:
        expression_list = expression_list[0]
    if LAMBDA in expression_list[0]:
        value, *exp = expression_list[0][1:].split(".")
        exp = ".".join(exp)
        return Abstraction(value, parse_expression([exp]))
    if len(expression_list) == 1:
        if len(expression_list[0]) == 1:

            return Variable(expression_list[0][0])
        elif type(expression_list) == str:
            if LAMBDA in expression_list:
                value, *exp = expression_list[1:].split(".")
                exp = ".".join(exp)
                return Abstraction(value, parse_expression([exp]))

            return parse_expression(expression_list.split(""))
        else:
            return parse_expression(expression_list[0])


    return Application(parse_expression(expression_list[:-1]), parse_expression(expression_list[-1]))

def beta_reduction(expression: LambdaExpression) -> LambdaExpression:
    def _substitute(expression: LambdaExpression, value: str, exp: LambdaExpression) -> LambdaExpression:
        if type(expression) == Variable:
            if expression.value == value:
                return exp
            else:
                return expression
        elif type(expression) == Application:
            return Application(_substitute(expression.exp1, value, exp), _substitute(expression.exp2, value, exp))
        elif type(expression) == Abstraction:
            if expression.value == value:
                return expression
            else:
                return Abstraction(expression.value, _substitute(expression.exp, value, exp))
    # base case
    if type(expression) == Variable:
        return expression
    elif type(expression) == Application:
        if type(expression.exp1) == Abstraction:
            return _substitute(expression.exp1.exp, expression.exp1.value, expression.exp2)
        else:
            return Application(beta_reduction(expression.exp1), beta_reduction(expression.exp2))
    elif type(expression) == Abstraction:
        return Abstraction(expression.value, beta_reduction(expression.exp))

def free_variables(max_length) -> chr:
    for i in range(97, 123):
        yield chr(i)

vars = free_variables(5)

def random_lambda_expression(depth: int, set_free_variables: set[chr]) -> LambdaExpression:
    if depth == 0:
        return Variable(random.choice(set_free_variables))
    else:
        if random.random() < 0.3:
            return Variable(random.choice(set_free_variables))
        elif random.random() < 0.8:
            return Application(random_lambda_expression(depth-1, set_free_variables), random_lambda_expression(depth-1, set_free_variables))
        else:
            new_free_variable = random.choice(set_free_variables)
            return Abstraction(new_free_variable, random_lambda_expression(depth-1, set_free_variables))
        
def get_beta_steps(expression: LambdaExpression, steps: int) -> LambdaExpression:
    expressions = []
    for i in range(steps):
        expression = beta_reduction(expression)
        expressions.append(str(expression))
    ordered_unique_expressions = []
    for expression in expressions:
        if expression not in ordered_unique_expressions:
            ordered_unique_expressions.append(expression)
    return ordered_unique_expressions

@app.post("/evaluate")
async def evaluate(expression: str):
    expression_list = preform_bidmas(expression)
    expression = parse_expression(expression_list)
    for i in range(100):
        expression = beta_reduction(expression)
    return {"expression": str(expression)}

@app.get("/random")
async def random_expression():
    expression = random_lambda_expression(5, [chr(i) for i in range(97, 123)][:5])
    steps = get_beta_steps(expression, 4)
    while len(steps) < 4:
        expression = random_lambda_expression(5, [chr(i) for i in range(97, 123)][:5])
        steps = get_beta_steps(expression, 4)
    return {"steps": steps, "expression": str(expression)}