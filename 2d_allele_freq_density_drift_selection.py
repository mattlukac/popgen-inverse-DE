from fenics import *
from ufl import diag_vector
import numpy as np
import sympy as sym

T = 100.0	    # final time
num_steps = 200     # number of time steps
dt = T / num_steps  # time step size
N1, N2 = 20, 10     # effective population size for pop 1 and 2
Nref = 100          # reference effective population size
nu1, nu2 = N1/Nref, N2/Nref         # relative effective population size
epsilon = 0.0       # distance from 0 and 1
p1, p2 = 0.5, 0.5   # initial x and y frequencies
s1, s2 = 50, 100    # 1/(root(2)sigma_x) and 1/(root(2)sigma_y)
#g1, g2 = 0.05, 0.01   # 2Ns for each population

# Create mesh and define function space
n1, n2 = 50, 50
mesh = RectangleMesh(Point(epsilon, epsilon), Point(1-epsilon, 1-epsilon), n1, n2)
V = FunctionSpace(mesh, 'P', 1)

# Define boundary condition 
#u_D = Expression('-t/(2*N)+nu', 
#                     degree=2 , N=N, nu=nu, t=0)

def boundary(x, on_boundary):
    return on_boundary

bc = DirichletBC(V, Constant(0.0), boundary)
#bc = []    # no boundary condition

# Define initial value of Gaussian with low variance
u_0 = Expression('s1*s2*exp(-(pow(s1*(x[0]-p1), 2) + pow(s2*(x[1]-p2), 2)))/pi', 
        s1=s1, s2=s2, p1=p1, p2=p2, degree=2)
#u_n = interpolate(u_D, V)
u_n = project(u_0, V)

# Define variational problem
u = TrialFunction(V)
v = TestFunction(V)

# Drift term
drift = Expression(('x[0]*(1-x[0])/N1', 'x[1]*(1-x[1])/N2'),
          N1=N1, N2=N2, degree = 2, domain=mesh)

# Selection term with time dependent 2Ns
sel = Expression(('(0.08*cos(0.1*t))*x[0]*(1-x[0])', 
    '(0.008*cos(0.05*t))*x[1]*(1-x[1])'),
    t=0, degree = 2, domain=mesh)

a = u*v*dx + dt/4 * inner(diag_vector(grad(drift*u)), grad(v))*dx - dt*u*inner(sel, grad(v))*dx 
L = u_n*v*dx

# Create VTK file for saving solution
vtkfile = File('solutions/2d_allele_freq_density_drift_selection/solution.pvd')

# Time-stepping
u = Function(V)
t = 0
for _ in range(num_steps):
    
    # Update current time
    t += dt
    sel.t = t
    
    # Compute solution and integrate to 1
    solve(a == L, u, bc)
    u.vector()[:] = n1*n2*u.vector()[:] / np.sum(u.vector()[:])

    # Save to file and plot solution
    vtkfile << (u, t)
    plot(u)

    # Update previous solution
    u_n.assign(u)

