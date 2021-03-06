
from xml.dom import minidom

import shared
import templates
import classes
import c
import collections
import sys

from event import *
from actions import *

StreamonLogo = """
   _____ _                  __  __  ____  _   _
  / ____| |                |  \/  |/ __ \| \ | |
 | (___ | |_ _ __ ___  __ _| \  / | |  | |  \| |
  \___ \| __| '__/ _ \/ _` | |\/| | |  | | . ` |
  ____) | |_| | |  __/ (_| | |  | | |__| | |\  |
 |_____/ \__|_|  \___|\__,_|_|  |_|\____/|_| \_|
"""

print StreamonLogo
print ""

queue_num = 6
core_num = 1
sourceType="pcap"

if sourceType=="pcap":
    core_num=1;

#queues numeber for core
qpb = queue_num/core_num

if queue_num%core_num!=0:
    print "Queues distribution is not uniform"
    quit()

if len(sys.argv) < 2:
    print "No config file defined."
    quit()


print "[LOADING]", sys.argv[1], "of", sys.argv[2], "..."

try:
    Config = minidom.parse(sys.argv[1])
except IOError as e:
    print e
    quit(-1)

Source = Config.getElementsByTagName('source')[0]
Publisher = Config.getElementsByTagName('publisher')[0]
Blocks = Config.getElementsByTagName('additional_block')
Metrics = Config.getElementsByTagName('metric')
Tables = Config.getElementsByTagName('table')
Features = Config.getElementsByTagName('feature')
Events = Config.getElementsByTagName('event')
ProbeID = sys.argv[2]

TemplateVars = dict()

MonstreamLibRows = [templates.BotstreamLibHeader]

TableLibRows = [templates.TableLibHeader]

EventNameArray = []

print"[THREAD_POOLS]"

tpl=[templates.ThreadPoolTemplate.format(i) for i in range(core_num)]#thread Pool List



print "[METRICS]"

MetricConnections = []
LastMetricName = ""
MetricHardware = []
#MetricObjects = []
MetricBlocks= []
for Index, Metric in enumerate(Metrics):

    m = classes.Metric(Metric)

    for i in range(core_num):

        if m.source == 'hw':

            entry = "<entry hid='{0}' sid='{1}' />".format(m.hw_id, m.metric_id)

            MetricHardware.append(entry)

            print entry
        else:

            shared.metrics[m.name] = Index

            MetricConnText = templates.ConnectionTemplate.format(LastMetricName+str(i),"out_Metric_Block", m.name+str(i),"in_Metric_Block")

            #m.name=m.name+i

            m.values['name'] = m.name+str(i)

            #m.name=m.name+"1"

            #print m.values['name']

            MetricConnections.append( MetricConnText )

            #MetricObjects.append(m)

            MetricBlocks.append(str(m))
    LastMetricName = m.name

#Connection LastMetricBlock to FeatureBlock
for i in range(core_num):
    MetricConnText = templates.ConnectionTemplate.format(LastMetricName+str(i),"out_Metric_Block", "FeatureBlock"+str(i),"in_FeatureBlock")
    MetricConnections.append( MetricConnText )


print "[SOURCE]"
sniffer_list=[]
TemplatePcapVars=dict()

if sourceType=="pfq":
    sniffer_list=[templates.SnifferTemplate.format(j,"".join([ """<queue number="{0}"/>""".format(i) for i in range(qpb*j,(j+1)*qpb) ])) for j in range(core_num)]
else:
    Source.type = Source.getAttribute('type')
    Source.name = Source.getAttribute('name')
    TemplatePcapVars["source_type"] = Source.type
    TemplatePcapVars["source_name"] = Source.name
    TemplatePcapVars["hw_metrics"] = "\n".join(MetricHardware)
    sniffer_list=templates.SnifferPcapTemplate.format(**TemplatePcapVars)

print "[PUBLISHER]"
Exporters_list = []
TemplateExporter = dict()
TemplateExporter["protocol"] = Publisher.getAttribute('protocol')
TemplateExporter["ip"] = Publisher.getAttribute('ip')
TemplateExporter["port"] = Publisher.getAttribute('port')
Exporters_list = templates.ExporterBlockTemplate.format(**TemplateExporter)
#print Publisher.protocol, Publisher.ip, Publisher.port


#MetricBlocks = [ str(x) for x in MetricObjects ]



PrimaryKeyBlock = []

for Index, Table in enumerate(Tables):

    t = shared.Table(Table)

    PrimaryKeyBlock.append( str(t) )

    # MonstreamLibRows.append( t.get_code() ) DEPRECATED

TableLibRows.append(shared.Table.declaration())
TableLibRows.append(shared.Table.reset_codes())



print "[FEATURES]"

for Index, Feature in enumerate(Features):

    f = c.Feature(Feature, classes.Metric.Table)

    shared.features[f.name] = Index

    MonstreamLibRows.append( str(f) )

#MonstreamLibRows.append(templates.FeatureListTemplate.format(", \n\t".join( x[0] for x in c.Feature.Table), StateName))


print "[STATES]"

StatesTable = collections.OrderedDict() # dict()

States = Config.getElementsByTagName('statedef')

state_count = 0

# StatesList = []

#code = '''std::map<std::string, std::string> m = {{0}};'''
for State in States:
    StateName = State.getAttribute('id')
    StateExpire = State.getAttribute('timeout')
    StateOnTimeout = State.getAttribute('next_state')

    if not StateExpire:
        StateExpire = 0
    else:
        StateExpire = int(StateExpire)*1000000

    if not StateOnTimeout:
        StateOnTimeout = 0

    if StateName not in StatesTable:
        StatesTable[ StateName ] = (state_count, StateExpire, StateOnTimeout)
        state_count += 1
#MonstreamLibRows.append(','.join(code))

StatesTable[""] = (-1, 0, 0)


print "[ADDITIONAL BLOCKS]"

AdditionalBlocks = []
AdditionalConnections = []

LastBlockName = "FilteringBlock0"
LastGateName = "out_FilteringBlock"

_attacks_num = 0

for Block in Blocks:
    name = Block.getAttribute('name')

    params = ""

    if name == "Forwarder":
        sock  = Block.getElementsByTagName("socket")

        if not sock:
            raise Exception("FORWARDER: socket must be specified.")

        feeds = Block.getElementsByTagName("feed")

        export_to_int = { "always":"0", "on_suspect":"1" }

        sock_path = sock[0].getAttribute("path")

        if not sock_path:
            raise Exception("FORWARDER: need url in socket!")

        params += "<socket path=\"{0}\" />".format(sock_path)

        for f in feeds:
            atype = f.getAttribute("atype")

            if atype not in shared.attacks:
                shared.attacks[atype] = _attacks_num
                _attacks_num += 1

            name_id = shared.tokens[ f.getAttribute("name") ]

            content_s = f.getAttribute("content")

            content_attr_name = None

            if content_s in shared.tokens:
                content_id = shared.tokens[ f.getAttribute("content") ]
                content_attr_name = "content"
            elif content_s in shared.metrics:
                content_id = shared.metrics[ f.getAttribute("content") ]
                content_attr_name = "metric"

            export = f.getAttribute("export")

            f.setAttribute("name", str(name_id) )
            f.setAttribute(content_attr_name, str(content_id) )
            f.setAttribute("export", export_to_int[export] )

            params += f.toxml() + "\n"

        print params
        print shared.attacks

    print "[BLOCK] ", name


    AdditionalBlocks.append("""<block id="{0}" type="{0}">
                                  <params>
                                    {1}
	                          </params>
	                       </block>""".format(name, params) )

    AdditionalConnections.append("""<connection src_block="{0}"
                                                src_gate="{1}"
                                                dst_block="{2}"
                                                dst_gate="in_gate" />""".format(LastBlockName, LastGateName, name) )

    LastBlockName = name
    LastGateName = "out_gate"


print "[TIMEOUTS]"

c.Timeout.fill_from_events(Events)

print "[EVENTS]"


for Ev in Events:

    # e = classes.Event(Ev)

    e = Event.parse(Ev)

    MonstreamLibRows.append( "/*### START EVENT_ID {0} ###*/\n".format( Event.last() ) )

    # PrimaryKeyBlock.append( str(e) )

    LocalStates = dict()

    # WARNING: THIS NEED MORE CHECKS!!!

    code = []
    level = []
    description =[]
    if Ev.getAttribute('type') == 'packet':
	    MonstreamLibRows.append( '''std::string getStateCode(const struct pptags* Tags);\n''')
	    MonstreamLibRows.append( '''std::string getStateLevel(const struct pptags* Tags);\n''')
	    MonstreamLibRows.append( '''std::string getStateDescription(const struct pptags* Tags);\n''')
	    mapp = "std::map<std::string,std::string> {0} = {{{1}}};\n"
    for s in Ev.getElementsByTagName('state'):
        LocalStates[ s.getAttribute('id') ] = s

    #LocalStates = set( [ s.getAttribute('id') for s in Ev.getElementsByTagName('state') ] )

    StateArray = []

    for StateName, StateData in StatesTable.iteritems():

        StateId, Timeout, StateOnTimeout = StateData

        # Timeout = StateData[1]

        if StateOnTimeout not in StatesTable:
            StateOnTimeout = 0
        else:
            StateOnTimeout = StatesTable[StateOnTimeout][0]


        if StateName in LocalStates:
            State = LocalStates[StateName]
    	    if Ev.getAttribute('type') == 'packet':
		    StateCode = State.getAttribute('code')
		    StateLevel = State.getAttribute('level')
		    StateDescription = State.getAttribute('description')

		    code.append("{{\"{0}\",\"{1}\"}}".format(StateId, StateCode))
		    level.append("{{\"{0}\",\"{1}\"}}".format(StateId, StateLevel))
		    description.append("{{\"{0}\",\"{1}\"}}".format(StateId, StateDescription))

            classes.MetricOp.reset()
            c.Condition.reset()

            RandToken = shared.GetRandomString()

            #print "Timeout => ", Timeout

            MetricOps = State.getElementsByTagName("use-metric")

            for mop in MetricOps:
                m = classes.MetricOp(mop, classes.Metric.D)


            MonstreamLibRows.append( classes.MetricOp.getCode(RandToken) )


            #print "   -> condition"

            Conditions = State.getElementsByTagName("condition")

            for Index, Condition in enumerate(Conditions):
                cc = c.Condition(Condition, c.Feature.Table, StatesTable)

                MonstreamLibRows.extend( cc.actions() )

                # generate names
                # add code to lib rows

            # CREATE Post Condition ActionList

            PostActionNodes = State.getElementsByTagName("post-condition-action")

            if PostActionNodes:
                PostActionNode = PostActionNodes[0]

                PostTimeout = PostActionNode.getElementsByTagName("timeout_set")
                PostActionStr = PostActionNode.getAttribute("do")

                for Arg, Index in c.Feature.Table:
                    if Arg in PostActionStr:
                        c.Condition.FeatureSet.append("{{ {0}, {1} }}".format(Index, Arg))

                pnames, pbodies = Actions.parse(PostActionStr)
                tnames, tbodies = c.Timeout.parse_all(PostTimeout)

                ActionStr, pdecl = Actions.generate(pnames+tnames)

                MonstreamLibRows.extend(pbodies+tbodies)
                MonstreamLibRows.append(pdecl)
            else:
                ActionStr = "NULL"


            LocalFeatureList = c.Condition.get_features_code(RandToken)

            MonstreamLibRows.append( LocalFeatureList )

            MonstreamLibRows.append( c.Condition.get_condition_code(RandToken) )


            # construct state tuple
            # in format { feature, condition, action }
            if LocalFeatureList:
                FeatureListName = "FeatureList_{0}".format(RandToken)
            else:
                FeatureListName = "NULL"

            ConditionListName = "ConditionList_{0}".format(RandToken)

            StateArray.append( "{{ {0}, {1}, {2}, {3}, {4}, {5}, {6} }}".format( StateId,
                                                                            classes.MetricOp.LastGenerated,
                                                                            FeatureListName,
                                                                            ConditionListName,
                                                                            ActionStr,
                                                                            Timeout,
                                                                            StateOnTimeout) )

        else:
            StateArray.append( "{{ {0}, NULL, NULL, NULL, NULL, 0, 0 }}".format(StateId) )


    if Ev.getAttribute('type') == 'packet':
	    MonstreamLibRows.append( mapp.format('code_map', ",".join(code)))
	    MonstreamLibRows.append( mapp.format('level_map', ",".join(level)))
	    MonstreamLibRows.append( mapp.format('description_map', ",".join(description)))

	    getStateFunc = \
	'''std::string {0}(const struct pptags* Tags)
	{{
	    return {1}[std::to_string(Tags->State->Id)];
	}}\n'''

	    MonstreamLibRows.append( getStateFunc.format('getStateCode', 'code_map'))
	    MonstreamLibRows.append( getStateFunc.format('getStateLevel', 'level_map'))
	    MonstreamLibRows.append( getStateFunc.format('getStateDescription', 'description_map'))

    MonstreamLibRows.append( templates.StatusTemplate.format(Event.last(), ", \n\t".join(StateArray)) )

    EventNameArray.append(e)  # EventName)

    MonstreamLibRows.append( "/*### END EVENT_ID {0} ###*/\n".format( Event.last() ) )

# REPLACE WITH event Events array of structs
#MonstreamLibRows.append( "state_tuple* Events[] = {{ {0} }};\n".format(", ".join(EventNameArray) ) )

PrimaryKeyBlock.append( shared.tokens.getAdditionalXml() )

MonstreamLibRows.append( templates.EventTemplate.format( ",\n\t".join( EventNameArray ) ) )

MonstreamLibRows.append( templates.BotstreamLibFooter )


#MonstreamLibRows.append(templates.FeatureByStatus.format(", \n\t".join(FeaturesArray)))
#MonstreamLibRows.append(templates.ConditionByStatus.format(", \n\t".join(ConditionArray)))

# generate template vars

print "[WRITE] app config"

#Generation core_num EventFactory Blocks
EventFactoryVars = dict()
EventFactoryVars["timeout_classes"] = len(shared.timeouts)
EventFactoryVars["Fields"] = shared.tokens.toxml()
EventFactoryVars["KeyRules"] = "".join(PrimaryKeyBlock)
EventFactory=[]
for k in range (core_num):
    EventFactoryVars["id"]=k
    EventFactory.append(templates.EventFactoryTemplate.format(**EventFactoryVars))

#Generation core_num FeatureBlocks
FeatureBlocks_list=[]
for k in range (core_num):
    FeatureBlocks_list.append(templates.FeatureBlockTemplate.format(k))


#Generation core_num FilteringBlocks
FilteringBlocks_list=[]
for k in range (core_num):
    FilteringBlocks_list.append(templates.FilteringBlockTemplate.format(k))

#Generation core_num Exporters
# Exporters_list=[]
# for k in range (core_num):
#     Exporters_list.append(templates.ExporterBlockTemplate.format(k))

#Connection Sniffer-EventFactory
ConnectionList=[]
for i in range(core_num):
    ConnectionList.append(templates.ConnectionTemplate.format("Sniffer"+str(i),"sniffer_out","Factory"+str(i),"in_Factory"))

#Connection EventFactory-firstMetric
for i in range(core_num):
    ConnectionList.append(templates.ConnectionTemplate.format("Factory"+str(i),"out_Factory",Metrics[0].getAttribute('name')+str(i),"in_Metric_Block"))

#Connection Feature-Filtering
ConnectionListFeatureFiltering=[]
for i in range(core_num):
    ConnectionListFeatureFiltering.append(templates.ConnectionTemplate.format("FeatureBlock"+str(i),"out_FeatureBlock","FilteringBlock"+str(i),"in_FilteringBlock"))

#Connection Filtering-Exporter
ConnectionListFilteringExporter=[]
for i in range(core_num):
    ConnectionListFilteringExporter.append(templates.ConnectionTemplate.format("FilteringBlock"+str(i),"out_FilteringBlock","ExporterBlock"+str(i),"in_gate"))

TemplateVars["appname"] = "botstream"
TemplateVars["probe_id"] = ProbeID
#TemplateVars["source_type"] = Source.type
#TemplateVars["source_name"] = Source.name
#TemplateVars["hw_metrics"] = "\n".join(MetricHardware)
TemplateVars["MetricBlock"] = "".join(MetricBlocks)
TemplateVars["AdditionalBlocks"] = "\n".join(AdditionalBlocks)
#TemplateVars["first_metric_name"] = Metrics[0].getAttribute('name')
TemplateVars["MetricConnections"] = "".join(MetricConnections[i] for i in xrange(core_num, len(MetricConnections)))
#TemplateVars["last_metric_name"] = LastMetricName
TemplateVars["filter_string"] = "" #" or ".join(FilterList)
TemplateVars["AdditionalConnections"] = "\n".join(AdditionalConnections)
TemplateVars["ThreadPools"] = "".join(tpl)
TemplateVars["Sniffers"] = "".join(sniffer_list)
TemplateVars["Events"]="\n".join(EventFactory)
TemplateVars["Feature"]="\n".join(FeatureBlocks_list)
TemplateVars["Filtering"]="\n".join(FilteringBlocks_list)
TemplateVars["Exporter"]=Exporters_list
TemplateVars["SnifferFactoryConnections"]="".join(ConnectionList)
TemplateVars["FeatureFilteringConnections"]="".join(ConnectionListFeatureFiltering)
TemplateVars["FilteringExporterConnections"]="".join(ConnectionListFilteringExporter)


# open Template and do XML output

with open('template.xml') as TemplateFile:
    TemplateTxt = "".join(TemplateFile.readlines())

    with open('{0}.xml'.format(TemplateVars["appname"]), 'w') as BlockmonFile:
        BlockmonFile.write(TemplateTxt.format(**TemplateVars))

print "[WRITE] table-include"
with open('tables.hpp', 'w') as TableFile:
    TableFile.writelines(TableLibRows)


print "[WRITE] monstream-lib"

with open('featurelib.cpp', 'w') as LibFile:
    LibFile.writelines(MonstreamLibRows)

#print "Done"
