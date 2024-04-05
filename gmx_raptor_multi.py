import os
import radical.pilot as rp
import radical.utils as ru
from shutil import copy
import gmxapi as gmx

@rp.pythontask
def run_grompp(input_gro: str, verbose: bool = False):
    import os
    import gmxapi as gmx
    input_dir='/home/joe/experiments/radical/alanine-dipeptide'
    input_top = os.path.join(input_dir, "topol.top")
    input_mdp = os.path.join(input_dir, "grompp.mdp")
    input_files={'-f': input_mdp, '-p': input_top, '-c': input_gro,},
    tpr = "run.tpr"
    output_files={'-o': tpr}
    grompp = gmx.commandline_operation(gmx.commandline.cli_executable(), 'grompp', input_files, output_files)
    grompp.run()
    if verbose:
        print(grompp.output.stderr.result())
    assert os.path.exists(grompp.output.file['-o'].result())
    return grompp.output.file['-o'].result()
    
@rp.pythontask
def run_mdrun(tpr_path, verbose: bool = False):
    import os
    import gmxapi as gmx
    if not os.path.exists(tpr_path):
        raise FileNotFoundError("You must supply a tpr file")

    input_files={'-s': tpr_path}
    output_files={'-x':'alanine-dipeptide.xtc', '-c': 'result.gro'}
    md = gmx.commandline_operation(gmx.commandline.cli_executable(), 'mdrun', input_files, output_files)
    md.run()
    if verbose:
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

def get_grompp_tasks(gro_paths):
    tds = list()
    for gro in gro_paths:
        td = rp.TaskDescription({'mode': rp.TASK_FUNCTION,
                                 'function': run_grompp(gro),})
        tds.append(td)
    return tds

def get_mdrun_tasks(tpr_paths: list[str]):
    tds = list()
    for tpr in tpr_paths:
        td = rp.TaskDescription({'mode': rp.TASK_FUNCTION,
                                 'function': run_mdrun(tpr),})
        tds.append(td)
    return tds

def get_uids_from_tasks(tasks):
    return [task.uid for task in tasks]

def get_rets_from_tasks(tasks):
    return [task.return_value for task in tasks]

def print_ret(tasks, verbose: bool = False):
    for task in tasks:
        print(f"id: {task.uid}\nret: {task.return_value}\n")
        if verbose:
            print(f"out: {task.stdout}")

max_cycles=2
replicates=2
input_dir='/home/joe/experiments/radical/alanine-dipeptide'
prev_step = [os.path.join(input_dir, "equil3.gro") for i in range(replicates)]
for cycle in range(max_cycles):
    this_step = prev_step
    print(f"step {cycle} has {this_step}")
    
    grompp_tasks_list = get_grompp_tasks(this_step)
    grompp_tasks = raptor.submit_tasks(grompp_tasks_list)
    #import ipdb;ipdb.set_trace()
    task_mgr.wait_tasks(get_uids_from_tasks(grompp_tasks))
    print_ret(grompp_tasks)

    mdrun_tasks_list = get_mdrun_tasks(get_rets_from_tasks(grompp_tasks))
    mdrun_tasks = raptor.submit_tasks(mdrun_tasks_list)
    task_mgr.wait_tasks(get_uids_from_tasks(mdrun_tasks))
    print_ret(mdrun_tasks)
    prev_step=get_rets_from_tasks(mdrun_tasks)
    #import ipdb;ipdb.set_trace()
        

client_sandbox = ru.Url(pilot.client_sandbox).path + '/' + session.uid
pilot_sandbox  = ru.Url(pilot.pilot_sandbox).path

print(f'client sandbox: {client_sandbox}')
print(f'pilot  sandbox: {pilot_sandbox}')

report.header('finalize')
session.close()

