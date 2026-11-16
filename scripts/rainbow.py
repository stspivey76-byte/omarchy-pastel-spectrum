"""Small opt-in patch for compatible Omarchy replacement bar loaders."""
import json
PALETTE=['#ed70df','#efd2aa','#91c69b','#80b8eb','#b8acd5']
def patch(source,layout):
    if 'function pastelIconColor(' in source:
        return source
    required=['  function publicLayoutConfig() {','      id: componentLoader\n','      id: registryLoader\n','      id: qmlLoader\n']
    if not all(x in source for x in required):
        raise ValueError('This bar version is not compatible with the rainbow patch; theme colors still work.')
    ids=[x['id'] for region in ['left','center','right'] for x in layout.get(region,[]) if 'id' in x]
    colors={name:PALETTE[i%len(PALETTE)] for i,name in enumerate(ids)}
    source=source.replace('import QtQuick\n','import QtQuick\nimport QtQuick.Effects\n',1)
    source=source.replace(required[0],'  function pastelIconColor(moduleName) {\n    var colors = '+json.dumps(colors)+'\n    return colors[moduleName] || "#80b8eb"\n  }\n\n'+required[0],1)
    for marker in required[1:]:
        source=source.replace(marker,marker+'      layer.enabled: ["steven.workspaces", "steven.spectrum", "steven.resources"].indexOf(slot.moduleName) < 0\n      layer.effect: MultiEffect {\n        colorization: 1.0\n        colorizationColor: root.pastelIconColor(slot.moduleName)\n      }\n',1)
    return source
