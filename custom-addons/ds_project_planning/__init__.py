# -*- coding: utf-8 -*-

from . import models

from odoo import api, SUPERUSER_ID


def dhx_uninstall_hook(cr, registry):
    """
    This uninstall-hook will remove dhx_gantt from the action.
    """
    env = api.Environment(cr, SUPERUSER_ID, dict())

    # task_action_id = env.ref("ds_project_planning.open_planning_task_all_on_gantt")
    # task_action_id.view_mode = 'kanban,tree,form'