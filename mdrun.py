import os
from shutil import copy
import gmxapi as gmx

output_dir="./output"
if not os.path.exists(output_dir):
  raise InputException("You must supply a directory with a tpr file")

tpr = "run.tpr"
input_list = gmx.read_tpr(os.path.join(output_dir, tpr))
md = gmx.mdrun(input_list)
threads_per_rank=2
runtime_args={'-nt': str(threads_per_rank)
md.run(runtime_args=runtime_args)
print(md.output.stderr.result())
