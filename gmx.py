import os
import radical.pilot as rp
import radical.utils as ru

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

gromp_task = rp.TaskDescription({"executable": "python",
                                 "arguments": os.path.join(os.getcwd(), "grompp.py")})
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
task_mgr.wait_tasks()

#import ipdb;ipdb.set_trace()
for task in tasks:
    print('%s: %s' % (task.uid, task.state))

client_sandbox = ru.Url(pilot.client_sandbox).path + '/' + session.uid
pilot_sandbox  = ru.Url(pilot.pilot_sandbox).path

print('client sandbox: %s' % client_sandbox)
print('pilot  sandbox: %s' % pilot_sandbox)

report.header('finalize')
session.close(cleanup=True)
