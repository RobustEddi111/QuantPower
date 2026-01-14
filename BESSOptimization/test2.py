import gurobipy as gp
from gurobipy import GRB

m = gp.Model()
x = m.addVar(lb=0, name="x")
m.setObjective(x, GRB.MAXIMIZE)
m.optimize()
print("status", m.Status)
