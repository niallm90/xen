import urllib2, hashlib, re, datetime, lxml.etree as ET

class Channel():
    def __init__(self, id, name):
        self.id = id
        self.name = name

class Program():
    def __init__(self, id, channel, title, 
                 start, stop, description = None):
        self.id = id
        self.channel = channel
        self.title = title
        self.start = start
        self.stop = stop
        self.description = description

class Xml():
    channels = []
    programs = []
    def __init__(self, url):        
        self.opener = urllib2.build_opener()
        self.opener.addheaders = [('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')]
        
        tree = ET.parse(self.opener.open("http://www.freeviewnz.tv/localservices/opg/schedule/"))
        self.root = tree.getroot()

    def parse(self):
        if len(self.channels) + len(self.programs) == 0:
            for url in self.root.findall('Index/UrlDate/Url'):
                root = ET.parse(self.opener.open("http://www.freeviewnz.tv/" + url.text))

                for opgChannelItem in root.findall('Channels/OpgChannelItem'):
                    channel = opgChannelItem.find('Channel')
                    name = channel.attrib['Name']
                    id = name.lower().replace(" ", "-") + ".freeviewnz.tv"

                    channel = Channel(id=id, name=name)
                    self.channels.append(channel)

                    for program in opgChannelItem.findall('Programs/Programs/ProgramEntity'):
                        start = convertDate(program.find('StartTime').text)
                        stop = convertDate(program.find('EndTime').text)
                        title = program.find('Title').text

                        id = channel.id + "_" + start.strftime("%Y%m%d%H%M%S") + "_" + title
                        id = md5(id.encode("utf-8"))

                        description = ""
                        if program.find('IsHD').text == "true": 
	                        description = "[HD] "

                        if program.find('Synopsis') is not None:
	                        description = description + program.find('Synopsis').text

                        program = Program(id=id,
                                          channel=channel,
                                          title=title, 
                                          description=description, 
                                          start=start, 
                                          stop=stop)
                        self.programs.append(program)

        return (self.channels, self.programs)

    def getTvFormat(self):
        xmlTv = ET.Element("tv")

        xmlTv.append(ET.Comment("Source: http://www.freeviewnz.tv/localservices/opg/schedule/"))
        xmlTv.append(ET.Comment("Copyright 2012 Freeview Ltd."))
        xmlTv.append(ET.Comment("I am in no way claiming this data as my own."))
        xmlTv.append(ET.Comment("The data is simply being reformatted to allow"))
        xmlTv.append(ET.Comment("media pc software such as Mediaportal to parse it."))

        channels, programs = self.parse()

        for channel in channels:
            xmlChannel = ET.SubElement(xmlTv, "channel", { 'id': channel.id })
            xmlDisplayName = ET.SubElement(xmlChannel, "display-name")
            xmlDisplayName.text = channel.name

        for program in programs:
            xmlProgram = ET.SubElement(xmlTv, "programme", 
                        { 'channel': program.channel.id, 
                          'start': program.start.strftime("%Y%m%d%H%M%S %z"), 
                          'stop': program.stop.strftime("%Y%m%d%H%M%S %z")
                        })
            xmlTitle = ET.SubElement(xmlProgram, "title")
            xmlTitle.text = program.title
            xmlDescription = ET.SubElement(xmlProgram, "desc")
            xmlDescription.text = program.description
            xmlId = ET.SubElement(xmlProgram, "episode-num", {'system': 'dd_progid'})
            xmlId.text = program.id

        return ET.tostring(xmlTv, pretty_print=True)

def md5(string):
    hash = hashlib.md5()
    hash.update(string)
    return hash.hexdigest()

def convertDate(string):
    reg = re.compile(r"(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)([\+\-])(\d\d)(\d\d)*")
    match = reg.match(string)

    class Timezone(datetime.tzinfo):
        def utcoffset(self, dt):
            if match.group(9) is not None:   
                return datetime.timedelta(hours=match.group(7)+match.group(8),minutes=match.group(7)+match.group(9))
            else:
                return datetime.timedelta(0)
        def dst(self, dt):
            return datetime.timedelta(0)

    tz = Timezone()

    date = datetime.datetime(int(match.group(1)),
                      int(match.group(2)),
                      int(match.group(3)),
                      int(match.group(4)),
                      int(match.group(5)),
                      int(match.group(6)),
                      tzinfo=tz)
    return date

xml = Xml("")
print xml.getTvFormat()
