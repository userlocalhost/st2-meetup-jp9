from orquesta import conducting
from orquesta import events
from orquesta.specs import native as native_specs
from orquesta import statuses
from orquesta.tests.unit import base as test_base
from os.path import dirname


class BasicWorkflowTest(test_base.WorkflowConductorTest):
    def get_workflow_path(self):
        return "%s/../actions/workflows" % dirname(__file__)

    def get_workflow_content(self, wf_filename):
        with open("%s/%s" % (self.get_workflow_path(), wf_filename), 'r') as fp:
            return fp.read()

    def setUp(self):
        # read content of specified workflow which is in actions/workflows directory in this pack
        self.spec = native_specs.WorkflowSpec(self.get_workflow_content('run_cmd.yaml'))

    def test_run_command_task_is_succeeded(self):
        # initialize workflow conductor
        conductor = conducting.WorkflowConductor(**{
            'spec': self.spec,
            'inputs': {
                'cmd': 'test_command',
                'host': 'test.example.com',
                'slack_channel': '#hoge'
            },
        })

        # initialize workflow status
        conductor.request_workflow_status(statuses.RUNNING)

        # get task informations to be run at first
        next_tasks = conductor.get_next_tasks()

        # This confirms whether expected action is specified
        self.assertEqual(len(next_tasks), 1)
        self.assertEqual(next_tasks[0]['id'], 'run_command')

        # When 'with' parameter is specified in action, 'actions' might have params more than 1.
        self.assertEqual(len(next_tasks[0]['actions']), 1)
        _action_info = next_tasks[0]['actions'][0]
        self.assertEqual(_action_info['action'], 'core.remote')
        self.assertEqual(_action_info['input']['cmd'], 'test_command')
        self.assertEqual(_action_info['input']['hosts'], 'test.example.com')

        # finish run_command with successful
        self.forward_task_statuses(conductor, 'run_command', [statuses.RUNNING])
        self.forward_task_statuses(conductor, 'run_command', [statuses.SUCCEEDED], **{
            'result': {
                'test.example.com': {
                    'stdout': 'test_output'
                }
            }
        })

        # get next running task after run_command is finished successfully
        next_tasks = conductor.get_next_tasks()

        # This confirms whether expected action is specified
        self.assertEqual(len(next_tasks), 1)
        self.assertEqual(next_tasks[0]['id'], 'report_result')

        self.assertEqual(len(next_tasks[0]['actions']), 1)
        _action_info = next_tasks[0]['actions'][0]
        self.assertEqual(_action_info['action'], 'slack.post_message')
        self.assertEqual(_action_info['input']['channel'], '#hoge')
        self.assertEqual(_action_info['input']['message'], (
            '===[ SUCCEEDED ]===\n'
            '* (command) "test_command" on test.example.com\n'
            '* (output) test_output\n'
        ))

        # This confirms after finishing report_result there is no task to be run
        self.forward_task_statuses(conductor, 'report_result', [statuses.RUNNING, statuses.SUCCEEDED])
        self.assertEqual(conductor.get_next_tasks(), [])

    def test_run_command_task_is_failed(self):
        # initialize workflow conductor
        conductor = conducting.WorkflowConductor(**{
            'spec': self.spec,
            'inputs': {
                'cmd': 'test_command',
                'host': 'test.example.com',
                'slack_channel': '#hoge'
            },
        })

        # initialize workflow status
        conductor.request_workflow_status(statuses.RUNNING)

        # get task informations to be run at first
        next_tasks = conductor.get_next_tasks()

        # finish run_command with failure and get next task
        self.forward_task_statuses(conductor, 'run_command', [statuses.RUNNING, statuses.FAILED])
        next_tasks = conductor.get_next_tasks()

        self.assertEqual(len(next_tasks), 1)
        self.assertEqual(next_tasks[0]['id'], 'report_error')

        self.assertEqual(len(next_tasks[0]['actions']), 1)
        _action_info = next_tasks[0]['actions'][0]
        self.assertEqual(_action_info['action'], 'slack.post_message')
        self.assertEqual(_action_info['input']['channel'], '#hoge')
        self.assertEqual(_action_info['input']['message'], (
            '===[   ERROR   ]===\n'
            'run_command task was failed to run command '
            '("test_command") on test.example.com\n'
        ))
