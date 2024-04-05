import os
import radical.pilot as rp
import radical.utils as ru
from shutil import copy
import gmxapi as gmx

@rp.pythontask
def run_grompp():
    import os
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
    return grompp.output.file['-o'].result()
    
@rp.pythontask
def run_mdrun(tpr_path):
    import os
    import gmxapi as gmx
    output_dir="./output"
    if not os.path.exists(tpr_path):
        raise InputException("You must supply a valid a tpr file")

    input_files={'-s': tpr_path}
    output_files={'-x':'alanine-dipeptide.xtc', '-c': 'result.gro'}
    md = gmx.commandline_operation(gmx.commandline.cli_executable(), 'mdrun', input_files, output_files)
    md.run()
    print(md.output.stderr.result())
    assert os.path.exists(md.output.file['-c'].result())
    return md.output.file['-c'].result()

#import ipdb;ipdb.set_trace()
ve_path = os.path.dirname(os.path.dirname(ru.which('python3')))

report = ru.Reporter(name='radical.pilot')
report.title('Getting Started (RP version %s)' % rp.version)

# create session and managers
session = rp.Session()
pilot_mgr    = rp.PilotManager(session)
task_mgr    = rp.TaskManager(session)

pdesc = rp.PilotDescription({'resource'     : 'local.localhost',
           'runtime'      : 30,  # pilot runtime minutes
           'exit_on_error': True,
           'project'      : None,
           'queue'        : None,
           'cores'        : 4,
           'gpus'         : 0,
           'exit_on_error': False})

pilot = pilot_mgr.submit_pilots(pdesc)
report.header('submit pilot')
env_name = 'local'
pilot.prepare_env(env_name=env_name, env_spec={"type": "venv", "path": ve_path, "setup": []})

# add the pilot to the task manager and wait for the pilot to become active
task_mgr.add_pilots(pilot)
pilot.wait(rp.PMGR_ACTIVE)
print('pilot is up and running')

master_descr = {'mode'     : rp.RAPTOR_MASTER,
                'named_env': env_name}
worker_descr = {'mode'     : rp.RAPTOR_WORKER,
                'named_env': env_name}

raptor  = pilot.submit_raptors( [rp.TaskDescription(master_descr)])[0]
workers = raptor.submit_workers([rp.TaskDescription(worker_descr),
                                 rp.TaskDescription(worker_descr)])

task_list=list()

@rp.pythontask
def msg(val: int):
    if(val %2 == 0):
        print("Regular message")
    else:
        print(f"This is a very odd message: {val}")

grompp_task_desc = rp.TaskDescription({'mode': rp.TASK_FUNCTION,
                                       'function': run_grompp(),})
grompp_task = raptor.submit_tasks([grompp_task_desc])[0]

print(grompp_task)
task_mgr.wait_tasks([grompp_task.uid])
print('id: %s [%s]:\n    out:\n%s\n    ret: %s\n'
     % (grompp_task.uid, grompp_task.state, grompp_task.stdout, grompp_task.return_value))

mdrun_task_desc = rp.TaskDescription({'mode': rp.TASK_FUNCTION,
                                      'function': run_mdrun(grompp_task.return_value),})
mdrun_task = raptor.submit_tasks([mdrun_task_desc])[0]

print(mdrun_task)
task_mgr.wait_tasks([mdrun_task.uid])
print('id: %s [%s]:\n    out:\n%s\n    ret: %s\n'
     % (mdrun_task.uid, mdrun_task.state, mdrun_task.stdout, mdrun_task.return_value))

client_sandbox = ru.Url(pilot.client_sandbox).path + '/' + session.uid
pilot_sandbox  = ru.Url(pilot.pilot_sandbox).path

print(f'client sandbox: {client_sandbox}')
print(f'pilot  sandbox: {pilot_sandbox}')

report.header('finalize')
session.close()
"""


gromp_task = rp.TaskDescription({'mode': 'task.function',
                                 'function': 'run_grompp',
                                 'pre_exec': 'source /home/joe/pyenvs/scalems/bin/activate'})
gromp_task.ranks = 1
gromp_task.cores_per_rank = 1
task_list.append(gromp_task)


mdrun_task = rp.TaskDescription({"executable": "python",
                                 "arguments": os.path.join(os.getcwd(), "mdrun.py")})
mdrun_task.ranks = 1
mdrun_task.cores_per_rank = 2
task_list.append(mdrun_task)


report.header(f"submitting tasks")
tasks = task_mgr.submit_tasks(task_list)
print(f"Before wait: {tasks}")
task_mgr.wait_tasks()
print(f"After wait: {tasks}")

"""
