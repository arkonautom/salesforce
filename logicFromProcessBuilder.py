#Nikita arkonautom@gmail.com Apr 25, 2023
#import os
#os.system("cls")

import sys
print(sys.argv)

def nope(message):
    print(f"nope ({message})")
    #exit()

if len(sys.argv) <= 1:
    nope('no filename specified')
    filename = 'NO_Case_Process_Builder.flow-meta.xml'
else:
    filename = sys.argv[1]
print(f'{filename}\n')

import xml.etree.ElementTree as ET
tree = ET.parse('force-app/main/default/flows/' + filename)
root = tree.getroot()

ns = {'sf': 'http://soap.sforce.com/2006/04/metadata'}
debug = False
TYPE_ACTION = '{http://soap.sforce.com/2006/04/metadata}actionCalls'
TYPE_ASSIGN = '{http://soap.sforce.com/2006/04/metadata}assignments'
TYPE_DECISION = '{http://soap.sforce.com/2006/04/metadata}decisions'
TYPE_UPDATE = '{http://soap.sforce.com/2006/04/metadata}recordUpdates'
TYPE_SCHEDULE = '{http://soap.sforce.com/2006/04/metadata}waits'
PAD = '----'
TAB = '    '

decisions = []
#decisionsMetPrev = {}
for decision in root.findall('sf:decisions', ns):
    if (decision.find('sf:processMetadataValues', ns)):
        index = int(float(decision.find('sf:processMetadataValues/sf:value/sf:numberValue', ns).text))
        decisions.append((index, decision))
    # elif (decision.find('sf:label', ns).text == 'Previously Met Decision'):
    #     decisionsMetPrev[decision.find('sf:name', ns).text] = decision
decisions.sort(key=lambda el: el[0])
#print(decisionsMetPrev)

# actionCalls = {}
# for action in root.findall('sf:actionCalls', ns):
#     actionCalls[action.find('sf:name', ns).text] = action
# #print(actionCalls)

def handleAction(action, level):
    #label = action.find('sf:label', ns).text
    actionName = action.find('sf:actionName', ns).text
    actionType = action.find('sf:actionType', ns).text
    if (actionName != 'chatterPost' and actionType != 'chatterPost'):
        print(f"{PAD*level}{actionType}\t{actionName}")
    else:
        textPath = 'sf:inputParameters[sf:name = \'text\']/sf:value/sf:stringValue'
        text = action.find(textPath, ns).text
        print(f"{PAD*level}chatterPost\t'{text}'")
    
    for param in action.findall('sf:inputParameters[sf:processMetadataValues]', ns):
        toRefPath = 'sf:processMetadataValues[sf:name = \'leftHandSideLabel\']/sf:value/sf:stringValue'
        toRef = param.find(toRefPath, ns)
        fromTypePath = 'sf:processMetadataValues[sf:name = \'rightHandSideType\']/sf:value/sf:stringValue'
        fromType = param.find(fromTypePath, ns)
        field = param.find('sf:name', ns)
        value = param.find('sf:value/*[1]', ns)
        print(f"{PAD*level}#{toRef.text}.{field.text} = {fromType.text}.{value.text if value is not None else '(empty string)'}")
    
    nextTarget = action.find('sf:connector/sf:targetReference', ns)
    print(f"{PAD*level}next ({'STOP' if nextTarget is None else nextTarget.text})")
    if (nextTarget is not None):
        handleTarget(nextTarget.text, level + 1)

def handleAssign(assign, level):
    #label = assign.find('sf:label', ns).text
    operator = assign.find('sf:assignmentItems/sf:operator', ns)
    value = assign.find('sf:assignmentItems/sf:value/*[1]', ns)
    print(f"{PAD*level}assign {operator.text} {value.text}")
    
    #RecursionError: maximum recursion depth exceeded
    # nextTarget = assign.find('sf:connector/sf:targetReference', ns)
    # print(f"{PAD*level}next ({'STOP' if nextTarget is None else nextTarget.text})")
    # if (nextTarget is not None):
    #     handleTarget(nextTarget.text, level + 1)

def handleDecision(decision, level):
    # label = decision.find('sf:label', ns).text
    name = decision.find('sf:name', ns).text
    # nextDecision = decision.find('sf:defaultConnector/sf:targetReference', ns)
    # defaultConnectorLabel = decision.find('sf:defaultConnectorLabel', ns).text
    print(f"{PAD*(level - 1)}({name})")
    rules = decision.findall('sf:rules', ns)
    handleRules(rules, level)
    print(f"{PAD*(level)}else (continue)")

def handleRules(rules, level):
    for rule in rules:
        ruleLabel = rule.find('sf:label', ns).text
        #ruleName = rule.find('sf:name', ns).text
        print(f"{PAD*(level - 1)}{index + 1}:{ruleLabel}")
        conditionLogic = rule.find('sf:conditionLogic', ns).text
        conditions = rule.findall('sf:conditions', ns)
        print(f"{PAD*level}if({len(conditions)}) {conditionLogic}")
        
        for i, condition in enumerate(conditions):
            leftValueReference = condition.find('sf:leftValueReference', ns)
            operator = condition.find('sf:operator', ns)
            rightValue = condition.find('sf:rightValue/*[1]', ns)
            rightValueText = rightValue.text if rightValue is not None else '(empty string)'
            if (conditionLogic != 'and' and conditionLogic != 'or'):
                toRefPath = 'sf:processMetadataValues[sf:name = \'leftHandSideLabel\']/sf:value/sf:stringValue'
                toRef = condition.find(toRefPath, ns)
                if (toRef is not None):
                    leftValueReference.text = toRef.text + '.' + leftValueReference.text
                fromTypePath = 'sf:processMetadataValues[sf:name = \'rightHandSideType\']/sf:value/sf:stringValue'
                fromType = condition.find(fromTypePath, ns)
                if (fromType is not None):
                    rightValueText = fromType.text + '.' + rightValueText
            if (leftValueReference.text.startswith('formula')):
                leftValueReference.text = 'Formula.' + handleFormula(leftValueReference.text, level)
            print(f"{PAD*level} {i + 1}.{leftValueReference.text} \t{operator.text} \t{rightValueText}")
        
        nextTarget = rule.find('sf:connector/sf:targetReference', ns)
        print(f"{PAD*level}then ({'STOP' if nextTarget is None else nextTarget.text})")
        if (nextTarget is not None):
            handleTarget(nextTarget.text, level + 1)

def handleFormula(name, level):
    path = 'sf:formulas[sf:name = \'' + name + '\']'
    formula = root.find(path, ns)
    #expression = formula.find('sf:expression', ns)
    expressionPath = 'sf:processMetadataValues[sf:name = \'originalFormula\']/sf:value/sf:stringValue'
    expression = formula.find(expressionPath, ns)
    text = '~' + expression.text.strip().replace('\n\n\n', '\n').replace('\n\n', '\n').replace('\n', '\n' + TAB*(level + 3)) + '~(' + name + ')'
    return text

def handleUpdate(update, level):
    label = update.find('sf:label', ns).text
    print(f"{PAD*level}{label}")
    for assign in update.findall('sf:inputAssignments', ns):
        toRefPath = 'sf:processMetadataValues[sf:name = \'leftHandSideReferenceTo\']/sf:value/sf:stringValue'
        toRef = assign.find(toRefPath, ns)
        fromTypePath = 'sf:processMetadataValues[sf:name = \'rightHandSideType\']/sf:value/sf:stringValue'
        fromType = assign.find(fromTypePath, ns)
        field = assign.find('sf:field', ns)
        value = assign.find('sf:value/*[1]', ns)
        if (value is not None and value.text.startswith('formula')):
            value.text = handleFormula(value.text, level)
        print(f"{PAD*level}#{toRef.text}.{field.text} = {fromType.text}.{value.text if value is not None else '(empty string)'}")
        
    nextTarget = update.find('sf:connector/sf:targetReference', ns)
    print(f"{PAD*level}next ({'STOP' if nextTarget is None else nextTarget.text})")
    if (nextTarget is not None):
        handleTarget(nextTarget.text, level + 1)

def handleSchedule(schedule, level):
    label = schedule.find('sf:label', ns).text
    print(f"{PAD*level}{label}")
    
    for wait in schedule.findall('sf:waitEvents', ns):
        offsetPath = 'sf:inputParameters[sf:name = \'TimeOffset\']/sf:value/sf:numberValue'
        offset = wait.find(offsetPath, ns)
        offsetUnitPath = 'sf:inputParameters[sf:name = \'TimeOffsetUnit\']/sf:value/sf:stringValue'
        offsetUnit = wait.find(offsetUnitPath, ns)
        print(f"{PAD*level}{offset.text} {offsetUnit.text}")
        
        nextTarget = wait.find('sf:connector/sf:targetReference', ns)
        print(f"{PAD*level}next ({'STOP' if nextTarget is None else nextTarget.text})")
        if (nextTarget is not None):
            handleTarget(nextTarget.text, level + 1)

def handleTarget(name, level):
    path = 'sf:*[sf:name = \'' + name + '\']'
    target = root.find(path, ns)
    #print(f"{PAD*level}\t{target.tag}")
    if (target.tag == TYPE_ACTION):
        handleAction(target, level)
    elif (target.tag == TYPE_ASSIGN):
        handleAssign(target, level)
    elif (target.tag == TYPE_DECISION):
        if (target.find('sf:processMetadataValues', ns) is None):
            if (target.find('sf:label', ns).text == 'Previously Met Decision'):
                name = target.find('sf:rules', ns).find('sf:connector/sf:targetReference', ns).text
                print(f"{PAD*level}(when met) transit to {name}")
                handleTarget(name, level)
            else:
                handleDecision(target, level)
    elif (target.tag == TYPE_UPDATE):
        handleUpdate(target, level)
    elif (target.tag == TYPE_SCHEDULE):
        handleSchedule(target, level)
    else:
        print(f'WARN other type {name}|{target.tag}')

level = 1
for index, decision in decisions:
    handleDecision(decision, level)
    print("")
