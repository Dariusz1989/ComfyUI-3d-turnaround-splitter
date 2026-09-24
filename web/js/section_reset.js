/**
 * Section reset buttons - Geekatplay 3D Multiview
 *
 * Any node (plain or subgraph) whose properties carry `resetSections` gets one
 * "reset" button per section plus "reset all". A section is a list of widget
 * names with the value each goes back to:
 *
 *   properties.resetSections = {
 *     "1 VOXEL": { "structure_seed": 56, "structure_steps": 12 },
 *     ...
 *   }
 *
 * The defaults travel inside the workflow file, so nothing here knows about any
 * particular node. The buttons are not serialized: widgets_values is positional,
 * and an extra saved entry would shift every value after it on reload.
 */
import { app } from "../../../scripts/app.js";

const BUTTON_PREFIX = "↺ reset ";

function findWidget(node, name) {
    const direct = node.widgets?.find((w) => w.name === name);
    if (direct) return direct;
    // A promoted subgraph widget may carry a different widget name than its input.
    const input = node.inputs?.find((i) => i.name === name);
    const widgetName = input?.widget?.name;
    return widgetName ? node.widgets?.find((w) => w.name === widgetName) : undefined;
}

function applyValues(node, values) {
    let changed = 0;
    for (const [name, value] of Object.entries(values)) {
        const widget = findWidget(node, name);
        if (!widget) {
            console.warn(`[Geekatplay] reset: no widget named ${name} on node ${node.id}`);
            continue;
        }
        if (widget.value !== value) {
            widget.value = value;
            widget.callback?.(value);
            changed += 1;
        }
    }
    node.setDirtyCanvas?.(true, true);
    return changed;
}

function addResetButtons(node) {
    const sections = node.properties?.resetSections;
    if (!sections || typeof sections !== "object") return;
    if (node.widgets?.some((w) => w.name?.startsWith(BUTTON_PREFIX))) return;

    const addButton = (label, values) => {
        const button = node.addWidget("button", BUTTON_PREFIX + label, null, () => applyValues(node, values));
        button.serialize = false;
        return button;
    };

    const all = {};
    for (const [label, values] of Object.entries(sections)) {
        Object.assign(all, values);
        addButton(label, values);
    }
    addButton("ALL", all);
    node.setSize?.([node.size[0], Math.max(node.size[1], node.computeSize?.()[1] ?? 0)]);
}

app.registerExtension({
    name: "Geekatplay.SectionReset",

    async nodeCreated(node) {
        // properties arrive with configure(), which runs after nodeCreated for a loaded graph.
        const original = node.onConfigure;
        node.onConfigure = function () {
            const result = original?.apply(this, arguments);
            setTimeout(() => addResetButtons(this), 0);
            return result;
        };
        setTimeout(() => addResetButtons(node), 0);
    },
});
