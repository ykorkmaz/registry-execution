__author__ = 'yakup'

import fnmatch
import os
import sys

outshimfile = 'execution_shim.csv'
outmuifile = 'execution_mui.csv'
outassistfile = 'execution_userassist.csv'
outlegacyfile = 'execution_legacy.csv'
outuserassistfile = 'execution_userassist.csv'
auditspath = 'C:\Users\yakup\PycharmProjects\RegRipper\TestAudits'
#auditspath = 'C:\Users\yakup\PycharmProjects\RegRipper\TestAudits2'
#auditspath = 'C:\CollectorRoot\Audits

# writes RegRipper's appcompatcache and ShimCacheParser's command output to a file
def writeshimfile(modtime, luptime, path, filesize, execflag, outfilepath):
    # write column titles if file will be newly created
    if not os.path.exists(outfilepath):
        fw = open(outfilepath,'w')
        fw.write("\"Last Modified\",\"Last Update\",\"Path\",\"File Size\",\"Exec Flag\"\n")
        fw.close()

    with open(outfilepath, 'a') as fw:
        fw.write("\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"\n" % (modtime, luptime, path, filesize, execflag))

# writes RegRipper's mui cache command outputs to file
def writemuifile(filename, path, company, username, outfilepath):
    # write column titles if file will be newly created
    if not os.path.exists(outfilepath):
        fw = open(outfilepath,'w')
        fw.write("\"File Name\",\"Path\",\"Company\",\"User\"\n")
        fw.close()

    with open(outfilepath, 'a') as fw:
        fw.write("\"%s\",\"%s\",\"%s\",\"%s\"\n" % (filename, path, company, username))

def writelegacyfile(modtime, legname, leglongname, legpath, legparam, outfilepath):
    # write column titles if file will be newly created
    if not os.path.exists(outfilepath):
        fw = open(outfilepath,'w')
        fw.write("\"Last Modified\",\"Key Name\",\"Long Name\",\"File Path\",\"Parameter\"\n")
        fw.close()

    with open(outfilepath, 'a') as fw:
        fw.write("\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"\n" % (modtime, legname, leglongname, legpath, legparam))

def writeuserassistfile(modtime, userkey, fpath, numruns, username, outfilepath):
    # write column titles if file will be newly created
    if not os.path.exists(outfilepath):
        fw = open(outfilepath,'w')
        fw.write("\"Last Modified\",\"UserAssist Key\",\"File Path\",\"Number of Runs\",\"User\"\n")
        fw.close()

    with open(outfilepath, 'a') as fw:
        fw.write("\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"\n" % (modtime, userkey, fpath, numruns, username))

def runuserassistcommand(filepath, filedir, username):

    # run userassist plugin to get the userassist execution list
    cmdout = os.popen('perl rip.pl -r %s -p userassist' %(filepath), 'r')

    lastwritten = ''
    userassistkey = ''

    line = cmdout.readline()
    while line:
        # get rid off heading and trailing white space chars
        line = line.strip().rstrip()

        isnotempty = True
        if line == '' or line.isspace():
            isnotempty = False

        # omit empty lines, get the first line specifying a path
        if isnotempty:

            # get the key name under userassist registry key
            if len(line.split(' ')) == 1 and line[0] == '{':
                userassistkey = line
            elif (len(line.split(' ')) == 6 or len(line.split(' ')) == 7) and line[-1] == 'Z':
                # get the modification time of the key
                lastwritten = line[:-2]
            elif len(line.split('(')) == 2:
                if line.split('(')[1][0] != 'U':

                    runpath = line.split('(')[0][:-1]
                    numberofruns = line.split('(')[1][:-1]

                    writeuserassistfile(lastwritten, userassistkey, runpath, numberofruns, username, os.path.join(filedir, outuserassistfile))

        line = cmdout.readline()

def runlegacycommand(filepath, filedir):

    # remove the old legacy output file
    if os.path.exists(os.path.join(filedir, outlegacyfile)):
        os.remove(os.path.join(filedir, outlegacyfile))

    # run ShimCacheParser to get the shim cache execution list
    cmdout = os.popen('perl rip.pl -r %s -p legacy' %(filepath), 'r')

    lastwritten = ''
    prevline = ''
    line = cmdout.readline()
    while line:
        # get rid off heading and trailing white space chars
        line = line.strip().rstrip()

        isnotspace = True
        isrelevant = True
        # check if the line is neither empty nor space and relevant for parsing
        if line == '' or line.isspace():
            isnotspace = False
        elif line[:4] == '(Sys' or line[:8] == 'legacy v':
            isrelevant = False

        # omit empty lines, get the first line specifying a path
        if isnotspace and isrelevant:
            legacyname = 'N\A'
            execpath = 'N\A'
            longname = 'N\A'
            legacyparam = 'N\A'

            # get time information
            if line[-5:] == '(UTC)':
                lastwritten = line[:-6]
            else:
                # if legacy entry contains additional information
                if len(line.split(' - ')) == 2:
                    legacyname = line.split(' - ')[0].split('\\')[0]

                    # get the path, if it exists, or long name of the file
                    if line.split(' - ')[1].strip()[0] == '@':
                        execpath = line.split(' - ')[1].strip().split(',')[0][1:]
                        legacyparam = line.split(' - ')[1].strip().split(',')[1]
                    else:
                        longname = line.split(' - ')[1].strip().rstrip()

                    # if there are two lines for one run but second one with a longname, ignore the previous one
                    if legacyname == prevline:
                        prevline = ''
                    elif prevline != '':
                        # if the subsequent lines are different entries, write the previous one
                        writelegacyfile(lastwritten, prevline, 'N\A', execpath, legacyparam, os.path.join(filedir, outlegacyfile))

                    writelegacyfile(lastwritten, legacyname, longname, execpath, legacyparam, os.path.join(filedir, outlegacyfile))

                else:
                    if prevline != '' and prevline != line:
                        writelegacyfile(lastwritten, prevline, longname, execpath, legacyparam, os.path.join(filedir, outlegacyfile))

                    # comment the below line for not getting the legacy entries without additional info
                    prevline = line

        line = cmdout.readline()

    # if previous line is not empty
    if prevline != '':
        writelegacyfile(lastwritten, prevline, longname, execpath, legacyparam, os.path.join(filedir, outlegacyfile))

# gets Application Compatibility Cache from system hive file using Mandiant's ShimCacheParser
def runshimcommand(filepath, filedir):
    # remove the old shim output file
    if os.path.exists(os.path.join(filedir, outshimfile)):
        os.remove(os.path.join(filedir, outshimfile))

    # run ShimCacheParser to get the shim cache execution list
    cmdout = os.popen('ShimCacheParser.py -i %s' %(filepath))

    line = cmdout.readline()
    while line:
        # omit empty lines, get the first line specifying a path
        if not line.isspace() and line[2] == '/':
            if len(line.rstrip().split('N/A')) == 2:
                delimline = line.rstrip().split(' ')
                mtime = ' '.join(delimline[:2])
                ltime = ' '.join(delimline[2:4])
                fpath = ' '.join(delimline[4:-2])
                fsize = delimline[-2]
                execf = delimline[-1]
                writeshimfile(mtime, ltime, fpath, fsize, execf, os.path.join(filedir, outshimfile))
            else:
                delimline = line.rstrip().split('N/A')
                mtime = delimline[0].strip()
                fpath = delimline[1].strip()
                execf = delimline[2].strip()
                writeshimfile(mtime, 'N/A', fpath, 'N/A', execf, os.path.join(filedir, outshimfile))
        line = cmdout.readline()


'''
# gets Application Compatibility Cache from system hive file using RegRipper (returns no result in Win 8)
def runcommand(filepath, filedir):
    # run RegRipper to get the shim cache execution list
    cmdout = os.popen('perl rip.pl -r %s -p appcompatcache' %(filepath), 'r')

    # get first line of the command output
    line = cmdout.readline()

    # parse the line and write it to csv file in format compatible to Mandiant's parser
    while line:
        # omit empty lines, get the first line specifying a path
        if not line.isspace() and line[1] == ':':
            path = line.rstrip()
            # after a path, comes modification time, omit the first letters
            modtime = cmdout.readline().rstrip()[9:][:-2]

            line = cmdout.readline()
            # if successor line is empty, execution flag is false
            if line.isspace():
                execflag = 'FALSE'
            else:
                execflag = 'TRUE'

            # write parsed fields to the output file
            writefile(modtime, path, execflag, os.path.join(filedir, outshimfile))

        line = cmdout.readline()
'''

# gets Mui Cache from user and user class hive files using RegRipper
def runmuicommand(filepath, filedir, username):

    # run RegRipper to get the mui cache execution list
    cmdout = os.popen('rip.exe -r %s -p muicache' %(filepath), 'r')

    # get first line of the command output
    line = cmdout.readline()

    isAppNameFound = False
    # parse the line and write it to csv file in format compatible to Mandiant's parser
    while line:
        line = line.strip().rstrip()
        # omit empty lines, get the first line specifying a path
        if not line.isspace() and len(line) > 1:
            if line[1] == ':':
                # in Windows 8, most of the time there are two lines for an application, in first line
                # path ends with "FriendlyAppName" and in the second line it ends with "CompanyName"
                if isAppNameFound:
                    isAppNameFound = False
                    if '('.join(line.split('(')[:-1]).rstrip().split('.')[-1] == 'ApplicationCompany':
                        # get the company info
                        appcompany = ''.join(line.split('(')[-1:])[:-1]
                        # write parsed fields to the output file
                        writemuifile(filename, path, appcompany, username, os.path.join(filedir, outmuifile))
                    else:
                        # write the previous line because it has no second line for application company
                        writemuifile(filename, path, appcompany, username, os.path.join(filedir, outmuifile))
                        continue
                else:
                    path = '('.join(line.split('(')[:-1]).rstrip()
                    filename = ''.join(line.split('(')[-1:])[:-1].rstrip()
                    appcompany = 'N/A'

                    # check if it is Windows 8 output
                    if '('.join(line.rstrip().split('(')[:-1]).rstrip().split('.')[-1] == 'FriendlyAppName':
                        isAppNameFound = True
                    else:
                        # write parsed fields to the output file
                        writemuifile(filename, path, appcompany, username, os.path.join(filedir, outmuifile))

        line = cmdout.readline()

# check the number of arguments entered
if len (sys.argv) == 1:
    print 'Executed with default path: %s' %(auditspath)
elif len (sys.argv) == 2:
    # check if the path entered exists
    if os.path.exists(sys.argv[1]):
        auditspath = sys.argv[1]
    else:
        print 'Path specified does not exist !'
        sys.exit(1)
else:
    print "Usage: python Regripper_Execution-v4.py [<audit-file-path>]"
    sys.exit(1)

# search the audits directory for system hive files
for root, dirnames, filenames in os.walk(auditspath):
    # if the system hive is already fetched
    for filename in fnmatch.filter(filenames, 'HKEY_LOCAL_MACHINE_SYSTEM'):
        # get full path of the system hive
        filepath = os.path.join(root, filename)

        runshimcommand(filepath, root)

        runlegacycommand(filepath, root)

        '''
        # for using RegRipper's appcompatcache plugin
        # if the execution list has not already been processed
        if os.path.exists(os.path.join(root, outshimfile)):
            os.remove(os.path.join(root, outshimfile))
            runcommand(filepath, root)
        else:
            runcommand(filepath, root)
        '''

    # is it the first User Class hive file in the directory
    isFirstMatchMUI = True
    isFirstMatchUserAssist = True

    # hive files for extracting mui cache
    userhives = ['*UsrClass.dat','*ntuser.dat']

    # extract mui cache from all user hive files
    for userhivefilter in userhives:
        for filename in fnmatch.filter(filenames, userhivefilter):
            # get full path of the netuser hive
            filepath = os.path.join(root, filename)

            # check if th hive files extracted from a Windows XP machine
            if ''.join(filename.split('_')[3:7]) == 'DocumentsandSettings':
                # get the user name from the hive file name
                if userhivefilter == userhives[0]:
                    username = ''.join(filename.split('_')[7:8])
                else:
                    username = ''.join(filename.split('_')[-2:-1])
            else:
                if userhivefilter == userhives[0]:
                    username = ''.join(filename.split('_')[5:6])
                else:
                    username = ''.join(filename.split('_')[-2:-1])

            # if the mui output file already exists
            if os.path.exists(os.path.join(root, outmuifile)):
                # if it is the first run, remove the old mui output file
                if isFirstMatchMUI:
                    os.remove(os.path.join(root, outmuifile))
                    isFirstMatchMUI = False
                runmuicommand(filepath, root, username)
            else:
                runmuicommand(filepath, root, username)
                if isFirstMatchMUI:
                    isFirstMatchMUI = False

            if userhivefilter == userhives[1]:
                if os.path.exists(os.path.join(root, outuserassistfile)):
                    if isFirstMatchUserAssist:
                        os.remove(os.path.join(root, outuserassistfile))
                        isFirstMatchUserAssist = False
                    runuserassistcommand(filepath, root, username)
                else:
                    runuserassistcommand(filepath, root, username)
                    if isFirstMatchUserAssist:
                        isFirstMatchUserAssist = False