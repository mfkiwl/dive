import os
os.add_dll_directory(r"C:\devel\dive\examples")

import structural
import solvers
import plots.oscillator
import math

def Harmonic(t: float, x: float, y: float, z: float) -> float:
    amplitude = 10.0
    omega = 1.0

    #return amplitude
    return amplitude * math.cos(omega * t)

mass = 1.0
stiffness = 100.0
damping = 0.5
omega = math.sqrt(stiffness / mass)
period = 2.0 * math.pi / omega
status  = 0

basis   = structural.CreateBasisCartesian(1)
timer   = structural.CreateTimerStepped(1, 0.0, 50.0 * period, 0.01)
time = []
position = []
velocity = []

T_ref   = 313.15      #[K]      = 40 [°C]
p_ref   = 101325.1    #[N/m²]   =  1 [atm]
temperature = structural.CreateValueScalar3D(T_ref)
pressure = structural.CreateValueScalar3D(p_ref)

node1 = structural.CreateNode(1, 0.0, 0.0, 0.0)
node2 = structural.CreateNode(2, 1.0, 0.0, 0.0)

spring = structural.CreateElementCombined(1)
spring.SetNode(0, node1)
spring.SetNode(1, node2)
spring.SetStiffness(structural.CreateValueScalar(stiffness))
spring.SetDamping(structural.CreateValueScalar(damping))

body = structural.CreateElementMass(3)
body.SetNode(0, node2)
body.SetMass(structural.CreateValueScalar(mass))

mesh = structural.CreateMesh(1)
mesh.AddNode(node1, status, True)
mesh.AddNode(node2, status, True)
mesh.AddElement(spring, status)
mesh.AddElement(body, status)

force = structural.CreateValueVector3DScalarsTime(3)
force.SetScalar(0, structural.CreateValueScalar3DTimeFunction(Harmonic))
#force.SetScalar(0, structural.CreateValueScalar3DTime(10.0))

structural.CreateProblem(1, mesh, temperature, pressure)
structural.ApplyDirichlet([node1], 0.0)
structural.ApplyDirichlet([node2], 0.0, dof = 1)
structural.ApplyDirichlet([node2], 0.0, dof = 2)
structural.ApplyLoadNodeTransient([node2], force)
structural.Initialize()

#--------------------------------------------------------------------------------------------------

totalDof = structural.GetProblem().GetTotalDof()
pivot = structural.GetProblem().GetPivot()

D = structural.PartitionMatrix(structural.Ellpack(totalDof, totalDof, structural.matrix_diagonal))
M = structural.PartitionMatrix(structural.GetProblem().Mass())
K = structural.PartitionMatrix(structural.GetProblem().Stiffness())
C = structural.PartitionMatrix(structural.GetProblem().Damping())
u = structural.PartitionVector(structural.GetProblem().Displacement())
v = structural.PartitionVector(structural.Vector(totalDof, 0.0))
f = structural.PartitionVector(structural.GetProblem().LoadNode(timer.GetCurrent()))

def ODE1(time, u, v):
    global M
    global C
    global K
    global f
  
    #print(body.GetNode(0).GetPoint())

    #print(force.GetValue(time, body.GetNode(0).GetPoint()))

    f = structural.PartitionVector(structural.GetProblem().LoadNode(time))
    #structural.GetProblem().LoadNode(time)

    #f[1] = force.GetValue(time, body.GetNode(0).GetPoint())
    #f[1][0] = scalar2.GetValue(time, body.GetNode(0).GetPoint())
    #f[1][0] = Harmonic(time, 0, 0, 0)
    #f[1][0] = 10.0
    #f = structural.PartitionVector(structural.GetProblem().LoadNode(time))

    return [M[3], -(C[3]*v + K[3]*u) + f[1]]

def ODE2(time, v):
    global D

    return [D[3], v]

while(timer.GetCurrent() < timer.GetEnd()):
    time.append(timer.GetCurrent())
    position.append(u[1][0])
    velocity.append(v[1][0])

    u[1], v[1] = solvers.ForwardMethod2(timer, u[1], v[1], ODE1, ODE2)

    timer.SetNextStep()

plots.oscillator.Show(time, position, velocity)