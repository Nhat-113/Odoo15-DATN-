/** @odoo-module **/

import { Dialog } from "../../core/dialog/dialog";
import { browser } from "../../core/browser/browser";
import { registry } from "../../core/registry";
import { _lt } from "../../core/l10n/translation";

class ShortCutsDialog extends Dialog {}
ShortCutsDialog.bodyTemplate = "web.UserMenu.shortcutsTable";
ShortCutsDialog.title = _lt("Shortcuts");

function shortCutsItem(env) {
    return {
        type: "item",
        id: "shortcuts",
        hide: env.isSmall,
        description: env._t("Shortcuts"),
        callback: () => {
            env.services.dialog.add(ShortCutsDialog);
        },
        sequence: 30,
    };
}


export function preferencesItem(env) {
    return {
        type: "item",
        id: "settings",
        description: env._t("Preferences"),
        callback: async function () {
            const actionDescription = await env.services.orm.call("res.users", "action_get");
            actionDescription.res_id = env.services.user.userId;
            env.services.action.doAction(actionDescription);
        },
        sequence: 50,
    };
}

function logOutItem(env) {
    const route = "/web/session/logout";
    return {
        type: "item",
        id: "logout",
        description: env._t("Log out"),
        href: `${browser.location.origin}${route}`,
        callback: () => {
            browser.location.href = route;
        },
        sequence: 70,
    };
}

registry
    .category("user_menuitems")
    .add("shortcuts", shortCutsItem)
    .add("profile", preferencesItem)
    .add("log_out", logOutItem);
