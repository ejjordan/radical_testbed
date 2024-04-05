import os
import radical.pilot as rp
import radical.utils as ru
from shutil import copy
import gmxapi as gmx

report = ru.Reporter(name='radical.pilot')
report.title('Getting Started (RP version %s)' % rp.version)

session = rp.Session()
pilot_mgr = rp.PilotManager(session=session)

pd_init = {'resource'     : 'local.localhost',
           'runtime'      : 30,  # pilot runtime minutes
           'exit_on_error': True,
           'project'      : None,
           'queue'        : None,
           'cores'        : 4,
           'gpus'         : 0,
           'exit_on_error': False}
pdesc = rp.PilotDescription(pd_init)

report.header('submit pilot')
pilot = pilot_mgr.submit_pilots(pdesc)

task_mgr = rp.TaskManager(session=session)

task_mgr.add_pilots(pilot)
task_list=list()

def run_grompp():
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
    return os.path.exists(grompp.output.file['-o'].result())

def run_mdrun(tpr_path):
    output_dir="./output"
    if not os.path.exists(output_dir):
        raise InputException("You must supply a directory with a tpr file")

    tpr = "run.tpr"
    input_list = gmx.read_tpr(os.path.join(output_dir, tpr))
    md = gmx.mdrun(input_list)
    threads_per_rank=2
    runtime_args={'-nt': str(threads_per_rank)}
    md.run(runtime_args=runtime_args)
    print(md.output.stderr.result())

gromp_task = rp.TaskDescription({'mode': 'task.function',
                                 'function': 'run_grompp',
                                 'pre_exec': 'source /home/joe/pyenvs/scalems/bin/activate'})
gromp_task.ranks = 1
gromp_task.cores_per_rank = 1
task_list.append(gromp_task)

"""
mdrun_task = rp.TaskDescription({"executable": "python",
                                 "arguments": os.path.join(os.getcwd(), "mdrun.py")})
mdrun_task.ranks = 1
mdrun_task.cores_per_rank = 2
task_list.append(mdrun_task)
"""

report.header(f"submitting tasks")
tasks = task_mgr.submit_tasks(task_list)
print(f"Before wait: {tasks}")
task_mgr.wait_tasks()
print(f"After wait: {tasks}")

import ipdb;ipdb.set_trace()
for task in tasks:
    print('%s: %s' % (task.uid, task.state))

client_sandbox = ru.Url(pilot.client_sandbox).path + '/' + session.uid
pilot_sandbox  = ru.Url(pilot.pilot_sandbox).path

print('client sandbox: %s' % client_sandbox)
print('pilot  sandbox: %s' % pilot_sandbox)

report.header('finalize')
session.close(cleanup=True)
