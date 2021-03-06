#> Main script
import os

# Intialise OpenCMISS-Iron
from opencmiss.iron import iron

# Set problem parameters

width = 60.0
length = 40.0
height = 40.0
density=9.0E-4 #in g mm^-3
gravity=[0.0,0.0,-9.81] #in m s^-2

usePressureBasis = False
NumberOfGaussXi = 2

coordinateSystemUserNumber = 1
regionUserNumber = 1
basisUserNumber = 1
pressureBasisUserNumber = 2
generatedMeshUserNumber = 1
meshUserNumber = 1
decompositionUserNumber = 1
geometricFieldUserNumber = 1
fibreFieldUserNumber = 2
materialFieldUserNumber = 3
dependentFieldUserNumber = 4
sourceFieldUserNumber = 5
equationsSetFieldUserNumber = 6
equationsSetUserNumber = 1
problemUserNumber = 1

# Set all diganostic levels on for testing
#iron.DiagnosticsSetOn(iron.DiagnosticTypes.All,[1,2,3,4,5],"Diagnostics",["DOMAIN_MAPPINGS_LOCAL_FROM_GLOBAL_CALCULATE"])

numberOfLoadIncrements = 1
numberGlobalXElements = 1
numberGlobalYElements = 1
numberGlobalZElements = 1
InterpolationType = 1
if(numberGlobalZElements==0):
    numberOfXi = 2
else:
    numberOfXi = 3

# Get the number of computational nodes and this computational node number
numberOfComputationalNodes = iron.ComputationalNumberOfNodesGet()
computationalNodeNumber = iron.ComputationalNodeNumberGet()

# Create a 3D rectangular cartesian coordinate system
coordinateSystem = iron.CoordinateSystem()
coordinateSystem.CreateStart(coordinateSystemUserNumber)
coordinateSystem.DimensionSet(3)
coordinateSystem.CreateFinish()

# Create a region and assign the coordinate system to the region
region = iron.Region()
region.CreateStart(regionUserNumber,iron.WorldRegion)
region.LabelSet("Region")
region.coordinateSystem = coordinateSystem
region.CreateFinish()

# Define basis
basis = iron.Basis()
basis.CreateStart(basisUserNumber)
if InterpolationType in (1,2,3,4):
    basis.type = iron.BasisTypes.LAGRANGE_HERMITE_TP
elif InterpolationType in (7,8,9):
    basis.type = iron.BasisTypes.SIMPLEX
basis.numberOfXi = numberOfXi
basis.interpolationXi = [iron.BasisInterpolationSpecifications.LINEAR_LAGRANGE]*numberOfXi
if(NumberOfGaussXi>0):
    basis.quadratureNumberOfGaussXi = [NumberOfGaussXi]*numberOfXi
basis.CreateFinish()

if(usePressureBasis):
    # Define pressure basis
    pressureBasis = iron.Basis()
    pressureBasis.CreateStart(pressureBasisUserNumber)
    if InterpolationType in (1,2,3,4):
        pressureBasis.type = iron.BasisTypes.LAGRANGE_HERMITE_TP
    elif InterpolationType in (7,8,9):
        pressureBasis.type = iron.BasisTypes.SIMPLEX
    pressureBasis.numberOfXi = numberOfXi
    pressureBasis.interpolationXi = [iron.BasisInterpolationSpecifications.LINEAR_LAGRANGE]*numberOfXi
    if(NumberOfGaussXi>0):
        pressureBasis.quadratureNumberOfGaussXi = [NumberOfGaussXi]*numberOfXi
    pressureBasis.CreateFinish()

# Start the creation of a generated mesh in the region
generatedMesh = iron.GeneratedMesh()
generatedMesh.CreateStart(generatedMeshUserNumber,region)
generatedMesh.type = iron.GeneratedMeshTypes.REGULAR
if(usePressureBasis):
    generatedMesh.basis = [basis,pressureBasis]
else:
    generatedMesh.basis = [basis]
if(numberGlobalZElements==0):
    generatedMesh.extent = [width,height]
    generatedMesh.numberOfElements = [numberGlobalXElements,numberGlobalYElements]
else:
    generatedMesh.extent = [width,length,height]
    generatedMesh.numberOfElements = [numberGlobalXElements,numberGlobalYElements,numberGlobalZElements]
# Finish the creation of a generated mesh in the region
mesh = iron.Mesh()
generatedMesh.CreateFinish(meshUserNumber,mesh)

# Create a decomposition for the mesh
decomposition = iron.Decomposition()
decomposition.CreateStart(decompositionUserNumber,mesh)
decomposition.type = iron.DecompositionTypes.CALCULATED
decomposition.numberOfDomains = numberOfComputationalNodes
decomposition.CreateFinish()

# Create a field for the geometry
geometricField = iron.Field()
geometricField.CreateStart(geometricFieldUserNumber,region)
geometricField.MeshDecompositionSet(decomposition)
geometricField.TypeSet(iron.FieldTypes.GEOMETRIC)
geometricField.VariableLabelSet(iron.FieldVariableTypes.U,"Geometry")
geometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,1,1)
geometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,2,1)
geometricField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,3,1)
if InterpolationType == 4:
    geometricField.fieldScalingType = iron.FieldScalingTypes.ARITHMETIC_MEAN
geometricField.CreateFinish()

# Update the geometric field parameters from generated mesh
generatedMesh.GeometricParametersCalculate(geometricField)

# Create a fibre field and attach it to the geometric field
fibreField = iron.Field()
fibreField.CreateStart(fibreFieldUserNumber,region)
fibreField.TypeSet(iron.FieldTypes.FIBRE)
fibreField.MeshDecompositionSet(decomposition)
fibreField.GeometricFieldSet(geometricField)
fibreField.VariableLabelSet(iron.FieldVariableTypes.U,"Fibre")
if InterpolationType == 4:
    fibreField.fieldScalingType = iron.FieldScalingTypes.ARITHMETIC_MEAN
fibreField.CreateFinish()

# Create the equations_set
equationsSetField = iron.Field()
equationsSet = iron.EquationsSet()
equationsSetSpecification = [iron.EquationsSetClasses.ELASTICITY,
    iron.EquationsSetTypes.FINITE_ELASTICITY,
    iron.EquationsSetSubtypes.MOONEY_RIVLIN]
equationsSet.CreateStart(equationsSetUserNumber,region,fibreField,
    equationsSetSpecification, equationsSetFieldUserNumber, equationsSetField)
equationsSet.CreateFinish()

# Create the dependent field
dependentField = iron.Field()
equationsSet.DependentCreateStart(dependentFieldUserNumber,dependentField)
dependentField.VariableLabelSet(iron.FieldVariableTypes.U,"Dependent")
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U,4,iron.FieldInterpolationTypes.ELEMENT_BASED)
dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.DELUDELN,4,iron.FieldInterpolationTypes.ELEMENT_BASED)
if(usePressureBasis):
    # Set the pressure to be nodally based and use the second mesh component
    if InterpolationType == 4:
        dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.U,4,iron.FieldInterpolationTypes.NODE_BASED)
        dependentField.ComponentInterpolationSet(iron.FieldVariableTypes.DELUDELN,4,iron.FieldInterpolationTypes.NODE_BASED)
    dependentField.ComponentMeshComponentSet(iron.FieldVariableTypes.U,4,2)
    dependentField.ComponentMeshComponentSet(iron.FieldVariableTypes.DELUDELN,4,2)
if InterpolationType == 4:
    dependentField.fieldScalingType = iron.FieldScalingTypes.ARITHMETIC_MEAN
equationsSet.DependentCreateFinish()


# Initialise dependent field from undeformed geometry and displacement bcs and set hydrostatic pressure
iron.Field.ParametersToFieldParametersComponentCopy(
    geometricField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,1,
    dependentField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,1)
iron.Field.ParametersToFieldParametersComponentCopy(
    geometricField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,2,
    dependentField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,2)
iron.Field.ParametersToFieldParametersComponentCopy(
    geometricField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,3,
    dependentField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,3)
iron.Field.ComponentValuesInitialiseDP(
    dependentField,iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,4,0.0)

# Create the material field
materialField = iron.Field()
equationsSet.MaterialsCreateStart(materialFieldUserNumber,materialField)
materialField.VariableLabelSet(iron.FieldVariableTypes.U,"Material")
materialField.VariableLabelSet(iron.FieldVariableTypes.V,"Density")
equationsSet.MaterialsCreateFinish()

# Set Mooney-Rivlin constants c10 and c01 respectively.
materialField.ComponentValuesInitialiseDP(
    iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,1,2.0)
materialField.ComponentValuesInitialiseDP(
    iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,2,2.0)
materialField.ComponentValuesInitialiseDP(
    iron.FieldVariableTypes.V,iron.FieldParameterSetTypes.VALUES,1,density)

#Create the source field with the gravity vector
sourceField = iron.Field()
equationsSet.SourceCreateStart(sourceFieldUserNumber,sourceField)
if InterpolationType == 4:
    sourceField.fieldScalingType = iron.FieldScalingTypes.ARITHMETIC_MEAN
else:
    sourceField.fieldScalingType = iron.FieldScalingTypes.UNIT
equationsSet.SourceCreateFinish()

#Set the gravity vector component values
sourceField.ComponentValuesInitialiseDP(
    iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,1,gravity[0])
sourceField.ComponentValuesInitialiseDP(
    iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,2,gravity[1])
sourceField.ComponentValuesInitialiseDP(
    iron.FieldVariableTypes.U,iron.FieldParameterSetTypes.VALUES,3,gravity[2])

# Create equations
equations = iron.Equations()
equationsSet.EquationsCreateStart(equations)
equations.sparsityType = iron.EquationsSparsityTypes.SPARSE
equations.outputType = iron.EquationsOutputTypes.NONE
equationsSet.EquationsCreateFinish()

# Define the problem
problem = iron.Problem()
problemSpecification = [iron.ProblemClasses.ELASTICITY,
        iron.ProblemTypes.FINITE_ELASTICITY,
        iron.ProblemSubtypes.NONE]
problem.CreateStart(problemUserNumber, problemSpecification)
problem.CreateFinish()

# Create the problem control loop
problem.ControlLoopCreateStart()
controlLoop = iron.ControlLoop()
problem.ControlLoopGet([iron.ControlLoopIdentifiers.NODE],controlLoop)
controlLoop.MaximumIterationsSet(numberOfLoadIncrements)
problem.ControlLoopCreateFinish()

# Create problem solver
nonLinearSolver = iron.Solver()
linearSolver = iron.Solver()
problem.SolversCreateStart()
problem.SolverGet([iron.ControlLoopIdentifiers.NODE],1,nonLinearSolver)
nonLinearSolver.outputType = iron.SolverOutputTypes.PROGRESS
nonLinearSolver.NewtonJacobianCalculationTypeSet(iron.JacobianCalculationTypes.FD)
nonLinearSolver.NewtonAbsoluteToleranceSet(1e-14)
nonLinearSolver.NewtonSolutionToleranceSet(1e-14)
nonLinearSolver.NewtonRelativeToleranceSet(1e-14)
nonLinearSolver.NewtonLinearSolverGet(linearSolver)
linearSolver.linearType = iron.LinearSolverTypes.DIRECT
#linearSolver.libraryType = iron.SolverLibraries.LAPACK
problem.SolversCreateFinish()

# Create solver equations and add equations set to solver equations
solver = iron.Solver()
solverEquations = iron.SolverEquations()
problem.SolverEquationsCreateStart()
problem.SolverGet([iron.ControlLoopIdentifiers.NODE],1,solver)
solver.SolverEquationsGet(solverEquations)
solverEquations.sparsityType = iron.SolverEquationsSparsityTypes.SPARSE
equationsSetIndex = solverEquations.EquationsSetAdd(equationsSet)
problem.SolverEquationsCreateFinish()

# Prescribe boundary conditions (absolute nodal parameters)
boundaryConditions = iron.BoundaryConditions()
solverEquations.BoundaryConditionsCreateStart(boundaryConditions)
# Set x=0 nodes to no x displacment
boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,1,1,1,iron.BoundaryConditionsTypes.FIXED,0.0)
boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,1,3,1,iron.BoundaryConditionsTypes.FIXED,0.0)
boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,1,5,1,iron.BoundaryConditionsTypes.FIXED,0.0)
boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,1,7,1,iron.BoundaryConditionsTypes.FIXED,0.0)

# Set y=0 nodes to no y displacement
boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,1,1,2,iron.BoundaryConditionsTypes.FIXED,0.0)
boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,1,3,2,iron.BoundaryConditionsTypes.FIXED,0.0)
boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,1,5,2,iron.BoundaryConditionsTypes.FIXED,0.0)
boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,1,7,2,iron.BoundaryConditionsTypes.FIXED,0.0)

# Set z=0 nodes to no y displacement
boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,1,1,3,iron.BoundaryConditionsTypes.FIXED,0.0)
boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,1,3,3,iron.BoundaryConditionsTypes.FIXED,0.0)
boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,1,5,3,iron.BoundaryConditionsTypes.FIXED,0.0)
boundaryConditions.AddNode(dependentField,iron.FieldVariableTypes.U,1,1,7,3,iron.BoundaryConditionsTypes.FIXED,0.0)
solverEquations.BoundaryConditionsCreateFinish()

# Solve the problem
problem.Solve()

if not os.path.exists("./results"):
    os.makedirs("./results")

# Export results
fields = iron.Fields()
fields.CreateRegion(region)
fields.NodesExport("./results/Cantilever","FORTRAN")
fields.ElementsExport("./results/Cantilever","FORTRAN")
fields.Finalise()

