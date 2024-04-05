import os

# do not use animated output in notebooks
os.environ['RADICAL_REPORT_ANIME'] = 'False'

import radical.pilot as rp
import radical.utils as ru

# determine the path of the currently active ve to simplify some examples below
ve_path = os.path.dirname(os.path.dirname(ru.which('python3')))

# create session and managers
session = rp.Session()
pmgr    = rp.PilotManager(session)
tmgr    = rp.TaskManager(session)

# submit a pilot
pilot = pmgr.submit_pilots(rp.PilotDescription({'resource'     : 'local.localhost',
                                                'runtime'      : 60,
                                                'cores'        : 8,
                                                'exit_on_error': False}))

# add the pilot to the task manager and wait for the pilot to become active
tmgr.add_pilots(pilot)
pilot.wait(rp.PMGR_ACTIVE)
print('pilot is up and running')

master_descr = {'mode'     : rp.RAPTOR_MASTER,
                'named_env': 'rp'}
worker_descr = {'mode'     : rp.RAPTOR_WORKER,
                'named_env': 'rp'}

raptor  = pilot.submit_raptors( [rp.TaskDescription(master_descr)])[0]
workers = raptor.submit_workers([rp.TaskDescription(worker_descr),
                                 rp.TaskDescription(worker_descr)])
@rp.pythontask
def msg(val: int):
    if(val %2 == 0):
        print("Regular message")
    else:
        print(f"This is a very odd message: {val}")

# create a minimal executable task
td   = rp.TaskDescription({'mode'     : rp.TASK_FUNCTION,
                           'function' : msg(2),
                           #'args'     : [1, 2],
                           'pre_exec': 'source /home/joe/pyenvs/scalems/bin/activate'})
task = raptor.submit_tasks([td])[0]

print(task)
tmgr.wait_tasks([task.uid])
print('id: %s [%s]:\n    out:\n%s\n    ret: %s\n'
     % (task.uid, task.state, task.stdout, task.return_value))

client_sandbox = ru.Url(pilot.client_sandbox).path + '/' + session.uid
pilot_sandbox  = ru.Url(pilot.pilot_sandbox).path

print(f'client sandbox: {client_sandbox}')
print(f'pilot  sandbox: {pilot_sandbox}')

session.close()
