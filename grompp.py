import os
from shutil import copy
import gmxapi as gmx

input_dir='/home/joe/experiments/radical/alanine-dipeptide'
output_dir="./output"
if not os.path.exists(output_dir):
  os.mkdir(output_dir)

input_gro = os.path.join(input_dir, "equil3.gro")
input_top = os.path.join(input_dir, "topol.top")
input_mdp = os.path.join(input_dir, "grompp.mdp")
input_files={'-f': input_mdp, '-p': input_top, '-c': input_gro,},
tpr = "run.tpr"
output_files={'-o': tpr}
grompp = gmx.commandline_operation(gmx.commandline.cli_executable(), 'grompp', input_files, output_files)
grompp.run()
print(grompp.output.stderr.result())
assert os.path.exists(grompp.output.file['-o'].result())
copy(grompp.output.file['-o'].result(), os.path.join(output_dir, tpr))
